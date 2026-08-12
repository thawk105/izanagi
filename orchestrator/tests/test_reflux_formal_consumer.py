"""Conjunct-level tests for the fail-closed reflux formal consumer."""
from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import inspect
import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from orchestrator.campaign import reflux_formal_consumer as C
from orchestrator.campaign import reflux_origin_binding as B
from orchestrator.campaign import reflux_origin_ledger as L
from orchestrator.campaign import reflux_origin_topology as T
from orchestrator.campaign import reflux_source_closure as S
from orchestrator.tests import reflux_origin_fixture_builder as F


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _issued_capability(**overrides) -> B.OriginBindingCapability:
    raw = F.build_launch_admission_inputs()
    workload = dict(raw["authority_workload"])
    workload.update(overrides.pop("authority_workload", {}))
    values = {
        "authority_blob_sha256": raw["authority_blob_sha256"],
        "source_closure_sha256": raw["source_closure_sha256"],
        "origin_id": raw["origin_id"],
        "cell_key": raw["cell_key"],
        "authority_workload": B.AuthorityWorkload(**workload),
        "axis_semantics_sha256": raw["axis_semantics_sha256"],
        "verifier_policy_sha256": raw["verifier_policy_sha256"],
        "environment_contract_sha256": raw["environment_contract_sha256"],
        "campaign_id": raw["campaign_id"],
        "trial_workload": raw["trial_workload"],
        "measurement_head": raw["measurement_head"],
        "store_scope": raw["store_scope"],
    }
    values.update(overrides)
    seal = object()
    capability = B.OriginBindingCapability(**values, _seal=seal)
    B._ISSUED_CAPABILITY_FIELDS[seal] = B._capability_fields(capability)
    return capability


def _issued_closure() -> S.ValidatedSourceClosure:
    record = F.build_source_closure_record()
    raw = _canonical(record)
    referents = {
        name: value["preimage_ref"]["sha256"]
        for name, value in record["referents"].items()
    }
    return S.ValidatedSourceClosure(
        source_closure_sha256=_digest(raw),
        captured_commit_oid=record["captured_commit_oid"],
        authority_series_id=record["authority_series_id"],
        origin_id=record["origin_id"],
        cell_key=record["cell_key"],
        referent_sha256s=referents,
        record_bytes=raw,
        _issuer=S._ISSUER_SEAL,
    )


def _run_plan() -> T.RecoveryEnvelope:
    raw = F.build_recovery_envelope_inputs()
    operations = T.EventOperationIds(**raw["event_operation_ids"])
    materials = tuple(
        T.MemberRecoveryMaterial(
            candidate_salt=item["candidate_salt"],
            result_evidence_salt=item["result_evidence_salt"],
            constraint_salt=item["constraint_salt"],
            evidence_path=item["evidence_path"],
            planned_campaign_run_identity=f"fixture-run-{index:04d}",
        )
        for index, item in enumerate(raw["members"])
    )
    return T.build_recovery_envelope(
        capability_digest=raw["origin_binding_capability_sha256"],
        source_closure_digest=raw["source_closure_sha256"],
        hypothesis_sha256=raw["hypothesis_sha256"],
        validation_plan_sha256=raw["validation_plan_sha256"],
        attempt_0_batch_id=raw["reserve_attempts"][0]["batch_id"],
        retry_1_batch_id=raw["reserve_attempts"][1]["batch_id"],
        event_operation_ids=operations,
        source_mask=7,
        member_materials=materials,
        initial_expected_state_commitment=raw["expected_state_commitment"],
    )


def _sealed_member(record: dict, raw: bytes) -> L.SealedBatchMember:
    return L.SealedBatchMember(
        query_ordinal=record["ledger_member"]["query_ordinal"],
        replicate_ordinal=record["ledger_member"]["replicate_ordinal"],
        candidate_bytes=record["trigger_binding"]["candidate_wire"].encode("ascii"),
        outcome=record["physical_result"]["outcome"],
        evidence_digest=L.EvidenceDigest(_digest(raw)),
        constraint_sha256=record["physical_result"]["constraint_sha256"],
    )


