"""Conjunct-level tests for the fail-closed reflux formal consumer."""
from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from orchestrator.campaign import model as M
from orchestrator.campaign import reflux_formal_consumer as C
from orchestrator.campaign import reflux_origin_binding as B
from orchestrator.campaign import reflux_origin_ledger as L
from orchestrator.campaign import reflux_origin_topology as T
from orchestrator.campaign import reflux_source_closure as S
from orchestrator.campaign import trigger_gate_binding as G
from orchestrator.campaign import wal as W
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.tests import reflux_origin_fixture_builder as F
from orchestrator.verifier import core as verifier_core
from orchestrator.verifier import report as verifier_report
from orchestrator.verifier.model import RW, WR, WW


WAVE_PRODUCTION_FILES = (
    "attempt_registry_core.py",
    "reflux_origin_artifacts.py",
    "reflux_source_closure.py",
    "reflux_result_evidence.py",
    "reflux_origin_ledger.py",
    "reflux_origin_topology.py",
    "reflux_origin_binding.py",
    "reflux_formal_consumer.py",
    "reflux_origin_client.py",
    "trial_registry.py",
    "autonomous_trial_completeness.py",
    "p3_autonomous_workload_trial.py",
    "wal.py",
    "s8b_descriptor.py",
    "s8c_arm_inputs.py",
)
_PRODUCER_VERBATIM_TRIGGER = (
    '{"variant":"probe-v","stage":"trigger_binding","env_tag":"probe-env",'
    '"ts":1788580452.4215896,"payload":{"build_attempt_id":'
    '"probe-attempt-0001","trigger_gate_binding":{"schema_version":'
    '"izanagi-trigger-gate-binding/v1","ir_schema":"izanagi-trigger-gate-ir/v1",'
    '"mask":7,"predicate_sha256":'
    '"9d6971707fdc3448fa20a707ba89f853df49705c6a8bdcd05068305b87cf3d56",'
    '"nonce":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",'
    '"source":null}}}'
)
_PRODUCER_VERBATIM_BUILD_START = (
    '{"variant":"probe-v","stage":"build_start","env_tag":"probe-env",'
    '"ts":1788580452.4419234,"payload":{"build_attempt_id":'
    '"probe-attempt-0001","trigger_gate_binding_commitment":'
    '"3971d4e14424e4d13bd63fc709a993ee12d8dfe13e072ce9960c9e51fa0b7029"}}'
)


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
        "enforcement_arm": "fixture-enforced",
        "arm_binding_digest_sha256": "d" * 64,
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


def _capability_digest(capability: B.OriginBindingCapability) -> str:
    record = {
        "authority_blob_sha256": capability.authority_blob_sha256,
        "source_closure_sha256": capability.source_closure_sha256,
        "origin_id": capability.origin_id,
        "cell_key": capability.cell_key,
        "authority_workload": {
            "descriptor_sha256": capability.authority_workload.descriptor_sha256,
            "records": capability.authority_workload.records,
            "threads": capability.authority_workload.threads,
        },
        "axis_semantics_sha256": capability.axis_semantics_sha256,
        "verifier_policy_sha256": capability.verifier_policy_sha256,
        "environment_contract_sha256": capability.environment_contract_sha256,
        "campaign_id": capability.campaign_id,
        "trial_workload": capability.trial_workload,
        "measurement_head": capability.measurement_head,
        "store_scope": capability.store_scope,
        "issuer_seal": "launch-admission-gate/v1",
    }
    return _digest(_canonical(record))


def _run_plan(capability: B.OriginBindingCapability) -> T.RecoveryEnvelope:
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
        capability_digest=_capability_digest(capability),
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
            "arm_binding_digest_sha256": "d" * 64,
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
    capability = _issued_capability()
    return _Case(
        fixture=fixture,
        capability=capability,
        closure=_issued_closure(),
        run_plan=_run_plan(capability),
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
        if "build_attempt_id" in wal_record:
            wal_record["build_attempt_id"] = selected_attempt
            continue
        payload = wal_record.get("payload")
        if type(payload) is dict and "build_attempt_id" in payload:
            payload["build_attempt_id"] = selected_attempt
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


def _rewrite_provenance(case: _Case, index: int, provenance: dict) -> None:
    record = copy.deepcopy(case.records[index])
    provenance_path = (
        case.fixture.evidence_root
        / record["evidence"]["execution_provenance_ref"]["path"]
    )
    raw = _canonical(provenance)
    provenance_path.write_bytes(raw)
    record["evidence"]["execution_provenance_ref"]["sha256"] = _digest(raw)
    _set_record(case, index, record)


def _projection_records(case: _Case, index: int) -> list[dict]:
    projection_path = case.fixture.evidence_root / case.records[index]["evidence"][
        "ordered_wal_ref"
    ]["path"]
    return copy.deepcopy(json.loads(projection_path.read_bytes())["records"])


def _fixture_witness_anomaly(case: _Case) -> dict:
    return copy.deepcopy(
        _projection_records(case, 0)[-1]["payload"]["verify"]["anomalies"][0]
    )


def _replace_terminal_fields(case: _Case, index: int, **fields: object) -> None:
    wal = _projection_records(case, index)
    wal[-1]["payload"].update(copy.deepcopy(fields))
    _rewrite_wal(case, index, wal)


def _replace_verify_fields(case: _Case, index: int, **fields: object) -> None:
    wal = _projection_records(case, index)
    wal[-1]["payload"]["verify"].update(copy.deepcopy(fields))
    _rewrite_wal(case, index, wal)


def _replace_rejected_witness(
    case: _Case,
    index: int,
    anomalies: list[dict],
    *,
    anomaly_count: int | bool | None = None,
    total_cycles: int | bool | None = None,
) -> str:
    constraint_sha256 = _digest(_canonical(anomalies[0]))
    selected_count = len(anomalies) if anomaly_count is None else anomaly_count
    selected_total = len(anomalies) if total_cycles is None else total_cycles
    wal = _projection_records(case, index)
    verify = wal[-1]["payload"]["verify"]
    verify["anomalies"] = copy.deepcopy(anomalies)
    verify["anomaly_count"] = selected_count
    verify["total_cycles"] = selected_total
    _rewrite_wal(case, index, wal)
    record = copy.deepcopy(case.records[index])
    record["physical_result"]["constraint_sha256"] = constraint_sha256
    _set_record(case, index, record)
    _set_member(case, index, constraint_sha256=constraint_sha256)
    return constraint_sha256


def _replace_all_rejected_witnesses(
    case: _Case,
    anomalies: list[dict],
    *,
    anomaly_count: int | bool | None = None,
    total_cycles: int | bool | None = None,
) -> None:
    for index in range(len(case.records)):
        _replace_rejected_witness(
            case,
            index,
            anomalies,
            anomaly_count=anomaly_count,
            total_cycles=total_cycles,
        )


def _replace_all_rejected_constraints(case: _Case, constraint_sha256: str) -> None:
    for index in range(len(case.records)):
        record = copy.deepcopy(case.records[index])
        record["physical_result"]["constraint_sha256"] = constraint_sha256
        _set_record(case, index, record)
        _set_member(case, index, constraint_sha256=constraint_sha256)


def _set_boolean_cycle_id(anomaly: dict) -> None:
    anomaly["cycle"][0] = True
    anomaly["edges"][0]["from"] = True
    anomaly["edges"][-1]["to"] = True


def _set_duplicate_cycle_ids(anomaly: dict) -> None:
    anomaly["cycle"] = [1, 1]
    for edge in anomaly["edges"]:
        edge["from"] = 1
        edge["to"] = 1


def _set_single_node_cycle(anomaly: dict) -> None:
    txid = anomaly["cycle"][0]
    edge = anomaly["edges"][0]
    edge["from"] = txid
    edge["to"] = txid
    anomaly["length"] = 1
    anomaly["cycle"] = [txid]
    anomaly["edges"] = [edge]


def _set_bogus_reason_type(anomaly: dict) -> None:
    edge = anomaly["edges"][0]
    edge["types"] = ["bogus"]
    edge["reasons"][0]["type"] = "bogus"


def _set_wr_reason_with_v_ver(anomaly: dict) -> None:
    edge = anomaly["edges"][0]
    edge["types"] = [WR]
    edge["reasons"][0]["type"] = WR


def _set_ww_reason_missing_u_ver(anomaly: dict) -> None:
    edge = anomaly["edges"][0]
    edge["types"] = [WW]
    edge["reasons"][0]["type"] = WW
    edge["reasons"][0].pop("u_ver")


def _set_rw_reason_missing_v_ver(anomaly: dict) -> None:
    anomaly["edges"][0]["reasons"][0].pop("v_ver")


def _wire(mask: int) -> str:
    return "".join("1" if mask & (1 << bit) else "0" for bit in range(5))


def _binding_projection(binding: G.TriggerGateBinding) -> dict:
    return {
        "mask": binding.mask,
        "candidate_wire": _wire(binding.mask),
        "trigger_gate_binding_commitment": G.commitment(binding),
    }


def _replace_case_trigger_binding(
    case: _Case,
    index: int,
    trigger_binding: dict,
) -> None:
    record = copy.deepcopy(case.records[index])
    record["trigger_binding"] = copy.deepcopy(trigger_binding)
    _set_record(case, index, record)
    _set_member(
        case,
        index,
        candidate_bytes=trigger_binding["candidate_wire"].encode("ascii"),
    )
    provenance_path = (
        case.fixture.evidence_root
        / case.records[index]["evidence"]["execution_provenance_ref"]["path"]
    )
    provenance = json.loads(provenance_path.read_bytes())
    provenance["trigger_binding"] = copy.deepcopy(trigger_binding)
    _rewrite_provenance(case, index, provenance)


def _live_trigger_record(
    case: _Case,
    index: int,
    binding: G.TriggerGateBinding,
    label: str,
) -> tuple[dict, str]:
    root = case.fixture.root / label
    layout = CampaignLayout(root=str(root)).ensure()
    attempt = case.records[index]["physical_result"]["build_attempt_id"]
    commitment = W.log_trigger_binding(
        layout,
        "fixture-v",
        "fixture-env",
        attempt,
        binding,
    )
    lines = (root / "runs" / "wal.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    return json.loads(lines[0]), commitment


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
        ("origin-workload", ("origin_binding", "workload")),
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


def test_fc03_rejects_run_plan_capability_digest_mismatch(case: _Case) -> None:
    changed = dataclasses.replace(
        case.run_plan, origin_binding_capability_sha256="e" * 64
    )
    _assert_reason(case, C.FormalReasonCode.FC03, run_plan=changed)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("build_attempt_id", "wrong-build-attempt"),
        ("campaign_id", "wrong-campaign"),
        ("workload", "wrong-workload"),
        ("contract_sha256", "e" * 64),
    ],
)
def test_fc03_rejects_each_execution_provenance_binding(
    case: _Case, field: str, value: str
) -> None:
    path = (
        case.fixture.evidence_root
        / case.records[0]["evidence"]["execution_provenance_ref"]["path"]
    )
    provenance = json.loads(path.read_bytes())
    provenance[field] = value
    _rewrite_provenance(case, 0, provenance)
    _assert_reason(case, C.FormalReasonCode.FC03)