@dataclass
class _Case:
    fixture: F.FixtureRepository
    capability: B.OriginBindingCapability
    closure: S.ValidatedSourceClosure
    run_plan: T.RecoveryEnvelope
    records: list[dict]
    raw_records: list[bytes]
    batches: tuple[L.SealedBatch, ...]
    snapshot: L.OriginSnapshot
    operation_id: str = "fixture-formal-terminal-operation"

    def kwargs(self) -> dict:
        first = self.records[0]
        return {
            "capability": self.capability,
            "source_closure": self.closure,
            "run_plan": self.run_plan,
            "authority_blob_bytes": self.fixture.authority_manifest_path.read_bytes(),
            "launch_admission_record_sha256": first["trial_binding"][
                "launch_admission_record_sha256"
            ],
            "origin_snapshot": self.snapshot,
            "sealed_batches": self.batches,
            "result_record_bytes": tuple(self.raw_records),
            "evidence_root": self.fixture.evidence_root,
            "verifier_policy_bytes": (
                self.fixture.root / "artifacts" / "verifier-policy.json"
            ).read_bytes(),
            "enforcement_arm": "fixture-enforced",
            "generator_closure": {
                "schema_version": "fixture-generator-closure/v1",
                "generator_sha256": "a" * 64,
            },
            "operation_id": self.operation_id,
        }


@pytest.fixture(autouse=True)
def _clear_process_local_receipt_state():
    C._ISSUED_RECEIPTS.clear()
    C._OPERATION_REPLAY_CACHE.clear()
    yield
    C._ISSUED_RECEIPTS.clear()
    C._OPERATION_REPLAY_CACHE.clear()


@pytest.fixture
def case(tmp_path: Path) -> _Case:
    fixture = F.build_fixture_repository(tmp_path / "formal-consumer")
    raw_records = [path.read_bytes() for path in fixture.result_evidence_paths]
    records = [json.loads(raw) for raw in raw_records]
    members = tuple(
        _sealed_member(record, raw)
        for record, raw in zip(records, raw_records, strict=True)
    )
    origin_id = records[0]["origin_binding"]["origin_id"]
    batch = L.SealedBatch(
        origin_id=origin_id,
        batch_id=records[0]["ledger_member"]["batch_id"],
        member_row_count=33,
        distinct_candidate_count=32,
        sealed_distinct_candidate_count=32,
        members=members,
    )
    snapshot = L.OriginSnapshot(
        origin_id=origin_id,
        state_commitment=_digest(b"fixture:formal-input-state"),
        phase="IDLE",
        iterations_used=1,
        queries_used=33,
        sealed_queries=33,
        tombstoned_queries=0,
        forfeited_iterations=0,
        forfeited_queries=0,
        batch_count=1,
        tombstone_count=0,
        terminal_status=None,
        constraint_class_sha256s=(),
        origin_distinct_candidate_count=32,
        reserved_batch_id=None,
        reserved_iteration_index=None,
        reserved_member_row_count=None,
        reserved_query_ordinal_start=None,
    )
    return _Case(
        fixture=fixture,
        capability=_issued_capability(),
        closure=_issued_closure(),
        run_plan=_run_plan(),
        records=records,
        raw_records=raw_records,
        batches=(batch,),
        snapshot=snapshot,
    )


def _set_member(case: _Case, index: int, **changes) -> None:
    batch = case.batches[0]
    members = list(batch.members)
    members[index] = dataclasses.replace(members[index], **changes)
    case.batches = (dataclasses.replace(batch, members=tuple(members)),) + case.batches[1:]


def _set_record(case: _Case, index: int, record: dict) -> None:
    raw = _canonical(record)
    case.records[index] = record
    case.raw_records[index] = raw
    _set_member(case, index, evidence_digest=L.EvidenceDigest(_digest(raw)))


def _mutate_record(case: _Case, index: int, path: tuple[str, ...], value) -> None:
    record = copy.deepcopy(case.records[index])
    target = record
    for component in path[:-1]:
        target = target[component]
    target[path[-1]] = value
    _set_record(case, index, record)