def test_fc03_rejects_execution_provenance_trigger_binding_mismatch(
    case: _Case,
) -> None:
    path = (
        case.fixture.evidence_root
        / case.records[0]["evidence"]["execution_provenance_ref"]["path"]
    )
    provenance = json.loads(path.read_bytes())
    provenance["trigger_binding"]["mask"] = 31
    _rewrite_provenance(case, 0, provenance)
    _assert_reason(case, C.FormalReasonCode.FC03)


def test_fc05b_rejects_execution_provenance_without_receipt(case: _Case) -> None:
    path = (
        case.fixture.evidence_root
        / case.records[0]["evidence"]["execution_provenance_ref"]["path"]
    )
    provenance = json.loads(path.read_bytes())
    provenance.pop("execution_receipt_sha256")
    _rewrite_provenance(case, 0, provenance)
    _assert_reason(case, C.FormalReasonCode.FC05B)


def test_fc05b_rejects_empty_execution_provenance(case: _Case) -> None:
    _rewrite_provenance(case, 0, {})
    _assert_reason(case, C.FormalReasonCode.FC05B)


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


def test_fc05a_rejects_duplicate_build_attempt_id(case: _Case) -> None:
    duplicate = case.records[0]["physical_result"]["build_attempt_id"]
    wal = copy.deepcopy(json.loads(
        (case.fixture.evidence_root / case.records[1]["evidence"]["ordered_wal_ref"]["path"])
        .read_bytes()
    )["records"])
    _rewrite_wal(case, 1, wal, attempt=duplicate)
    provenance_path = (
        case.fixture.evidence_root
        / case.records[1]["evidence"]["execution_provenance_ref"]["path"]
    )
    provenance = json.loads(provenance_path.read_bytes())
    provenance["build_attempt_id"] = duplicate
    _rewrite_provenance(case, 1, provenance)
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
    wal = _projection_records(case, 0)
    wal[0]["payload"]["trigger_gate_binding"]["nonce"] = "f" * 64
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC05C)


def test_live_producer_trigger_without_source_reaches_only_p6_unavailable(
    case: _Case,
) -> None:
    binding = G.TriggerGateBinding(
        mask=7,
        predicate_sha256=G.expected_predicate_sha256(7),
        nonce="a" * 64,
        source=None,
    )
    trigger, commitment = _live_trigger_record(case, 0, binding, "producer-p1")
    assert commitment == case.records[0]["trigger_binding"][
        "trigger_gate_binding_commitment"
    ]
    terminal = _projection_records(case, 0)[-1]
    _rewrite_wal(case, 0, [trigger, terminal])

    result = _evaluate(case)
    assert type(result) is C.P6Unavailable
    assert result.reason_code is C.FormalReasonCode.P6_UNAVAILABLE


def test_live_producer_trigger_with_source_reaches_only_p6_unavailable(
    case: _Case,
) -> None:
    index = 19
    binding = G.TriggerGateBinding(
        mask=18,
        predicate_sha256=G.expected_predicate_sha256(18),
        nonce="b" * 64,
        source=G.SourceBinding(
            src_token="fixture-src",
            source_bytes_sha256="c" * 64,
        ),
    )
    projected = _binding_projection(binding)
    _replace_case_trigger_binding(case, index, projected)
    trigger, commitment = _live_trigger_record(case, index, binding, "producer-p2")
    assert commitment == projected["trigger_gate_binding_commitment"]
    terminal = _projection_records(case, index)[-1]
    _rewrite_wal(case, index, [trigger, terminal])

    result = _evaluate(case)
    assert type(result) is C.P6Unavailable
    assert result.reason_code is C.FormalReasonCode.P6_UNAVAILABLE