def _rewrite_wal(case: _Case, index: int, records: list[dict], *, attempt: str | None = None) -> None:
    record = copy.deepcopy(case.records[index])
    projection_path = case.fixture.evidence_root / record["evidence"]["ordered_wal_ref"]["path"]
    projection = json.loads(projection_path.read_bytes())
    selected_attempt = attempt or record["physical_result"]["build_attempt_id"]
    for wal_record in records:
        wal_record["build_attempt_id"] = selected_attempt
    source_raw = _canonical(records)
    source_path = case.fixture.evidence_root / projection["source_wal_ref"]["path"]
    source_path.write_bytes(source_raw)
    projection["source_wal_ref"]["sha256"] = _digest(source_raw)
    projection["byte_start"] = 0
    projection["byte_end"] = len(source_raw)
    projection["build_attempt_id"] = selected_attempt
    projection["records"] = records
    projection_raw = _canonical(projection)
    projection_path.write_bytes(projection_raw)
    record["physical_result"]["build_attempt_id"] = selected_attempt
    record["evidence"]["ordered_wal_ref"]["sha256"] = _digest(projection_raw)
    _set_record(case, index, record)


def _evaluate(case: _Case, **overrides) -> C.FormalConsumerResult:
    kwargs = case.kwargs()
    kwargs.update(overrides)
    return C.evaluate_formal_origin(**kwargs)


def _assert_reason(case: _Case, expected: C.FormalReasonCode, **overrides) -> None:
    result = _evaluate(case, **overrides)
    assert type(result) is C.FormalContractRejected
    assert result.reason_code is expected
    assert result.projection.reason_code is expected
    assert result.projection.formal_receipt_sha256 is None
    assert result.projection.evidence_root_sha256 is None
    payload = json.loads(C.canonical_aborted_origin_payload_bytes(result.decision))
    assert payload["seal_kind"] == "aborted"
    assert payload["constraint_class_sha256s"] == []


def test_exact_fixture_contract_reaches_only_p6_unavailable(case: _Case) -> None:
    result = _evaluate(case)
    assert type(result) is C.P6Unavailable
    assert result.reason_code is C.FormalReasonCode.P6_UNAVAILABLE
    payload = json.loads(C.canonical_aborted_origin_payload_bytes(result.decision))
    assert payload["seal_kind"] == "aborted"
    assert payload["constraint_class_sha256s"] == []


def test_fc01_rejects_missing_non_tombstone_record(case: _Case) -> None:
    case.raw_records.pop()
    case.records.pop()
    _assert_reason(case, C.FormalReasonCode.FC01)


def test_fc01_rejects_duplicate_non_tombstone_record(case: _Case) -> None:
    case.raw_records.append(case.raw_records[0])
    case.records.append(copy.deepcopy(case.records[0]))
    _assert_reason(case, C.FormalReasonCode.FC01)


def test_fc01_rejects_record_for_unknown_member(case: _Case) -> None:
    extra = copy.deepcopy(case.records[0])
    extra["ledger_member"]["query_ordinal"] = 999
    case.records.append(extra)
    case.raw_records.append(_canonical(extra))
    _assert_reason(case, C.FormalReasonCode.FC01)


def test_fc01_rejects_record_raw_digest_mismatch(case: _Case) -> None:
    _set_member(case, 0, evidence_digest=L.EvidenceDigest("f" * 64))
    _assert_reason(case, C.FormalReasonCode.FC01)


def test_fc02_rejects_record_for_tombstone_member(case: _Case) -> None:
    _set_member(
        case,
        0,
        outcome="tombstoned",
        evidence_digest=None,
        constraint_sha256=None,
    )
    _assert_reason(case, C.FormalReasonCode.FC02)


@pytest.mark.parametrize(
    ("conjunct", "path"),
    [
        ("origin", ("origin_binding", "origin_id")),
        ("cell", ("origin_binding", "cell_key")),
        ("authority", ("origin_binding", "authority_blob_sha256")),
        ("campaign", ("trial_binding", "campaign_id")),
        ("workload", ("trial_binding", "workload")),
        ("axis", ("origin_binding", "axis_semantics_sha256")),
        ("verifier", ("origin_binding", "verifier_policy_sha256")),
        ("environment", ("origin_binding", "environment_contract_sha256")),
    ],
)
def test_fc03_rejects_each_record_binding_conjunct(
    case: _Case, conjunct: str, path: tuple[str, ...]
) -> None:
    value = "e" * 64 if path[-1].endswith("sha256") else f"wrong-{conjunct}"
    _mutate_record(case, 0, path, value)
    _assert_reason(case, C.FormalReasonCode.FC03)


def test_fc03_rejects_descriptor_conjunct(case: _Case) -> None:
    case.capability = _issued_capability(
        authority_workload={"descriptor_sha256": "e" * 64}
    )
    _assert_reason(case, C.FormalReasonCode.FC03)


def test_fc03_rejects_launch_admission_conjunct(case: _Case) -> None:
    _assert_reason(
        case,
        C.FormalReasonCode.FC03,
        launch_admission_record_sha256="e" * 64,
    )


@pytest.mark.parametrize(
    ("name", "path", "value"),
    [
        ("query", ("ledger_member", "query_ordinal"), 1),
        ("replicate", ("ledger_member", "replicate_ordinal"), 9),
        ("wire", ("trigger_binding", "candidate_wire"), "00000"),
    ],
)
def test_fc04_rejects_individually_reachable_mapping_fields(
    case: _Case, name: str, path: tuple[str, ...], value
) -> None:
    _mutate_record(case, 0, path, value)
    _assert_reason(case, C.FormalReasonCode.FC04)


def test_fc04_outcome_single_flip_is_preempted_by_record_schema(case: _Case) -> None:
    _mutate_record(case, 0, ("physical_result", "outcome"), "accepted")
    _assert_reason(case, C.FormalReasonCode.FC01)


def test_fc04_constraint_single_flip_is_preempted_by_exact_class_set(case: _Case) -> None:
    _mutate_record(
        case,
        0,
        ("physical_result", "constraint_sha256"),
        "e" * 64,
    )
    _assert_reason(case, C.FormalReasonCode.FC09)


def test_fc05a_rejects_duplicate_build_attempt_id(case: _Case) -> None:
    duplicate = case.records[0]["physical_result"]["build_attempt_id"]
    wal = copy.deepcopy(json.loads(
        (case.fixture.evidence_root / case.records[1]["evidence"]["ordered_wal_ref"]["path"])
        .read_bytes()
    )["records"])
    _rewrite_wal(case, 1, wal, attempt=duplicate)
    _assert_reason(case, C.FormalReasonCode.FC05A)


def test_fc05b_rejects_overlapping_resolved_wal_range(case: _Case) -> None:
    record = copy.deepcopy(case.records[1])
    record["evidence"]["ordered_wal_ref"] = copy.deepcopy(
        case.records[0]["evidence"]["ordered_wal_ref"]
    )
    record["physical_result"]["build_attempt_id"] = case.records[0][
        "physical_result"
    ]["build_attempt_id"]
    _set_record(case, 1, record)
    _assert_reason(case, C.FormalReasonCode.FC05B)


def test_fc05c_rejects_wal_trigger_binding_mismatch(case: _Case) -> None:
    projection_path = case.fixture.evidence_root / case.records[0]["evidence"][
        "ordered_wal_ref"
    ]["path"]
    wal = copy.deepcopy(json.loads(projection_path.read_bytes())["records"])
    wal[0]["trigger_binding"]["mask"] = 31
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC05C)


def test_fc06_rejects_missing_source_base_with_33_rows_preserved(case: _Case) -> None:
    _mutate_record(case, 0, ("p6_plan", "purpose"), "p6-validation")
    _assert_reason(case, C.FormalReasonCode.FC06)


def test_fc06_rejects_validation_mask_set_mismatch(case: _Case) -> None:
    record = copy.deepcopy(case.records[1])
    record["trigger_binding"] = copy.deepcopy(case.records[2]["trigger_binding"])
    _set_record(case, 1, record)
    _set_member(
        case,
        1,
        candidate_bytes=record["trigger_binding"]["candidate_wire"].encode("ascii"),
    )
    projection_path = case.fixture.evidence_root / record["evidence"]["ordered_wal_ref"]["path"]
    wal = copy.deepcopy(json.loads(projection_path.read_bytes())["records"])
    wal[0]["trigger_binding"] = copy.deepcopy(record["trigger_binding"])
    _rewrite_wal(case, 1, wal)
    _assert_reason(case, C.FormalReasonCode.FC06)