def test_verbatim_producer_records_with_only_attempt_transplanted_reach_p6(
    case: _Case,
) -> None:
    """The consumer reads only the trigger.

    This test independently pins build_start's commitment.
    """

    trigger = json.loads(_PRODUCER_VERBATIM_TRIGGER)
    build_start = json.loads(_PRODUCER_VERBATIM_BUILD_START)
    terminal = _projection_records(case, 0)[-1]
    _rewrite_wal(case, 0, [trigger, build_start, terminal])

    projected = C._wal_trigger([trigger, build_start, terminal])
    assert type(projected) is dict
    assert projected["trigger_gate_binding_commitment"] == build_start["payload"][
        "trigger_gate_binding_commitment"
    ]
    assert projected["trigger_gate_binding_commitment"] == (
        "3971d4e14424e4d13bd63fc709a993ee12d8dfe13e072ce9960c9e51fa0b7029"
    )
    result = _evaluate(case)
    assert type(result) is C.P6Unavailable
    assert result.reason_code is C.FormalReasonCode.P6_UNAVAILABLE


def test_fc05c_rejects_legacy_root_trigger_binding_shape(case: _Case) -> None:
    terminal = _projection_records(case, 0)[-1]
    legacy = {
        "kind": "TriggerGateBinding",
        "build_attempt_id": "placeholder",
        "trigger_binding": copy.deepcopy(case.records[0]["trigger_binding"]),
    }
    _rewrite_wal(case, 0, [legacy, terminal])
    _assert_reason(case, C.FormalReasonCode.FC05C)


def test_fc05c_rejects_trigger_payload_under_non_trigger_stage(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[0]["stage"] = "build_start"
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC05C)


def test_fc05c_rejects_duplicate_valid_trigger_stages(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal.insert(1, copy.deepcopy(wal[0]))
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC05C)


def test_fc05c_rejects_duplicate_trigger_stages_with_invalid_second_payload(
    case: _Case,
) -> None:
    wal = _projection_records(case, 0)
    invalid = copy.deepcopy(wal[0])
    invalid["payload"] = {"build_attempt_id": "placeholder"}
    wal.insert(1, invalid)
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC05C)


def test_fc05c_rejects_raw_trigger_binding_extra_key(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[0]["payload"]["trigger_gate_binding"]["extra"] = 1
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC05C)


def test_fc05c_rejects_trigger_payload_extra_key(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[0]["payload"]["extra"] = 1
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC05C)


def test_fc05c_rejects_root_attempt_shadow(case: _Case) -> None:
    wal = _projection_records(case, 0)
    attempt = case.records[0]["physical_result"]["build_attempt_id"]
    wal[0]["build_attempt_id"] = attempt
    wal[0]["payload"]["build_attempt_id"] = "fixture-shadow-attempt"
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC05C)


def test_fc05c_rejects_ledger_mask_only_mismatch(case: _Case) -> None:
    changed = copy.deepcopy(case.records[0]["trigger_binding"])
    changed["mask"] = 31
    _replace_case_trigger_binding(case, 0, changed)
    _assert_reason(case, C.FormalReasonCode.FC05C)


def test_fc05c_rejects_ledger_commitment_only_mismatch(case: _Case) -> None:
    changed = copy.deepcopy(case.records[0]["trigger_binding"])
    changed["trigger_gate_binding_commitment"] = "e" * 64
    _replace_case_trigger_binding(case, 0, changed)
    _assert_reason(case, C.FormalReasonCode.FC05C)


def test_fc05c_rejects_source_only_mismatch(case: _Case) -> None:
    index = 19
    binding = G.TriggerGateBinding(
        mask=18,
        predicate_sha256=G.expected_predicate_sha256(18),
        nonce="b" * 64,
        source=G.SourceBinding(
            src_token="fixture-src",
            source_bytes_sha256="c" * 64,
        ),
    )
    projected = _binding_projection(binding)
    _replace_case_trigger_binding(case, index, projected)
    trigger, _ = _live_trigger_record(case, index, binding, "producer-n10")
    trigger["payload"]["trigger_gate_binding"]["source"] = None
    terminal = _projection_records(case, index)[-1]
    _rewrite_wal(case, index, [trigger, terminal])
    _assert_reason(case, C.FormalReasonCode.FC05C)


def test_fc05c_rejects_boolean_trigger_timestamp(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[0]["ts"] = True
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC05C)


def test_fc05c_rejects_string_trigger_timestamp(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[0]["ts"] = "1788580082.583126"
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC05C)