def test_fc06_rejects_validation_order_mismatch(case: _Case) -> None:
    batch = case.batches[0]
    members = list(batch.members)
    members[1], members[2] = members[2], members[1]
    case.batches = (dataclasses.replace(batch, members=tuple(members)),)
    _assert_reason(case, C.FormalReasonCode.FC06)


def test_fc07_rejects_accepted_without_terminal_commit(case: _Case) -> None:
    record = copy.deepcopy(case.records[0])
    record["physical_result"] = {
        "build_attempt_id": record["physical_result"]["build_attempt_id"],
        "outcome": "accepted",
        "constraint_sha256": None,
    }
    _set_record(case, 0, record)
    _set_member(case, 0, outcome="accepted", constraint_sha256=None)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_accepted_verify_config_order_mismatch(case: _Case) -> None:
    record = copy.deepcopy(case.records[0])
    record["physical_result"]["outcome"] = "accepted"
    record["physical_result"]["constraint_sha256"] = None
    _set_record(case, 0, record)
    _set_member(case, 0, outcome="accepted", constraint_sha256=None)
    wal = [
        {
            "kind": "TriggerGateBinding",
            "build_attempt_id": "placeholder",
            "trigger_binding": copy.deepcopy(record["trigger_binding"]),
        },
        {
            "kind": "commit",
            "build_attempt_id": "placeholder",
            "verify_configs": ["s2", "legacy"],
        },
    ]
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_rejected_without_single_candidate_witness(case: _Case) -> None:
    projection_path = case.fixture.evidence_root / case.records[0]["evidence"][
        "ordered_wal_ref"
    ]["path"]
    wal = copy.deepcopy(json.loads(projection_path.read_bytes())["records"])
    wal[-1]["witness_class_sha256s"] = []
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc09_rejects_nonexact_rejected_class_set(case: _Case) -> None:
    _mutate_record(
        case,
        0,
        ("physical_result", "constraint_sha256"),
        "e" * 64,
    )
    _assert_reason(case, C.FormalReasonCode.FC09)


def test_fc09_rejects_kmax_excess(case: _Case) -> None:
    second_class = "e" * 64
    record = copy.deepcopy(case.records[1])
    record["physical_result"]["constraint_sha256"] = second_class
    _set_record(case, 1, record)
    _set_member(case, 1, constraint_sha256=second_class)
    projection_path = case.fixture.evidence_root / record["evidence"]["ordered_wal_ref"]["path"]
    wal = copy.deepcopy(json.loads(projection_path.read_bytes())["records"])
    wal[-1]["witness_class_sha256s"] = [second_class]
    _rewrite_wal(case, 1, wal)
    _assert_reason(case, C.FormalReasonCode.FC09)


def test_fc09_rejects_query_floor_mismatch(case: _Case) -> None:
    case.snapshot = dataclasses.replace(case.snapshot, sealed_queries=32)
    _assert_reason(case, C.FormalReasonCode.FC09)


def test_fc10_rejects_origin_containing_all_tombstone_batch(case: _Case) -> None:
    tombstones = tuple(
        L.SealedBatchMember(index + 33, 0, b"00000", "tombstoned", None, None)
        for index in range(2)
    )
    extra = L.SealedBatch(
        origin_id=case.snapshot.origin_id,
        batch_id="fixture-all-tombstone-batch",
        member_row_count=2,
        distinct_candidate_count=1,
        sealed_distinct_candidate_count=0,
        members=tombstones,
    )
    case.batches = case.batches + (extra,)
    case.snapshot = dataclasses.replace(
        case.snapshot,
        batch_count=2,
        tombstone_count=2,
        tombstoned_queries=2,
    )
    _assert_reason(case, C.FormalReasonCode.FC10)