def test_fc05c_rejects_integer_trigger_variant(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[0]["variant"] = 1
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
    wal = _projection_records(case, 1)
    donor_wal = _projection_records(case, 2)
    wal[0]["payload"]["trigger_gate_binding"] = copy.deepcopy(
        donor_wal[0]["payload"]["trigger_gate_binding"]
    )
    _rewrite_wal(case, 1, wal)
    provenance_path = (
        case.fixture.evidence_root
        / case.records[1]["evidence"]["execution_provenance_ref"]["path"]
    )
    provenance = json.loads(provenance_path.read_bytes())
    provenance["trigger_binding"] = copy.deepcopy(record["trigger_binding"])
    _rewrite_provenance(case, 1, provenance)
    _assert_reason(case, C.FormalReasonCode.FC06)


def test_fc06_rejects_validation_order_mismatch(case: _Case) -> None:
    batch = case.batches[0]
    members = list(batch.members)
    members[1], members[2] = members[2], members[1]
    case.batches = (dataclasses.replace(batch, members=tuple(members)),)
    _assert_reason(case, C.FormalReasonCode.FC06)


def test_real_dense_cycle4_anomaly_passes_witness_structure_validator() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = verifier_core.verify_trace_dir(
        str(Path(__file__).with_name("fixtures") / "r9_dense_cycle4"),
        protocol="silo",
        ccbench_root=repo_root / "external" / "ccbench",
    )
    report = verifier_report.result_to_dict(result)

    assert result.integrity.clean(), result.integrity.notes
    assert len(report["anomalies"]) == 1
    assert C._valid_witness_anomaly(report["anomalies"][0])


def test_real_dense_cycle4_report_schema_matches_consumer_key_sets() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = verifier_core.verify_trace_dir(
        str(Path(__file__).with_name("fixtures") / "r9_dense_cycle4"),
        protocol="silo",
        ccbench_root=repo_root / "external" / "ccbench",
    )
    report = verifier_report.result_to_dict(result)

    assert frozenset(report) - {"trace_dir"} == C._VERIFY_KEYS
    assert frozenset(report["stats"]) == C._VERIFY_STATS_KEYS
    assert frozenset(report["integrity"]) == C._VERIFY_INTEGRITY_KEYS
    assert (
        frozenset(report["integrity"]["permutation_violation_details"])
        == C._PERMUTATION_VIOLATION_DETAILS_KEYS
    )
    assert (
        frozenset(
            report["integrity"]["permutation_violation_details"]["counts"]
        )
        == C._PERMUTATION_VIOLATION_COUNT_KEYS
    )


def test_fc07_rejects_legacy_root_kind_terminal_shape(case: _Case) -> None:
    trigger = _projection_records(case, 0)[0]
    legacy = {
        "kind": "abort",
        "build_attempt_id": "placeholder",
        "candidate_attributable": True,
        "truncated": False,
        "witness_class_sha256s": [
            case.records[0]["physical_result"]["constraint_sha256"]
        ],
    }
    _rewrite_wal(case, 0, [trigger, legacy])
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_accepts_production_commit_terminal_shape(case: _Case) -> None:
    record = copy.deepcopy(case.records[0])
    record["physical_result"] = {
        "build_attempt_id": record["physical_result"]["build_attempt_id"],
        "outcome": "accepted",
        "constraint_sha256": None,
    }
    _set_record(case, 0, record)
    _set_member(case, 0, outcome="accepted", constraint_sha256=None)

    trigger = _projection_records(case, 0)[0]
    terminal = {
        "variant": "fixture-v",
        "stage": M.STAGE_COMMIT,
        "env_tag": "fixture-env",
        "ts": 0,
        "payload": {
            "build_attempt_id": "placeholder",
            "verify_configs": ["legacy", "s2"],
        },
    }
    _rewrite_wal(case, 0, [trigger, terminal])

    result = _evaluate(case)
    assert type(result) is C.P6Unavailable
    assert result.reason_code is C.FormalReasonCode.P6_UNAVAILABLE


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
    trigger = _projection_records(case, 0)[0]
    wal = [
        trigger,
        {
            "variant": "fixture-v",
            "stage": M.STAGE_COMMIT,
            "env_tag": "fixture-env",
            "ts": 0,
            "payload": {
                "build_attempt_id": "placeholder",
                "verify_configs": ["s2", "legacy"],
            },
        },
    ]
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_non_candidate_reason_with_valid_verify(case: _Case) -> None:
    _replace_terminal_fields(case, 0, reason="indeterminate")
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_non_candidate_verdict_with_valid_reason(case: _Case) -> None:
    _replace_verify_fields(case, 0, verdict="indeterminate")
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_dirty_integrity_with_valid_cycle(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[-1]["payload"]["verify"]["integrity"]["clean"] = False
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_serializable_true_with_reject_verdict(case: _Case) -> None:
    _replace_verify_fields(case, 0, serializable=True)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_certified_true_with_reject_verdict(case: _Case) -> None:
    _replace_verify_fields(case, 0, certified=True)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_anomaly_count_different_from_list_length(case: _Case) -> None:
    _replace_verify_fields(case, 0, anomaly_count=2, total_cycles=2)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_truncated_verifier_anomaly_list(case: _Case) -> None:
    _replace_verify_fields(case, 0, total_cycles=2)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_boolean_total_cycles(case: _Case) -> None:
    _replace_verify_fields(case, 0, anomaly_count=1, total_cycles=True)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_boolean_anomaly_count(case: _Case) -> None:
    _replace_verify_fields(case, 0, anomaly_count=True, total_cycles=1)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_two_anomalies_even_when_first_digest_matches(
    case: _Case,
) -> None:
    first = _fixture_witness_anomaly(case)
    second = copy.deepcopy(first)
    second["cycle"] = [3, 4]
    second["edges"][0]["from"] = 3
    second["edges"][0]["to"] = 4
    second["edges"][1]["from"] = 4
    second["edges"][1]["to"] = 3
    _replace_all_rejected_witnesses(case, [first, second])
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_ring_position_mismatch_with_matching_digest(
    case: _Case,
) -> None:
    anomaly = _fixture_witness_anomaly(case)
    edge = anomaly["edges"][0]
    edge["from"], edge["to"] = edge["to"], edge["from"]
    _replace_all_rejected_witnesses(case, [anomaly])
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_anomaly_extra_key_with_matching_digest(case: _Case) -> None:
    anomaly = _fixture_witness_anomaly(case)
    anomaly["extra"] = "not-production"
    _replace_all_rejected_witnesses(case, [anomaly])
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_empty_anomaly_with_matching_digest(case: _Case) -> None:
    _replace_all_rejected_witnesses(case, [{}])
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_witness_digest_mismatch_after_other_gates_pass(
    case: _Case,
) -> None:
    _replace_all_rejected_constraints(case, "e" * 64)
    _assert_reason(case, C.FormalReasonCode.FC07)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda anomaly: anomaly.__setitem__("phenomenon", "unknown"),
        lambda anomaly: anomaly.update({"length": 0, "cycle": [], "edges": []}),
        lambda anomaly: anomaly.__setitem__("cycle", "not-a-list"),
        _set_boolean_cycle_id,
        _set_duplicate_cycle_ids,
        lambda anomaly: anomaly.__setitem__("length", 3),
        lambda anomaly: anomaly.__setitem__("length", 2.0),
        _set_single_node_cycle,
        lambda anomaly: anomaly["edges"].pop(),
        lambda anomaly: anomaly["edges"][0].pop("types"),
        lambda anomaly: anomaly["edges"][0].__setitem__("types", []),
        lambda anomaly: anomaly["edges"][0].__setitem__("types", [1]),
        lambda anomaly: anomaly["edges"][0].__setitem__("from", 1.0),
        lambda anomaly: anomaly["edges"][0].__setitem__("to", 2.0),
        lambda anomaly: anomaly["edges"][0].__setitem__("reasons", []),
        lambda anomaly: anomaly["edges"][0]["reasons"][0].pop("key"),
        lambda anomaly: anomaly["edges"][0]["reasons"][0].update({"extra": 1}),
        lambda anomaly: anomaly["edges"][0]["reasons"][0].__setitem__("type", 1),
        _set_bogus_reason_type,
        lambda anomaly: anomaly["edges"][0]["types"].append(WW),
        lambda anomaly: anomaly.__setitem__("phenomenon", "G1c"),
        lambda anomaly: anomaly["edges"][0]["reasons"][0].__setitem__(
            "u_ver", "not-a-list"
        ),
        lambda anomaly: anomaly["edges"][0]["reasons"][0].__setitem__(
            "u_ver", [1]
        ),
        lambda anomaly: anomaly["edges"][0]["reasons"][0].__setitem__(
            "v_ver", [True, 2]
        ),
        _set_wr_reason_with_v_ver,
        _set_ww_reason_missing_u_ver,
        _set_rw_reason_missing_v_ver,
    ],
    ids=[
        "unknown-phenomenon",
        "empty-cycle",
        "cycle-not-list",
        "boolean-cycle-id",
        "duplicate-cycle-id",
        "length-mismatch",
        "length-float",
        "single-node-cycle",
        "edge-count-mismatch",
        "edge-key-missing",
        "empty-types",
        "non-string-type",
        "edge-from-float",
        "edge-to-float",
        "empty-reasons",
        "reason-required-key-missing",
        "reason-extra-key",
        "reason-type-not-string",
        "reason-type-outside-closed-set",
        "types-not-derived-from-reasons",
        "phenomenon-not-derived-from-types",
        "reason-version-not-list",
        "reason-version-not-two-elements",
        "reason-version-boolean",
        "wr-reason-has-v-ver",
        "ww-reason-missing-u-ver",
        "rw-reason-missing-v-ver",
    ],
)
def test_fc07_rejects_each_malformed_witness_structure(
    case: _Case,
    mutate,
) -> None:
    anomaly = _fixture_witness_anomaly(case)
    mutate(anomaly)
    _replace_all_rejected_witnesses(case, [anomaly])
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_verify_without_stats(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[-1]["payload"]["verify"].pop("stats")
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_stats_with_missing_key(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[-1]["payload"]["verify"]["stats"].pop("abort_reasons")
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_string_stats_count(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[-1]["payload"]["verify"]["stats"]["txns"] = "bad"
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_negative_stats_count(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[-1]["payload"]["verify"]["stats"]["txns"] = -1
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_non_dict_abort_reasons(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[-1]["payload"]["verify"]["stats"]["abort_reasons"] = []
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_string_abort_reason_count(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[-1]["payload"]["verify"]["stats"]["abort_reasons"] = {
        "fixture-abort": "bad"
    }
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_negative_abort_reason_count(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[-1]["payload"]["verify"]["stats"]["abort_reasons"] = {
        "fixture-abort": -1
    }
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_integrity_with_missing_key(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[-1]["payload"]["verify"]["integrity"].pop("notes")
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_permutation_details_with_missing_key(case: _Case) -> None:
    wal = _projection_records(case, 0)
    details = wal[-1]["payload"]["verify"]["integrity"][
        "permutation_violation_details"
    ]
    details.pop("sample")
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_clean_integrity_with_nonzero_wire_counter(
    case: _Case,
) -> None:
    wal = _projection_records(case, 0)
    wal[-1]["payload"]["verify"]["integrity"]["orphan_reads"] = 1
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_zero_framing_count_with_nonempty_details(
    case: _Case,
) -> None:
    wal = _projection_records(case, 0)
    wal[-1]["payload"]["verify"]["integrity"][
        "framing_violation_details"
    ] = [{"kind": "unexpected-detail"}]
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_non_list_framing_violation_details(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[-1]["payload"]["verify"]["integrity"][
        "framing_violation_details"
    ] = {}
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_non_string_integrity_note(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[-1]["payload"]["verify"]["integrity"]["notes"] = [1]
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_non_list_integrity_notes(case: _Case) -> None:
    wal = _projection_records(case, 0)
    wal[-1]["payload"]["verify"]["integrity"]["notes"] = {}
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_permutation_count_sum_mismatch(case: _Case) -> None:
    wal = _projection_records(case, 0)
    details = wal[-1]["payload"]["verify"]["integrity"][
        "permutation_violation_details"
    ]
    details["counts"]["size-changed"] = 1
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_permutation_count_key_set_mismatch(case: _Case) -> None:
    wal = _projection_records(case, 0)
    details = wal[-1]["payload"]["verify"]["integrity"][
        "permutation_violation_details"
    ]
    details["counts"]["not-production"] = 0
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_non_dict_permutation_counts(case: _Case) -> None:
    wal = _projection_records(case, 0)
    details = wal[-1]["payload"]["verify"]["integrity"][
        "permutation_violation_details"
    ]
    details["counts"] = []
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_float_permutation_count(case: _Case) -> None:
    wal = _projection_records(case, 0)
    details = wal[-1]["payload"]["verify"]["integrity"][
        "permutation_violation_details"
    ]
    details["counts"]["size-changed"] = 0.0
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_negative_permutation_count_with_matching_sum(
    case: _Case,
) -> None:
    wal = _projection_records(case, 0)
    details = wal[-1]["payload"]["verify"]["integrity"][
        "permutation_violation_details"
    ]
    details["counts"]["size-changed"] = -1
    details["counts"]["rcdptr-set-changed"] = 1
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_non_list_permutation_sample(case: _Case) -> None:
    wal = _projection_records(case, 0)
    details = wal[-1]["payload"]["verify"]["integrity"][
        "permutation_violation_details"
    ]
    details["sample"] = "bad"
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_rejects_non_list_unknown_reason_sample(case: _Case) -> None:
    wal = _projection_records(case, 0)
    details = wal[-1]["payload"]["verify"]["integrity"][
        "permutation_violation_details"
    ]
    details["unknown_reason_sample"] = {}
    _rewrite_wal(case, 0, wal)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc07_converts_witness_canonicalization_artifact_error(
    case: _Case,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = C.canonical_json_bytes

    def fail_only_for_anomaly(value: object) -> bytes:
        if type(value) is dict and set(value) == C._ANOMALY_KEYS:
            raise C.ArtifactError("fixture canonicalization failure")
        return original(value)

    monkeypatch.setattr(C, "canonical_json_bytes", fail_only_for_anomaly)
    _assert_reason(case, C.FormalReasonCode.FC07)


def test_fc09_rejects_nonexact_rejected_class_set(case: _Case) -> None:
    """constraint_sha256 の単一変更は FC04 ではなく FC09 が先取して拒否する。"""
    _mutate_record(
        case,
        0,
        ("physical_result", "constraint_sha256"),
        "e" * 64,
    )
    _assert_reason(case, C.FormalReasonCode.FC09)


def test_fc09_rejects_kmax_excess(case: _Case) -> None:
    second = _fixture_witness_anomaly(case)
    second["cycle"] = [3, 4]
    second["edges"][0]["from"] = 3
    second["edges"][0]["to"] = 4
    second["edges"][1]["from"] = 4
    second["edges"][1]["to"] = 3
    _replace_rejected_witness(case, 1, [second])
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
        "arm_binding_digest_sha256",
        "generator_closure",
        "reason_code",
        "issuer_seal",
    }
    assert record["enforcement_arm"] == "fixture-enforced"
    assert record["arm_binding_digest_sha256"] == "d" * 64
    assert all("receipt_sha256" not in key for key in record)
    assert C.canonical_formal_consumer_receipt_bytes(result.receipt) == _canonical(record)
    assert not C.canonical_formal_consumer_receipt_bytes(result.receipt).endswith(b"\n")


def test_formal_consumer_rejects_invalid_arm_binding_digest_before_issuance(
    case: _Case,
) -> None:
    with pytest.raises(ValueError, match="arm_binding_digest_sha256"):
        _evaluate(case, arm_binding_digest_sha256="not-a-digest")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("enforcement_arm", "caller-selected"),
        ("arm_binding_digest_sha256", "e" * 64),
    ],
)
def test_formal_consumer_requires_digest_and_label_from_issued_binding(
    case: _Case,
    field: str,
    value: str,
) -> None:
    with pytest.raises(ValueError, match="differs from issued arm binding"):
        _evaluate(case, **{field: value})


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
    first_result = _evaluate(case)
    second_snapshot = dataclasses.replace(case.snapshot, forfeited_queries=1)
    second_result = _evaluate(case, origin_snapshot=second_snapshot)
    assert type(first_result) is C.P6Unavailable
    assert type(second_result) is C.P6Unavailable
    assert first_result.receipt.operation_id == second_result.receipt.operation_id
    assert (
        first_result.receipt.origin_sealed_payload_sha256
        != second_result.receipt.origin_sealed_payload_sha256
    )
    C.consume_formal_consumer_receipt(
        first_result.receipt,
        operation_id=case.operation_id,
        input_state_commitment=case.snapshot.state_commitment,
        decision=first_result.decision,
    )
    with pytest.raises(C.FormalReceiptError) as caught:
        C.consume_formal_consumer_receipt(
            second_result.receipt,
            operation_id=case.operation_id,
            input_state_commitment=second_snapshot.state_commitment,
            decision=second_result.decision,
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
        "arm_binding_digest_sha256",
    }
    assert nested["reason_code"] == "P6Unavailable"
    assert nested["formal_receipt_sha256"] is not None
    assert nested["evidence_root_sha256"] is not None
    assert nested["arm_binding_digest_sha256"] == "d" * 64
    assert type(result.projection.reason_code) is C.FormalReasonCode


def test_consumer_source_has_no_nonaborted_construction_or_success_variant() -> None:
    assert len(WAVE_PRODUCTION_FILES) == 15
    assert set(WAVE_PRODUCTION_FILES) == {
        "attempt_registry_core.py",
        "autonomous_trial_completeness.py",
        "p3_autonomous_workload_trial.py",
        "reflux_formal_consumer.py",
        "reflux_origin_artifacts.py",
        "reflux_origin_binding.py",
        "reflux_origin_client.py",
        "reflux_origin_ledger.py",
        "reflux_origin_topology.py",
        "reflux_result_evidence.py",
        "reflux_source_closure.py",
        "s8b_descriptor.py",
        "s8c_arm_inputs.py",
        "trial_registry.py",
        "wal.py",
    }
    campaign_root = Path(C.__file__).resolve().parent
    sources = {
        name: (campaign_root / name).read_text(encoding="utf-8")
        for name in WAVE_PRODUCTION_FILES
    }
    assert all((campaign_root / name).is_file() for name in WAVE_PRODUCTION_FILES)
    positional_nonaborted_calls = []
    for name, source in sources.items():
        tree = ast.parse(source, filename=name)
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
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
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and (
                    (
                        isinstance(node.func, ast.Name)
                        and node.func.id == "OriginSealed"
                    )
                    or (
                        isinstance(node.func, ast.Attribute)
                        and node.func.attr == "OriginSealed"
                    )
                )
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value is False
            ):
                continue
            ancestor = parents[node]
            wrapper_name = None
            if isinstance(ancestor, ast.Call):
                if isinstance(ancestor.func, ast.Name):
                    wrapper_name = ancestor.func.id
                elif isinstance(ancestor.func, ast.Attribute):
                    wrapper_name = ancestor.func.attr
            assignment_name = None
            function_name = None
            while not isinstance(ancestor, ast.Module):
                if (
                    assignment_name is None
                    and isinstance(ancestor, ast.Assign)
                    and len(ancestor.targets) == 1
                    and isinstance(ancestor.targets[0], ast.Name)
                ):
                    assignment_name = ancestor.targets[0].id
                if isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    function_name = ancestor.name
                    break
                ancestor = parents[ancestor]
            positional_nonaborted_calls.append(
                (name, function_name, wrapper_name, assignment_name)
            )

    assert positional_nonaborted_calls == [
        (
            "reflux_origin_ledger.py",
            "_check_budget_codec_feasibility",
            "_feasibility_event_frame",
            "class_frame",
        )
    ]

    consumer_tree = ast.parse(
        sources["reflux_formal_consumer.py"],
        filename="reflux_formal_consumer.py",
    )
    definitions = {
        node.name
        for node in ast.walk(consumer_tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "P6Derived" not in definitions
    assert "derive_p6_cut" not in definitions