def test_receipt_has_exact_keys_independent_canonical_bytes_and_no_self_digest(
    case: _Case,
) -> None:
    result = _evaluate(case)
    assert type(result) is C.P6Unavailable
    record = C.formal_consumer_receipt_record(result.receipt)
    assert set(record) == {
        "schema_version",
        "operation_id",
        "authority_blob_sha256",
        "source_closure_sha256",
        "run_plan_sha256",
        "origin_id",
        "input_state_commitment",
        "origin_sealed_payload_sha256",
        "evidence_sha256s",
        "evidence_root_sha256",
        "enforcement_arm",
        "generator_closure",
        "reason_code",
        "issuer_seal",
    }
    assert all("receipt_sha256" not in key for key in record)
    assert C.canonical_formal_consumer_receipt_bytes(result.receipt) == _canonical(record)
    assert not C.canonical_formal_consumer_receipt_bytes(result.receipt).endswith(b"\n")


def test_receipt_rejects_wrong_input_state_commitment(case: _Case) -> None:
    result = _evaluate(case)
    assert type(result) is C.P6Unavailable
    with pytest.raises(C.FormalReceiptError) as caught:
        C.consume_formal_consumer_receipt(
            result.receipt,
            operation_id=case.operation_id,
            input_state_commitment="e" * 64,
            decision=result.decision,
        )
    assert caught.value.reason_code is C.FormalReceiptReason.STATE


def test_receipt_rejects_wrong_terminal_payload_digest(case: _Case) -> None:
    result = _evaluate(case)
    assert type(result) is C.P6Unavailable
    changed = dataclasses.replace(result.decision, sealed_queries=32)
    with pytest.raises(C.FormalReceiptError) as caught:
        C.consume_formal_consumer_receipt(
            result.receipt,
            operation_id=case.operation_id,
            input_state_commitment=case.snapshot.state_commitment,
            decision=changed,
        )
    assert caught.value.reason_code is C.FormalReceiptReason.PAYLOAD


def test_receipt_exact_operation_replay_returns_cached_decision(case: _Case) -> None:
    result = _evaluate(case)
    assert type(result) is C.P6Unavailable
    first = C.consume_formal_consumer_receipt(
        result.receipt,
        operation_id=case.operation_id,
        input_state_commitment=case.snapshot.state_commitment,
        decision=result.decision,
    )
    second = C.consume_formal_consumer_receipt(
        result.receipt,
        operation_id=case.operation_id,
        input_state_commitment=case.snapshot.state_commitment,
        decision=result.decision,
    )
    assert second is first


def test_receipt_same_operation_different_payload_is_rejected(case: _Case) -> None:
    result = _evaluate(case)
    assert type(result) is C.P6Unavailable
    C.consume_formal_consumer_receipt(
        result.receipt,
        operation_id=case.operation_id,
        input_state_commitment=case.snapshot.state_commitment,
        decision=result.decision,
    )
    changed = dataclasses.replace(result.decision, sealed_queries=32)
    with pytest.raises(C.FormalReceiptError) as caught:
        C.consume_formal_consumer_receipt(
            result.receipt,
            operation_id=case.operation_id,
            input_state_commitment=case.snapshot.state_commitment,
            decision=changed,
        )
    assert caught.value.reason_code is C.FormalReceiptReason.REPLAY


def test_terminal_projection_is_one_nested_key_with_closed_reason(case: _Case) -> None:
    result = _evaluate(case)
    assert type(result) is C.P6Unavailable
    wire = C.origin_terminal_projection_record(result.projection)
    assert set(wire) == {"origin_terminal_projection"}
    nested = wire["origin_terminal_projection"]
    assert set(nested) == {
        "schema_version",
        "reason_code",
        "formal_receipt_sha256",
        "evidence_root_sha256",
        "authority_blob_sha256",
        "origin_id",
        "cell_key",
        "terminal_payload_sha256",
    }
    assert nested["reason_code"] == "P6Unavailable"
    assert nested["formal_receipt_sha256"] is not None
    assert nested["evidence_root_sha256"] is not None
    assert type(result.projection.reason_code) is C.FormalReasonCode


def test_consumer_source_has_no_nonaborted_construction_or_success_variant() -> None:
    source = inspect.getsource(C)
    tree = ast.parse(source)
    assert "aborted=False" not in source
    assert not any(
        isinstance(node, ast.Call)
        and any(
            keyword.arg == "aborted"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is False
            for keyword in node.keywords
        )
        for node in ast.walk(tree)
    )
    definitions = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "P6Derived" not in definitions
    assert "derive_p6_cut" not in definitions
