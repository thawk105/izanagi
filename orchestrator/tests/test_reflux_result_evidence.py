from __future__ import annotations

import copy
import hashlib
import json
import os
from dataclasses import dataclass, fields, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.campaign import reflux_origin_ledger as ledger
from orchestrator.campaign import reflux_origin_binding as origin_binding
from orchestrator.campaign import reflux_result_evidence as evidence
from orchestrator.campaign import env_attestation, env_contract, execution_guard
from orchestrator.campaign import trigger_gate_binding
from orchestrator.campaign import wal
from orchestrator.campaign.layout import (
    CampaignLayout, ExplorationCampaignLayout, exploration_campaign_layout,
)
from orchestrator.campaign.model import (
    STAGE_ABORT,
    STAGE_BUILD_DONE,
    STAGE_BUILD_START,
    STAGE_COMMIT,
    STAGE_VERIFY_DONE,
)
from orchestrator.tests.reflux_origin_fixture_builder import (
    build_execution_provenance,
    build_launch_admission_inputs,
    build_ordered_wal_projection,
    build_result_evidence_record,
)
from orchestrator.verifier import result_to_dict, verify_trace_dir
from orchestrator.verifier.model import VerifyResult


_RECORD_RAW_GOLDEN = "5c0ac03d7ccd53153f70c2e10dde301aa4097eeee61f9118eeefc49b3ad24767"
_LEDGER_EVIDENCE_DIGEST_GOLDEN = "5c0ac03d7ccd53153f70c2e10dde301aa4097eeee61f9118eeefc49b3ad24767"
_OUTER_SALTED_COMMITMENT_GOLDEN = "b9e20f457bec0bb2ed7e866c7bd175cee9fba8779a96fe2085fd7f79d5cb6365"
_WRONG_DOMAIN_PREFIXED_RAW_GOLDEN = "610867ca65d585909812e468368f931a76fdf0a7faca488a0a294554ed97735f"
_SALT = "0123456789abcdef0123456789abcdef"
_FIXTURE_ROOT = Path(__file__).with_name("fixtures")
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BUILD_ATTEMPT_ID = "producer-build-attempt-0000"
_ORDERED_VERIFIERS = ("legacy", "s2")


def _independent_canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def _synthetic_silo_source(tmp_path: Path) -> Path:
    ccbench_root = tmp_path / "ccbench"
    silo_source = ccbench_root / "cc" / "silo"
    silo_source.mkdir(parents=True, exist_ok=True)
    (silo_source / "CMakeLists.txt").write_text(
        "ccbench_add_protocol(silo SOURCES transaction.cc WORKLOADS ycsb)\n",
        encoding="utf-8",
    )
    (silo_source / "transaction.cc").write_text(
        "#if TRACE\n"
        "izanagi_trace::emit_lock_violation(0, 0, {}, {});\n"
        'izanagi_trace::stream(0) << "P ";\n'
        "#endif\n",
        encoding="utf-8",
    )
    return ccbench_root


def _verify_fixture(
    tmp_path: Path, name: str, *, max_report: int | None = 20
) -> VerifyResult:
    return verify_trace_dir(
        str(_FIXTURE_ROOT / name),
        max_report=max_report,
        protocol="silo",
        ccbench_root=_synthetic_silo_source(tmp_path),
    )


def _verify_snapshot(result: VerifyResult) -> dict:
    snapshot = result_to_dict(result)
    snapshot.pop("trace_dir", None)
    return snapshot


def _wal_record(stage: str, payload: dict) -> dict:
    return {
        "variant": "fixture-v",
        "stage": stage,
        "env_tag": "fixture-env",
        "ts": 0,
        "payload": payload,
    }


def _abort_terminal(result: VerifyResult, *, snapshot: dict | None = None) -> dict:
    return _wal_record(
        STAGE_ABORT,
        {
            "reason": result.verdict,
            "build_attempt_id": _BUILD_ATTEMPT_ID,
            "build_admission_receipt_sha256": "a" * 64,
            "verify": _verify_snapshot(result) if snapshot is None else snapshot,
            "workload": {"tag": "ycsb-a"},
        },
    )


def _commit_terminal(*, verify_configs: list[str] | None = None) -> dict:
    return _wal_record(
        STAGE_COMMIT,
        {
            "verify_configs": (
                list(_ORDERED_VERIFIERS)
                if verify_configs is None
                else verify_configs
            ),
            "build_attempt_id": _BUILD_ATTEMPT_ID,
            "build_admission_receipt_sha256": "a" * 64,
            "fitness_tps": None,
            "note": "no-bench",
        },
    )


def _projection_bytes(
    *, records: list[dict], build_attempt_id: str = _BUILD_ATTEMPT_ID
) -> bytes:
    source_raw = _independent_canonical(records)
    projection = build_ordered_wal_projection(
        source_wal_ref={
            "path": "wal/source/producer.json",
            "sha256": _sha(source_raw),
        },
        byte_start=0,
        byte_end=len(source_raw),
        build_attempt_id=build_attempt_id,
        records=records,
    )
    return _independent_canonical(projection)


def _derive(*, records: list[dict], result: VerifyResult | None = None):
    return evidence.derive_physical_result(
        ordered_wal_projection_bytes=_projection_bytes(records=records),
        build_attempt_id=_BUILD_ATTEMPT_ID,
        ordered_verifiers=_ORDERED_VERIFIERS,
        verify_result=result,
    )


def _assemble_from_fixture(
    fixture_record: dict,
    derived: evidence.DerivedPhysicalResult,
) -> dict:
    return evidence.assemble_result_evidence_record(
        origin_binding=fixture_record["origin_binding"],
        trial_binding=fixture_record["trial_binding"],
        ledger_member=fixture_record["ledger_member"],
        p6_plan=fixture_record["p6_plan"],
        trigger_binding=fixture_record["trigger_binding"],
        derived=derived,
        ordered_wal_ref=fixture_record["evidence"]["ordered_wal_ref"],
        execution_provenance_ref=fixture_record["evidence"][
            "execution_provenance_ref"
        ],
    )


def _assert_issuance_refused(
    evidence_root: Path,
    *,
    records: list[dict],
    result: VerifyResult | None,
) -> None:
    record = None
    path = None
    with pytest.raises(evidence.ResultEvidenceIssuanceRefused):
        derived = _derive(records=records, result=result)
        record = _assemble_from_fixture(
            build_result_evidence_record(), derived
        )
        path = evidence.issue_result_evidence_record(
            evidence_root=evidence_root, record=record
        )
    assert record is None
    assert path is None
    assert not evidence_root.exists()


def _resolution_tree(root: Path) -> dict:
    record = build_result_evidence_record()
    projection = build_ordered_wal_projection()
    provenance = build_execution_provenance()
    source_raw = _independent_canonical(projection["records"])
    _write(root / projection["source_wal_ref"]["path"], source_raw)
    _write(
        root / record["evidence"]["ordered_wal_ref"]["path"],
        _independent_canonical(projection),
    )
    _write(
        root / record["evidence"]["execution_provenance_ref"]["path"],
        _independent_canonical(provenance),
    )
    return record


def _rewrite_projection(root: Path, record: dict, projection: dict) -> None:
    raw = _independent_canonical(projection)
    path = root / record["evidence"]["ordered_wal_ref"]["path"]
    path.write_bytes(raw)
    record["evidence"]["ordered_wal_ref"]["sha256"] = _sha(raw)


def _rewrite_provenance(root: Path, record: dict, provenance: dict) -> None:
    raw = _independent_canonical(provenance)
    path = root / record["evidence"]["execution_provenance_ref"]["path"]
    path.write_bytes(raw)
    record["evidence"]["execution_provenance_ref"]["sha256"] = _sha(raw)


def _issued_origin_capability(
    contract_sha256: str,
) -> origin_binding.OriginBindingCapability:
    raw = build_launch_admission_inputs(
        environment_contract_sha256=contract_sha256,
    )
    seal = object()
    capability = origin_binding.OriginBindingCapability(
        authority_blob_sha256=raw["authority_blob_sha256"],
        source_closure_sha256=raw["source_closure_sha256"],
        origin_id=raw["origin_id"],
        cell_key=raw["cell_key"],
        authority_workload=origin_binding.AuthorityWorkload(
            **raw["authority_workload"]
        ),
        axis_semantics_sha256=raw["axis_semantics_sha256"],
        verifier_policy_sha256=raw["verifier_policy_sha256"],
        environment_contract_sha256=raw["environment_contract_sha256"],
        campaign_id=raw["campaign_id"],
        trial_workload=raw["trial_workload"],
        measurement_head=raw["measurement_head"],
        store_scope=raw["store_scope"],
        enforcement_arm="fixture-enforced",
        arm_binding_digest_sha256="d" * 64,
        _seal=seal,
    )
    origin_binding._ISSUED_CAPABILITY_FIELDS[seal] = (
        origin_binding._capability_fields(capability)
    )
    return capability


def _producer_context(
    evidence_root: Path,
    *,
    contract: env_contract.ExecutionEnvironmentContract | None = None,
    verified_calibration: object | None = None,
) -> evidence.ResultEvidenceIssuanceContext:
    contract = contract or env_contract.authorize("linux-baremetal").contract
    fixture_record = build_result_evidence_record(
        origin_binding__environment_contract_sha256=contract.contract_sha256,
    )
    capability = _issued_origin_capability(contract.contract_sha256)
    assert fixture_record["origin_binding"] == {
        "authority_blob_sha256": capability.authority_blob_sha256,
        "source_closure_sha256": capability.source_closure_sha256,
        "origin_id": capability.origin_id,
        "cell_key": capability.cell_key,
        "workload": capability.trial_workload,
        "axis_semantics_sha256": capability.axis_semantics_sha256,
        "verifier_policy_sha256": capability.verifier_policy_sha256,
        "environment_contract_sha256": capability.environment_contract_sha256,
    }
    member = fixture_record["ledger_member"]
    return evidence.ResultEvidenceIssuanceContext(
        origin_capability=capability,
        evidence_root=evidence_root,
        batch_id=member["batch_id"],
        query_ordinal=member["query_ordinal"],
        iteration_index=member["iteration_index"],
        replicate_ordinal=member["replicate_ordinal"],
        p6_plan=fixture_record["p6_plan"],
        trial_binding=fixture_record["trial_binding"],
        origin_binding=fixture_record["origin_binding"],
        ordered_verifiers=_ORDERED_VERIFIERS,
        expected_record_path=evidence.result_evidence_relative_path(
            fixture_record
        ).as_posix(),
        env_tag=contract.env_tag,
        attestation_mode=contract.attestation_mode,
        verified_calibration=verified_calibration,
    )


def _producer_layout(
    evidence_root: Path, *, kind: str = "official",
) -> CampaignLayout | ExplorationCampaignLayout:
    if kind == "exploration":
        return exploration_campaign_layout(
            "fixture-physical-run", os.fspath(evidence_root)
        ).ensure()
    return CampaignLayout(
        root=os.fspath(evidence_root / "campaigns" / "fixture-physical-run")
    ).ensure()


def _producer_binding() -> trigger_gate_binding.TriggerGateBinding:
    mask = 7
    return trigger_gate_binding.TriggerGateBinding(
        mask=mask,
        predicate_sha256=trigger_gate_binding.expected_predicate_sha256(mask),
        nonce="a" * 64,
        source=None,
    )


def _log_producer_attempt(
    layout: object,
    *,
    build_attempt_id: str,
    result: VerifyResult,
    first_ts: int,
) -> None:
    binding = _producer_binding()
    wal.log(
        layout,
        "fixture-v",
        trigger_gate_binding.WAL_RECORD_STAGE,
        "fixture-env",
        {
            "build_attempt_id": build_attempt_id,
            wal.TRIGGER_BINDING_PAYLOAD_KEY: trigger_gate_binding.to_record(binding),
        },
        ts=first_ts,
    )
    for offset, stage in enumerate(
        (STAGE_BUILD_START, STAGE_BUILD_DONE, STAGE_VERIFY_DONE), start=1
    ):
        wal.log(
            layout,
            "fixture-v",
            stage,
            "fixture-env",
            {"build_attempt_id": build_attempt_id},
            ts=first_ts + offset,
        )
    terminal = _abort_terminal(result)
    terminal["payload"]["build_attempt_id"] = build_attempt_id
    wal.log(
        layout,
        terminal["variant"],
        terminal["stage"],
        terminal["env_tag"],
        terminal["payload"],
        ts=first_ts + 4,
    )


def _execution_receipt() -> dict:
    contract = env_contract.authorize("linux-baremetal").contract
    return execution_guard.build_receipt(contract)


def _required_execution_inputs() -> tuple[
    env_contract.ExecutionEnvironmentContract,
    env_attestation.VerifiedCalibration,
    dict,
]:
    contract = env_contract.GENERATIONS["pegasus"][0].contract
    verified = env_attestation.load_verified_calibration(contract, _REPO_ROOT)
    expected = env_attestation.profile_to_dict(verified.attestation_profile)
    clock_samples = expected["effective_clock"]["samples_mhz"]
    median_clock = sorted(clock_samples)[len(clock_samples) // 2]
    expected["effective_clock"]["samples_mhz"] = [
        median_clock for _sample in clock_samples
    ]
    del expected["effective_clock"]["tolerance_pct"]
    observed = env_attestation.normalize_observed_profile(expected)
    receipt = execution_guard.attest_and_build_receipt(
        contract,
        verified,
        probe_fn=lambda: observed,
        now_fn=lambda: "2026-09-09T00:00:00Z",
    )
    return contract, verified, receipt


def _issue_producer_record(
    *,
    layout: object,
    context: evidence.ResultEvidenceIssuanceContext,
    build_attempt_id: str,
    verify_result: object | None,
    execution_receipt: object | None,
    environment_contract: env_contract.ExecutionEnvironmentContract | None = None,
) -> Path:
    capability = context.origin_capability
    assert type(capability) is origin_binding.OriginBindingCapability
    contract = (
        environment_contract
        if environment_contract is not None
        else env_contract.authorize("linux-baremetal").contract
    )
    return evidence.issue_campaign_result_evidence(
        layout=layout,
        context=context,
        build_attempt_id=build_attempt_id,
        verify_result=verify_result,
        campaign_run_identity="fixture-run-00000000",
        campaign_id=capability.campaign_id,
        environment_contract=contract,
        execution_receipt=execution_receipt,
    )


def _file_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_exact_nine_key_schema_and_nested_cardinalities():
    record = build_result_evidence_record()
    assert evidence.RESULT_EVIDENCE_SCHEMA_VERSION == "result-evidence/v1"
    assert record["schema_version"] == "result-evidence/v1"
    assert set(record) == {
        "schema_version",
        "issuer",
        "origin_binding",
        "trial_binding",
        "ledger_member",
        "p6_plan",
        "trigger_binding",
        "physical_result",
        "evidence",
    }
    assert len(record["origin_binding"]) == 8
    assert len(record["trial_binding"]) == 3
    assert len(record["ledger_member"]) == 4
    assert len(record["p6_plan"]) == 3
    assert len(record["trigger_binding"]) == 3
    assert len(record["physical_result"]) == 3
    assert len(record["evidence"]) == 2
    assert set(record["evidence"]) == {
        "ordered_wal_ref", "execution_provenance_ref",
    }
    assert evidence.validate_result_evidence(record) == record


@pytest.mark.parametrize(
    "mutate",
    [
        lambda record: record.update({"unexpected": 1}),
        lambda record: record.pop("issuer"),
        lambda record: record.__setitem__("origin_binding", []),
    ],
    ids=["top-level-extra", "top-level-missing", "wrong-object-type"],
)
def test_exact_schema_rejects_one_extra_one_missing_and_wrong_type(mutate):
    record = build_result_evidence_record()
    mutate(record)
    with pytest.raises(evidence.ResultEvidenceError):
        evidence.validate_result_evidence(record)


def test_self_hash_field_is_rejected_instead_of_proving_the_record():
    record = build_result_evidence_record()
    record["sha256"] = "0" * 64
    with pytest.raises(evidence.ResultEvidenceError):
        evidence.canonical_result_evidence_bytes(record)


def test_record_outcome_is_closed_and_accepted_has_no_constraint():
    accepted = build_result_evidence_record(
        physical_result__outcome="accepted",
        physical_result__constraint_sha256=None,
    )
    assert evidence.validate_result_evidence(accepted)["physical_result"] == {
        "build_attempt_id": "fixture-build-attempt-0000",
        "outcome": "accepted",
        "constraint_sha256": None,
    }
    tombstoned = build_result_evidence_record(
        physical_result__outcome="tombstoned",
        physical_result__constraint_sha256=None,
    )
    with pytest.raises(evidence.ResultEvidenceError, match="accepted or rejected"):
        evidence.validate_result_evidence(tombstoned)


def test_canonical_bytes_are_independently_pinned_without_a_trailing_lf():
    record = build_result_evidence_record()
    expected = _independent_canonical(record)
    actual = evidence.canonical_result_evidence_bytes(record)
    assert actual == expected
    assert len(actual) == 1848
    assert not actual.endswith(b"\n")


def test_hash_layer_1_record_raw_sha256_has_literal_golden():
    raw = _independent_canonical(build_result_evidence_record())
    assert evidence.RECORD_RAW_SHA256_LAYER == "result-evidence-record/raw-sha256/v1"
    assert evidence.result_evidence_record_raw_sha256(raw) == _RECORD_RAW_GOLDEN


def test_hash_layer_2_ledger_evidence_digest_has_separate_literal_golden():
    raw = _independent_canonical(build_result_evidence_record())
    assert evidence.LEDGER_EVIDENCE_DIGEST_LAYER == "ledger-evidence-digest/raw-sha256/v1"
    assert evidence.ledger_evidence_digest_sha256(raw) == _LEDGER_EVIDENCE_DIGEST_GOLDEN


def test_hash_layer_3_outer_salted_commitment_has_separate_literal_golden():
    digest = ledger.EvidenceDigest(_LEDGER_EVIDENCE_DIGEST_GOLDEN)
    assert evidence.LEDGER_OUTER_COMMITMENT_LAYER == "ledger-result-evidence/salted-domain/v1"
    assert evidence.ledger_result_evidence_outer_commitment(
        result_evidence_salt=_SALT,
        outcome="rejected",
        evidence_digest=digest,
    ) == _OUTER_SALTED_COMMITMENT_GOLDEN


def test_hash_layer_mutation_domain_prefixing_raw_record_is_detected():
    raw = _independent_canonical(build_result_evidence_record())
    wrong = hashlib.sha256(
        b"izanagi-reflux-origin-result-evidence/v1\0" + raw
    ).hexdigest()
    assert wrong == _WRONG_DOMAIN_PREFIXED_RAW_GOLDEN
    assert evidence.result_evidence_record_raw_sha256(raw) != wrong


def test_content_addressed_resolver_rejects_sha256_mismatch(tmp_path):
    record = _resolution_tree(tmp_path)
    record["evidence"]["ordered_wal_ref"]["sha256"] = "0" * 64
    with pytest.raises(evidence.ResultEvidenceError, match="sha256 mismatch"):
        evidence.resolve_result_evidence(record, evidence_root=tmp_path)


@pytest.mark.parametrize(
    "provenance",
    [
        {},
        build_execution_provenance(execution_receipt_sha256=None),
        build_execution_provenance(trigger_binding={}),
        build_execution_provenance(campaign_run_identity=...),
        build_execution_provenance(campaign_run_identity=None),
        build_execution_provenance(campaign_run_identity=""),
        build_execution_provenance(campaign_run_identity=7),
        build_execution_provenance(unexpected="closed-schema"),
        build_execution_provenance(schema_version="execution-provenance/v1"),
        build_execution_provenance(
            campaign_run_identity="../foreign-run-00000000"
        ),
        build_execution_provenance(campaign_run_identity="fixture-run-0000"),
    ],
    ids=[
        "empty", "missing-receipt", "missing-trigger", "missing-run-identity",
        "null-run-identity", "empty-run-identity", "non-string-run-identity",
        "extra", "v1", "path-invalid-run-identity", "non-ident-run-identity",
    ],
)
def test_execution_provenance_is_closed_and_nonempty(tmp_path, provenance):
    record = _resolution_tree(tmp_path)
    if provenance.get("execution_receipt_sha256") is None:
        provenance.pop("execution_receipt_sha256", None)
    _rewrite_provenance(tmp_path, record, provenance)
    with pytest.raises(evidence.ResultEvidenceError, match="execution provenance"):
        evidence.resolve_result_evidence(record, evidence_root=tmp_path)


def test_execution_provenance_v2_has_exact_eight_keys(tmp_path):
    provenance = build_execution_provenance()
    assert provenance["schema_version"] == "execution-provenance/v2"
    assert set(provenance) == evidence._EXECUTION_PROVENANCE_V2_KEYS == {
        "schema_version",
        "build_attempt_id",
        "campaign_id",
        "workload",
        "contract_sha256",
        "trigger_binding",
        "execution_receipt_sha256",
        "campaign_run_identity",
    }
    record = _resolution_tree(tmp_path)
    resolved = evidence.resolve_result_evidence(record, evidence_root=tmp_path)
    assert resolved.execution_provenance == provenance


def test_content_addressed_resolver_rejects_path_outside_root(tmp_path):
    record = _resolution_tree(tmp_path)
    outside = tmp_path.parent / "outside-result-evidence.json"
    outside.write_bytes(b"outside")
    record["evidence"]["ordered_wal_ref"] = {
        "path": "../outside-result-evidence.json",
        "sha256": _sha(b"outside"),
    }
    with pytest.raises(evidence.ResultEvidenceError, match="escapes"):
        evidence.resolve_result_evidence(record, evidence_root=tmp_path)


def test_content_addressed_resolver_rejects_symlink_ancestor(tmp_path):
    record = _resolution_tree(tmp_path)
    (tmp_path / "projection-alias").symlink_to(tmp_path / "wal" / "projections")
    record["evidence"]["ordered_wal_ref"]["path"] = "projection-alias/0000.json"
    with pytest.raises(evidence.ResultEvidenceError, match="symlink"):
        evidence.resolve_result_evidence(record, evidence_root=tmp_path)


def test_path_aliases_normalize_to_the_same_physical_identity(tmp_path):
    record = _resolution_tree(tmp_path)
    direct_ref = record["evidence"]["ordered_wal_ref"]
    alias_ref = dict(direct_ref, path="wal/projections/../projections/0000.json")
    direct = evidence.resolve_content_addressed_ref(
        evidence_root=tmp_path, reference=direct_ref
    )
    alias = evidence.resolve_content_addressed_ref(
        evidence_root=tmp_path, reference=alias_ref
    )
    assert direct.identity == alias.identity
    assert direct.normalized_path == alias.normalized_path


def test_wal_declared_range_must_match_actual_source_bytes(tmp_path):
    record = _resolution_tree(tmp_path)
    projection = build_ordered_wal_projection()
    changed_records = copy.deepcopy(projection["records"])
    changed_records[0]["kind"] = "different-physical-record"
    changed_source = _independent_canonical(changed_records)
    source_path = tmp_path / projection["source_wal_ref"]["path"]
    source_path.write_bytes(changed_source)
    projection["source_wal_ref"]["sha256"] = _sha(changed_source)
    projection["byte_end"] = len(changed_source)
    _rewrite_projection(tmp_path, record, projection)

    with pytest.raises(evidence.ResultEvidenceError, match="do not match"):
        evidence.resolve_result_evidence(record, evidence_root=tmp_path)


def test_batch_rejects_overlapping_source_wal_ranges(tmp_path):
    first = _resolution_tree(tmp_path)
    second = copy.deepcopy(first)
    second["ledger_member"]["query_ordinal"] = 1
    projection = build_ordered_wal_projection(
        source_wal_ref__path="wal/source/../source/0000.json"
    )
    projection_raw = _independent_canonical(projection)
    projection_path = "wal/projections/alias-0000.json"
    _write(tmp_path / projection_path, projection_raw)
    second["evidence"]["ordered_wal_ref"] = {
        "path": projection_path,
        "sha256": _sha(projection_raw),
    }
    with pytest.raises(evidence.ResultEvidenceError, match="ranges overlap"):
        evidence.resolve_result_evidence_batch(
            [first, second], evidence_root=tmp_path
        )


def test_member_mapping_matches_every_section_3_5_row():
    record = build_result_evidence_record()
    raw = _independent_canonical(record)
    opened = evidence.map_result_evidence_to_opened_member(
        record,
        candidate_salt="1" * 32,
        result_evidence_salt="2" * 32,
        constraint_salt="3" * 32,
        raw_bytes=raw,
    )
    sealed = evidence.map_result_evidence_to_sealed_member(record, raw_bytes=raw)

    for member in (opened, sealed):
        assert member.query_ordinal == record["ledger_member"]["query_ordinal"]
        assert member.replicate_ordinal == record["ledger_member"]["replicate_ordinal"]
        assert member.candidate_bytes == record["trigger_binding"]["candidate_wire"].encode("ascii")
        assert member.outcome == record["physical_result"]["outcome"]
        assert member.evidence_digest == ledger.EvidenceDigest(
            _LEDGER_EVIDENCE_DIGEST_GOLDEN
        )
        assert member.constraint_sha256 == record["physical_result"]["constraint_sha256"]
    assert opened.candidate_salt == "1" * 32
    assert opened.result_evidence_salt == "2" * 32
    assert opened.constraint_salt == "3" * 32
    assert "batch_id" not in {item.name for item in fields(opened)}
    assert "iteration_index" not in {item.name for item in fields(sealed)}


def test_absent_record_maps_to_tombstone_without_evidence_or_constraint():
    opened = evidence.map_absent_result_to_opened_tombstone(
        query_ordinal=9,
        replicate_ordinal=2,
        candidate_bytes=b"10100",
        candidate_salt="1" * 32,
        result_evidence_salt="2" * 32,
        constraint_salt="3" * 32,
    )
    sealed = evidence.map_absent_result_to_sealed_tombstone(
        query_ordinal=9, replicate_ordinal=2, candidate_bytes=b"10100"
    )
    for member in (opened, sealed):
        assert member.outcome == "tombstoned"
        assert member.evidence_digest is None
        assert member.constraint_sha256 is None


def test_create_only_writer_uses_deterministic_path_and_refuses_overwrite(tmp_path):
    record = build_result_evidence_record()
    path = evidence.write_result_evidence_record(
        evidence_root=tmp_path, record=record
    )
    assert path.relative_to(tmp_path) == evidence.result_evidence_relative_path(record)
    assert path.read_bytes() == _independent_canonical(record)
    with pytest.raises(evidence.ResultEvidenceError):
        evidence.write_result_evidence_record(evidence_root=tmp_path, record=record)


def test_wal_ordered_attempt_frames_preserve_order_and_physical_offsets(tmp_path):
    layout = CampaignLayout(root=os.fspath(tmp_path / "campaign")).ensure()
    wal.log(
        layout,
        "variant-a",
        STAGE_BUILD_START,
        "fixture-env",
        {"build_attempt_id": "attempt-a", "sequence": 1},
        ts=1,
    )
    wal.log(
        layout,
        "variant-b",
        STAGE_BUILD_START,
        "fixture-env",
        {"build_attempt_id": "attempt-b", "sequence": 99},
        ts=2,
    )
    wal.log(
        layout,
        "variant-a",
        STAGE_VERIFY_DONE,
        "fixture-env",
        {"build_attempt_id": "attempt-a", "sequence": 2},
        ts=3,
    )
    source = Path(layout.wal_file).read_bytes()
    frames = wal.ordered_attempt_frames(layout, "attempt-a")
    assert [frame.record.payload["sequence"] for frame in frames] == [1, 2]
    assert [frame.line_number for frame in frames] == [1, 3]
    for frame in frames:
        assert source[frame.byte_start:frame.byte_end] == frame.raw_bytes
        assert frame.raw_bytes.endswith(b"\n")


def test_formal_consumer_contract_derives_accepted_commit_terminal() -> None:
    records = [_commit_terminal()]
    derived = _derive(records=records)
    assert derived == evidence.DerivedPhysicalResult(
        build_attempt_id=_BUILD_ATTEMPT_ID,
        outcome="accepted",
        constraint_sha256=None,
        ordered_wal_sha256=_sha(_projection_bytes(records=records)),
    )


@pytest.mark.parametrize(
    "malformation",
    ["noncanonical", "different-attempt", "empty-records"],
    ids=["noncanonical", "different-attempt", "empty-records"],
)
def test_formal_consumer_contract_refuses_invalid_ordered_wal_projection(
    malformation: str,
) -> None:
    records = [_commit_terminal()]
    if malformation == "noncanonical":
        projection_raw = _projection_bytes(records=records) + b"\n"
    elif malformation == "different-attempt":
        records[0]["payload"]["build_attempt_id"] = "other-attempt"
        projection_raw = _projection_bytes(
            records=records, build_attempt_id="other-attempt"
        )
    else:
        projection_raw = _projection_bytes(records=[])
    with pytest.raises(evidence.ResultEvidenceIssuanceRefused):
        evidence.derive_physical_result(
            ordered_wal_projection_bytes=projection_raw,
            build_attempt_id=_BUILD_ATTEMPT_ID,
            ordered_verifiers=_ORDERED_VERIFIERS,
        )


@pytest.mark.parametrize(
    "shadow",
    ["reason", "verify_configs", "verify", "build_attempt_id"],
    ids=["reason", "verify-configs", "verify", "build-attempt-id"],
)
def test_formal_consumer_contract_refuses_terminal_root_shadow(
    shadow: str,
) -> None:
    terminal = _commit_terminal()
    shadow_values = {
        "reason": "non-serializable",
        "verify_configs": list(_ORDERED_VERIFIERS),
        "verify": {},
        "build_attempt_id": _BUILD_ATTEMPT_ID,
    }
    terminal[shadow] = shadow_values[shadow]
    with pytest.raises(evidence.ResultEvidenceIssuanceRefused):
        _derive(records=[terminal])


@pytest.mark.parametrize(
    "fixture_name",
    ["r9_dense_cycle4", "r3_cycle3", "r1_write_skew"],
    ids=["r9_dense_cycle4", "r3_cycle3", "r1_write_skew"],
)
def test_synthetic_silo_source_derives_rejected_single_witness_class(
    tmp_path: Path, fixture_name: str
) -> None:
    result = _verify_fixture(tmp_path, fixture_name)
    snapshot = _verify_snapshot(result)
    records = [_abort_terminal(result, snapshot=snapshot)]
    derived = _derive(records=records, result=result)
    expected = hashlib.sha256(
        evidence.canonical_json_bytes(snapshot["anomalies"][0])
    ).hexdigest()
    independent = hashlib.sha256(
        _independent_canonical(snapshot["anomalies"][0])
    ).hexdigest()
    assert derived == evidence.DerivedPhysicalResult(
        build_attempt_id=_BUILD_ATTEMPT_ID,
        outcome="rejected",
        constraint_sha256=expected,
        ordered_wal_sha256=_sha(_projection_bytes(records=records)),
    )
    assert derived.constraint_sha256 == evidence.witness_class_sha256(
        snapshot["anomalies"][0]
    )
    assert derived.constraint_sha256 == independent


@pytest.mark.parametrize(
    "fixture_name",
    ["integrity_orphan", "m2_version_dup"],
    ids=["integrity_orphan", "m2_version_dup"],
)
def test_synthetic_silo_source_refuses_indeterminate_result(
    tmp_path: Path, fixture_name: str
) -> None:
    result = _verify_fixture(tmp_path, fixture_name)
    _assert_issuance_refused(
        tmp_path / "evidence",
        records=[_abort_terminal(result)],
        result=result,
    )


def test_synthetic_silo_source_refuses_dirty_nonserializable_result(
    tmp_path: Path,
) -> None:
    result = _verify_fixture(tmp_path, "r4_mixed_cycle")
    assert result.verdict == "non-serializable"
    assert result.integrity.clean() is False
    _assert_issuance_refused(
        tmp_path / "evidence",
        records=[_abort_terminal(result)],
        result=result,
    )


def test_synthetic_silo_source_refuses_empty_capped_witness_report(
    tmp_path: Path,
) -> None:
    result = _verify_fixture(tmp_path, "r9_dense_cycle4", max_report=0)
    assert result.total_cycles == 1
    assert result.anomalies == []
    _assert_issuance_refused(
        tmp_path / "evidence",
        records=[_abort_terminal(result)],
        result=result,
    )


def test_synthetic_silo_source_refuses_multiple_witness_classes(
    tmp_path: Path,
) -> None:
    result = _verify_fixture(tmp_path, "r8_silo_broken_norw")
    assert result.total_cycles == len(result.anomalies) == 4
    _assert_issuance_refused(
        tmp_path / "evidence",
        records=[_abort_terminal(result)],
        result=result,
    )


def test_synthetic_silo_source_refuses_truncated_multiple_witness_classes(
    tmp_path: Path,
) -> None:
    result = _verify_fixture(tmp_path, "r8_silo_broken_norw", max_report=1)
    assert result.total_cycles == 4
    assert len(result.anomalies) == 1
    _assert_issuance_refused(
        tmp_path / "evidence",
        records=[_abort_terminal(result)],
        result=result,
    )


@pytest.mark.parametrize(
    "mismatch",
    ["different-run-snapshot", "wrong-reason", "wrong-verify-configs"],
    ids=["different-run-snapshot", "wrong-reason", "wrong-verify-configs"],
)
def test_formal_consumer_contract_refuses_terminal_mismatch(
    tmp_path: Path, mismatch: str
) -> None:
    result: VerifyResult | None
    if mismatch == "wrong-verify-configs":
        result = None
        records = [_commit_terminal(verify_configs=["wrong"])]
    else:
        result = _verify_fixture(tmp_path, "r9_dense_cycle4")
        terminal = _abort_terminal(result)
        if mismatch == "different-run-snapshot":
            donor = _verify_fixture(tmp_path, "r3_cycle3")
            terminal["payload"]["verify"] = _verify_snapshot(donor)
        else:
            terminal["payload"]["reason"] = "indeterminate"
        records = [terminal]
    _assert_issuance_refused(
        tmp_path / "evidence",
        records=records,
        result=result,
    )


@pytest.mark.parametrize(
    "verify_configs",
    [
        [],
        list(_ORDERED_VERIFIERS[:-1]),
        list(reversed(_ORDERED_VERIFIERS)),
        [_ORDERED_VERIFIERS[0], _ORDERED_VERIFIERS[0]],
    ],
    ids=["empty", "prefix", "reverse", "duplicate"],
)
def test_formal_consumer_contract_refuses_nonexact_accepted_verifier_order(
    tmp_path: Path, verify_configs: list[str]
) -> None:
    assert len(_ORDERED_VERIFIERS) >= 2
    _assert_issuance_refused(
        tmp_path / "evidence",
        records=[_commit_terminal(verify_configs=verify_configs)],
        result=None,
    )


@pytest.mark.parametrize(
    "malformation",
    ["stats-bool", "cycle-bool", "reason-version-float"],
    ids=["stats-bool", "cycle-bool", "reason-version-float"],
)
def test_synthetic_silo_source_refuses_nonexact_typed_values(
    tmp_path: Path, malformation: str
) -> None:
    result = copy.deepcopy(_verify_fixture(tmp_path, "r9_dense_cycle4"))
    if malformation == "stats-bool":
        result = replace(result, n_txns=True)
    elif malformation == "cycle-bool":
        result.anomalies[0].cycle[0] = True
    else:
        reason = result.anomalies[0].edges[0].reasons[0]
        assert reason.u_ver is not None
        result.anomalies[0].edges[0].reasons[0] = replace(
            reason,
            u_ver=(1.0, reason.u_ver[1]),
        )
    _assert_issuance_refused(
        tmp_path / "evidence",
        records=[_abort_terminal(result)],
        result=result,
    )


@pytest.mark.parametrize(
    "malformation",
    ["unknown-phenomenon", "ring-mismatch", "unknown-reason-type"],
    ids=["unknown-phenomenon", "ring-mismatch", "unknown-reason-type"],
)
def test_synthetic_silo_source_refuses_nonproduction_witness_shape(
    tmp_path: Path, malformation: str
) -> None:
    result = copy.deepcopy(_verify_fixture(tmp_path, "r9_dense_cycle4"))
    anomaly = result.anomalies[0]
    if malformation == "unknown-phenomenon":
        anomaly.phenomenon = "unknown"
    elif malformation == "ring-mismatch":
        anomaly.edges[0].src += 1000
    else:
        anomaly.edges[0].reasons[0] = replace(
            anomaly.edges[0].reasons[0], etype="unknown"
        )
    _assert_issuance_refused(
        tmp_path / "evidence",
        records=[_abort_terminal(result)],
        result=result,
    )


def test_synthetic_silo_source_shared_witness_digest_matches_independent_bytes(
    tmp_path: Path,
) -> None:
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    anomaly = _verify_snapshot(result)["anomalies"][0]
    assert evidence.validate_witness_anomaly(anomaly)
    assert evidence.witness_class_sha256(anomaly) == hashlib.sha256(
        _independent_canonical(anomaly)
    ).hexdigest()


def test_formal_consumer_contract_assembler_rejects_invalid_input() -> None:
    fixture_record = build_result_evidence_record()
    origin_binding = dict(fixture_record["origin_binding"])
    origin_binding.pop("cell_key")
    with pytest.raises(evidence.ResultEvidenceError):
        evidence.assemble_result_evidence_record(
            origin_binding=origin_binding,
            trial_binding=fixture_record["trial_binding"],
            ledger_member=fixture_record["ledger_member"],
            p6_plan=fixture_record["p6_plan"],
            trigger_binding=fixture_record["trigger_binding"],
            derived=evidence.DerivedPhysicalResult(
                _BUILD_ATTEMPT_ID,
                "accepted",
                None,
                fixture_record["evidence"]["ordered_wal_ref"]["sha256"],
            ),
            ordered_wal_ref=fixture_record["evidence"]["ordered_wal_ref"],
            execution_provenance_ref=fixture_record["evidence"][
                "execution_provenance_ref"
            ],
        )


def test_formal_consumer_contract_assembler_rejects_different_projection_same_attempt(
    tmp_path: Path,
) -> None:
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    donor = _verify_fixture(tmp_path, "r3_cycle3")
    records = [_abort_terminal(result)]
    donor_records = [_abort_terminal(donor)]
    projection_raw = _projection_bytes(records=records)
    donor_projection_raw = _projection_bytes(records=donor_records)
    assert projection_raw != donor_projection_raw
    derived = evidence.derive_physical_result(
        ordered_wal_projection_bytes=projection_raw,
        build_attempt_id=_BUILD_ATTEMPT_ID,
        ordered_verifiers=_ORDERED_VERIFIERS,
        verify_result=result,
    )
    fixture_record = build_result_evidence_record()
    fixture_record["evidence"]["ordered_wal_ref"] = {
        "path": "wal/projections/donor.json",
        "sha256": _sha(donor_projection_raw),
    }
    with pytest.raises(evidence.ResultEvidenceError):
        _assemble_from_fixture(fixture_record, derived)


def test_formal_consumer_contract_issuer_resolves_before_record_creation(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    fixture_record = build_result_evidence_record()
    assembled = _assemble_from_fixture(
        fixture_record,
        evidence.DerivedPhysicalResult(
            fixture_record["physical_result"]["build_attempt_id"],
            "rejected",
            fixture_record["physical_result"]["constraint_sha256"],
            fixture_record["evidence"]["ordered_wal_ref"]["sha256"],
        ),
    )
    record_path = root / evidence.result_evidence_relative_path(assembled)
    with pytest.raises(evidence.ResultEvidenceError):
        evidence.issue_result_evidence_record(evidence_root=root, record=assembled)
    assert not record_path.exists()


def test_formal_consumer_contract_issuer_writes_nine_keys_create_only(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    fixture_record = _resolution_tree(root)
    assembled = _assemble_from_fixture(
        fixture_record,
        evidence.DerivedPhysicalResult(
            fixture_record["physical_result"]["build_attempt_id"],
            "rejected",
            fixture_record["physical_result"]["constraint_sha256"],
            fixture_record["evidence"]["ordered_wal_ref"]["sha256"],
        ),
    )
    path = evidence.issue_result_evidence_record(
        evidence_root=root, record=assembled
    )
    parsed = evidence.parse_result_evidence_bytes(path.read_bytes())
    assert len(parsed) == 9
    assert parsed == assembled
    with pytest.raises(evidence.ResultEvidenceError):
        evidence.issue_result_evidence_record(evidence_root=root, record=assembled)


def _layout_rejection_fixture(tmp_path: Path, *, kind: str = "official"):
    root = tmp_path / "evidence"
    root.mkdir()
    real = _producer_layout(root, kind=kind)
    context = _producer_context(root)
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    _log_producer_attempt(
        real, build_attempt_id=_BUILD_ATTEMPT_ID, result=result, first_ts=10
    )
    return real, context, result


def _layout_subclass(real):
    class LayoutSubclass(type(real)):
        pass

    return LayoutSubclass(root=real.root)


def _duck_layout(real, kind: str):
    @dataclass(frozen=True)
    class FrozenLayout:
        root: str
        wal_file: str

    cls = FrozenLayout if kind == "frozen" else SimpleNamespace
    return cls(root=real.root, wal_file=real.wal_file)


def _non_layout_value(real, kind: str):
    return {"str": str(real.root), "path": Path(real.root), "none": None}[kind]


def _type_equality_impostor(real):
    target = type(real)

    class EqualLayoutType(type):
        def __eq__(cls, other):
            return other is target or other is cls

        __hash__ = type.__hash__

    class Impostor(metaclass=EqualLayoutType):
        root = real.root
        wal_file = real.wal_file

    impostor = Impostor()
    assert type(impostor) is not target
    assert type(impostor) in (CampaignLayout, ExplorationCampaignLayout)
    return impostor


def _assert_layout_issuance_rejected(layout, context, result) -> None:
    root = Path(context.evidence_root)
    before = _file_snapshot(root)
    with pytest.raises(
        evidence.ResultEvidenceError,
        match="^layout must be an exact CampaignLayout or ExplorationCampaignLayout$",
    ):
        _issue_producer_record(
            layout=layout,
            context=context,
            build_attempt_id=_BUILD_ATTEMPT_ID,
            verify_result=result,
            execution_receipt=_execution_receipt(),
        )
    assert _file_snapshot(root) == before
    assert not (root / context.expected_record_path).exists()


def _assert_layout_projection_rejected(layout, real, context) -> None:
    frames = wal.ordered_attempt_frames(real, _BUILD_ATTEMPT_ID)
    terminal_prefix = Path(real.wal_file).read_bytes()[:frames[-1].byte_end]
    source_ref = {
        "path": Path(real.wal_file).relative_to(context.evidence_root).as_posix(),
        "sha256": hashlib.sha256(terminal_prefix).hexdigest(),
    }
    with pytest.raises(
        evidence.ResultEvidenceError,
        match="^layout must be an exact CampaignLayout or ExplorationCampaignLayout$",
    ):
        evidence.produce_ordered_wal_projection(
            layout=layout,
            build_attempt_id=_BUILD_ATTEMPT_ID,
            source_wal_ref=source_ref,
        )


@pytest.mark.parametrize("kind", ["official", "exploration"])
def test_ordered_wal_projection_accepts_exact_layouts(
    tmp_path: Path, kind: str,
) -> None:
    real, context, _result = _layout_rejection_fixture(tmp_path, kind=kind)
    if kind == "exploration":
        assert type(real) is ExplorationCampaignLayout
    frames = wal.ordered_attempt_frames(real, _BUILD_ATTEMPT_ID)
    terminal_prefix = Path(real.wal_file).read_bytes()[:frames[-1].byte_end]
    source_ref = {
        "path": Path(real.wal_file).relative_to(context.evidence_root).as_posix(),
        "sha256": hashlib.sha256(terminal_prefix).hexdigest(),
    }
    projection = evidence.produce_ordered_wal_projection(
        layout=real, build_attempt_id=_BUILD_ATTEMPT_ID, source_wal_ref=source_ref,
    )
    assert isinstance(projection, bytes) and projection
    parsed = json.loads(projection)
    assert isinstance(parsed, dict)
    assert parsed["build_attempt_id"] == _BUILD_ATTEMPT_ID
    assert parsed["schema_version"] == "ordered-wal-projection/v1"


@pytest.mark.parametrize("kind", ["official", "exploration"])
def test_campaign_producer_refuses_layout_subclasses_before_writes(
    tmp_path: Path, kind: str,
) -> None:
    real, context, result = _layout_rejection_fixture(tmp_path, kind=kind)
    _assert_layout_issuance_rejected(_layout_subclass(real), context, result)


@pytest.mark.parametrize("kind", ["official", "exploration"])
def test_ordered_wal_projection_refuses_layout_subclasses(
    tmp_path: Path, kind: str,
) -> None:
    real, context, result = _layout_rejection_fixture(tmp_path, kind=kind)
    _assert_layout_projection_rejected(_layout_subclass(real), real, context)


@pytest.mark.parametrize("kind", ["frozen", "namespace"])
def test_campaign_producer_refuses_duck_layout_before_writes(
    tmp_path: Path, kind: str,
) -> None:
    real, context, result = _layout_rejection_fixture(tmp_path, kind="official")
    _assert_layout_issuance_rejected(_duck_layout(real, kind), context, result)


@pytest.mark.parametrize("kind", ["frozen", "namespace"])
def test_ordered_wal_projection_refuses_duck_layout(
    tmp_path: Path, kind: str,
) -> None:
    real, context, result = _layout_rejection_fixture(tmp_path, kind="official")
    _assert_layout_projection_rejected(_duck_layout(real, kind), real, context)


@pytest.mark.parametrize("kind", ["str", "path", "none"])
def test_campaign_producer_refuses_non_layout_values_before_writes(
    tmp_path: Path, kind: str,
) -> None:
    real, context, result = _layout_rejection_fixture(tmp_path, kind="official")
    _assert_layout_issuance_rejected(_non_layout_value(real, kind), context, result)


@pytest.mark.parametrize("kind", ["str", "path", "none"])
def test_ordered_wal_projection_refuses_non_layout_values(
    tmp_path: Path, kind: str,
) -> None:
    real, context, result = _layout_rejection_fixture(tmp_path, kind="official")
    _assert_layout_projection_rejected(_non_layout_value(real, kind), real, context)


@pytest.mark.parametrize("kind", ["official", "exploration"])
def test_campaign_producer_refuses_type_equality_impostor_before_writes(
    tmp_path: Path, kind: str,
) -> None:
    real, context, result = _layout_rejection_fixture(tmp_path, kind=kind)
    _assert_layout_issuance_rejected(_type_equality_impostor(real), context, result)


@pytest.mark.parametrize("kind", ["official", "exploration"])
def test_ordered_wal_projection_refuses_type_equality_impostor(
    tmp_path: Path, kind: str,
) -> None:
    real, context, result = _layout_rejection_fixture(tmp_path, kind=kind)
    _assert_layout_projection_rejected(_type_equality_impostor(real), real, context)


def test_campaign_producer_refuses_exploration_root_outside_evidence_root_before_writes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    outside = tmp_path / "outside-output"
    layout = exploration_campaign_layout(
        "fixture-physical-run", os.fspath(outside)
    ).ensure()
    context = _producer_context(root)
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    _log_producer_attempt(
        layout, build_attempt_id=_BUILD_ATTEMPT_ID, result=result, first_ts=10
    )
    before = _file_snapshot(root)
    outside_before = _file_snapshot(outside)
    with pytest.raises(
        evidence.ResultEvidenceError,
        match="^physical campaign root is outside the result evidence root$",
    ):
        _issue_producer_record(
            layout=layout,
            context=context,
            build_attempt_id=_BUILD_ATTEMPT_ID,
            verify_result=result,
            execution_receipt=_execution_receipt(),
        )
    assert _file_snapshot(root) == before
    assert _file_snapshot(outside) == outside_before
    assert not (root / context.expected_record_path).exists()


@pytest.mark.parametrize("kind", ["official", "exploration"])
def test_campaign_producer_issues_real_wal_projection_and_resolves_interval(
    tmp_path: Path, kind: str,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    layout = _producer_layout(root, kind=kind)
    if kind == "exploration":
        assert type(layout) is ExplorationCampaignLayout
        assert Path(layout.namespace_file).is_file()
    context = _producer_context(root)
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    attempt = "producer-attempt-one"
    _log_producer_attempt(
        layout, build_attempt_id=attempt, result=result, first_ts=10
    )
    frames = wal.ordered_attempt_frames(layout, attempt)
    terminal_prefix = Path(layout.wal_file).read_bytes()[:frames[-1].byte_end]

    record_path = _issue_producer_record(
        layout=layout,
        context=context,
        build_attempt_id=attempt,
        verify_result=result,
        execution_receipt=_execution_receipt(),
    )
    record = evidence.parse_result_evidence_bytes(record_path.read_bytes())
    resolved = evidence.resolve_result_evidence(record, evidence_root=root)

    assert record_path.relative_to(root).as_posix() == context.expected_record_path
    assert resolved.ordered_wal.byte_start == frames[0].byte_start == 0
    assert resolved.ordered_wal.byte_end == frames[-1].byte_end
    assert (
        resolved.ordered_wal.source_wal_ref.raw_bytes[
            resolved.ordered_wal.byte_start:resolved.ordered_wal.byte_end
        ]
        == b"".join(frame.raw_bytes for frame in frames)
    )
    assert resolved.ordered_wal.source_wal_ref.raw_bytes == terminal_prefix
    assert [item["stage"] for item in resolved.ordered_wal.records] == [
        trigger_gate_binding.WAL_RECORD_STAGE,
        STAGE_BUILD_START,
        STAGE_BUILD_DONE,
        STAGE_VERIFY_DONE,
        STAGE_ABORT,
    ]
    assert set(resolved.execution_provenance) == {
        "schema_version",
        "build_attempt_id",
        "campaign_id",
        "workload",
        "contract_sha256",
        "trigger_binding",
        "execution_receipt_sha256",
        "campaign_run_identity",
    }
    content_prefix = Path("reports/reflux-result-evidence-content/v1")
    physical_root = Path(layout.root)
    assert resolved.ordered_wal.projection_ref.normalized_path.relative_to(
        physical_root
    ).parent == content_prefix / "ordered-wal"
    assert resolved.ordered_wal.source_wal_ref.normalized_path.relative_to(
        physical_root
    ).parent == content_prefix / "source-wal"
    assert resolved.execution_provenance_ref.normalized_path.relative_to(
        physical_root
    ).parent == content_prefix / "execution-provenance"


def test_campaign_producer_preserves_nonzero_offset_for_second_attempt(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    layout = _producer_layout(root)
    context = _producer_context(root)
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    _log_producer_attempt(
        layout,
        build_attempt_id="producer-attempt-previous",
        result=result,
        first_ts=10,
    )
    attempt = "producer-attempt-second"
    _log_producer_attempt(
        layout, build_attempt_id=attempt, result=result, first_ts=20
    )
    frames = wal.ordered_attempt_frames(layout, attempt)
    assert frames[0].byte_start > 0

    record_path = _issue_producer_record(
        layout=layout,
        context=context,
        build_attempt_id=attempt,
        verify_result=result,
        execution_receipt=_execution_receipt(),
    )
    record = evidence.parse_result_evidence_bytes(record_path.read_bytes())
    resolved = evidence.resolve_result_evidence(record, evidence_root=root)
    assert resolved.ordered_wal.byte_start == frames[0].byte_start > 0
    assert resolved.ordered_wal.byte_end == frames[-1].byte_end
    assert (
        resolved.ordered_wal.source_wal_ref.raw_bytes[
            frames[0].byte_start:frames[-1].byte_end
        ]
        == b"".join(frame.raw_bytes for frame in frames)
    )


def test_campaign_producer_refuses_absent_execution_receipt_before_writes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    layout = _producer_layout(root)
    context = _producer_context(root)
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    attempt = "producer-attempt-no-receipt"
    _log_producer_attempt(
        layout, build_attempt_id=attempt, result=result, first_ts=10
    )
    before = _file_snapshot(root)

    with pytest.raises(evidence.ResultEvidenceIssuanceRefused):
        _issue_producer_record(
            layout=layout,
            context=context,
            build_attempt_id=attempt,
            verify_result=result,
            execution_receipt=None,
        )
    assert _file_snapshot(root) == before


def test_campaign_producer_refuses_required_contract_v1_receipt_before_writes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    layout = _producer_layout(root)
    contract, verified, _valid_v2_receipt = _required_execution_inputs()
    context = _producer_context(
        root,
        contract=contract,
        verified_calibration=verified,
    )
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    attempt = "producer-attempt-required-v1-receipt"
    _log_producer_attempt(
        layout, build_attempt_id=attempt, result=result, first_ts=10
    )
    before = _file_snapshot(root)

    with pytest.raises(
        evidence.ResultEvidenceIssuanceRefused,
        match="execution receipt is absent or does not match",
    ):
        _issue_producer_record(
            layout=layout,
            context=context,
            build_attempt_id=attempt,
            verify_result=result,
            execution_receipt=execution_guard.build_receipt(contract),
            environment_contract=contract,
        )
    assert _file_snapshot(root) == before


def test_campaign_producer_refuses_contract_not_bound_by_capability_before_writes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    layout = _producer_layout(root)
    contract = env_contract.authorize("linux-baremetal").contract
    context = _producer_context(root, contract=contract)
    mismatched_contract = replace(
        contract, clocks_per_us=contract.clocks_per_us + 1
    )
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    attempt = "producer-attempt-contract-mismatch"
    _log_producer_attempt(
        layout, build_attempt_id=attempt, result=result, first_ts=10
    )
    before = _file_snapshot(root)

    with pytest.raises(
        evidence.ResultEvidenceIssuanceRefused,
        match="environment contract differs from the origin capability",
    ):
        _issue_producer_record(
            layout=layout,
            context=context,
            build_attempt_id=attempt,
            verify_result=result,
            execution_receipt=execution_guard.build_receipt(
                mismatched_contract
            ),
            environment_contract=mismatched_contract,
        )
    assert _file_snapshot(root) == before


def test_campaign_producer_refuses_required_contract_without_verified_calibration(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    layout = _producer_layout(root)
    contract, _verified, valid_v2_receipt = _required_execution_inputs()
    context = _producer_context(root, contract=contract)
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    attempt = "producer-attempt-required-without-calibration"
    _log_producer_attempt(
        layout, build_attempt_id=attempt, result=result, first_ts=10
    )
    before = _file_snapshot(root)

    with pytest.raises(
        evidence.ResultEvidenceIssuanceRefused,
        match="required environment contract lacks verified calibration",
    ):
        _issue_producer_record(
            layout=layout,
            context=context,
            build_attempt_id=attempt,
            verify_result=result,
            execution_receipt=valid_v2_receipt,
            environment_contract=contract,
        )
    assert _file_snapshot(root) == before


@pytest.mark.parametrize(
    "mismatch",
    ("schema", "env_tag", "attestation_mode"),
)
def test_campaign_producer_refuses_unauthenticated_receipt_before_writes(
    tmp_path: Path,
    mismatch: str,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    layout = _producer_layout(root)
    context = _producer_context(root)
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    attempt = f"producer-attempt-invalid-receipt-{mismatch}"
    _log_producer_attempt(
        layout, build_attempt_id=attempt, result=result, first_ts=10
    )
    receipt = _execution_receipt()
    checked_context = context
    if mismatch == "schema":
        receipt["schema"] = "fixture-execution-receipt/v1"
    elif mismatch == "env_tag":
        receipt["env_tag"] = "different-env"
    else:
        checked_context = replace(context, attestation_mode="required")
    before = _file_snapshot(root)

    with pytest.raises(evidence.ResultEvidenceIssuanceRefused):
        _issue_producer_record(
            layout=layout,
            context=checked_context,
            build_attempt_id=attempt,
            verify_result=result,
            execution_receipt=receipt,
        )
    assert _file_snapshot(root) == before


def test_campaign_producer_refuses_interleaved_attempt_before_writes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    layout = _producer_layout(root)
    context = _producer_context(root)
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    attempt = "producer-attempt-interleaved"
    binding = _producer_binding()
    wal.log(
        layout,
        "fixture-v",
        trigger_gate_binding.WAL_RECORD_STAGE,
        "fixture-env",
        {
            "build_attempt_id": attempt,
            wal.TRIGGER_BINDING_PAYLOAD_KEY: trigger_gate_binding.to_record(binding),
        },
        ts=10,
    )
    wal.log(
        layout,
        "fixture-v",
        STAGE_BUILD_START,
        "fixture-env",
        {"build_attempt_id": attempt},
        ts=11,
    )
    wal.log(
        layout,
        "other-v",
        STAGE_BUILD_START,
        "fixture-env",
        {"build_attempt_id": "producer-attempt-other"},
        ts=12,
    )
    for timestamp, stage in (
        (13, STAGE_BUILD_DONE),
        (14, STAGE_VERIFY_DONE),
    ):
        wal.log(
            layout,
            "fixture-v",
            stage,
            "fixture-env",
            {"build_attempt_id": attempt},
            ts=timestamp,
        )
    terminal = _abort_terminal(result)
    terminal["payload"]["build_attempt_id"] = attempt
    wal.log(
        layout,
        terminal["variant"],
        terminal["stage"],
        terminal["env_tag"],
        terminal["payload"],
        ts=15,
    )
    before = _file_snapshot(root)

    with pytest.raises(evidence.ResultEvidenceIssuanceRefused):
        _issue_producer_record(
            layout=layout,
            context=context,
            build_attempt_id=attempt,
            verify_result=result,
            execution_receipt=_execution_receipt(),
        )
    assert _file_snapshot(root) == before


def test_campaign_producer_refuses_nonexact_verify_result_before_writes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    layout = _producer_layout(root)
    context = _producer_context(root)
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    attempt = "producer-attempt-untyped"
    _log_producer_attempt(
        layout, build_attempt_id=attempt, result=result, first_ts=10
    )
    before = _file_snapshot(root)

    with pytest.raises(evidence.ResultEvidenceIssuanceRefused):
        _issue_producer_record(
            layout=layout,
            context=context,
            build_attempt_id=attempt,
            verify_result=_verify_snapshot(result),
            execution_receipt=_execution_receipt(),
        )
    assert _file_snapshot(root) == before


def test_campaign_producer_refuses_wrong_expected_record_path_before_writes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    layout = _producer_layout(root)
    context = _producer_context(root)
    wrong_context = replace(
        context,
        expected_record_path="reports/reflux-result-evidence/v1/wrong.json",
    )
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    attempt = "producer-attempt-wrong-record-path"
    _log_producer_attempt(
        layout, build_attempt_id=attempt, result=result, first_ts=10
    )
    before = _file_snapshot(root)

    with pytest.raises(
        evidence.ResultEvidenceError,
        match="record path differs from the issuance context",
    ):
        _issue_producer_record(
            layout=layout,
            context=wrong_context,
            build_attempt_id=attempt,
            verify_result=result,
            execution_receipt=_execution_receipt(),
        )
    assert _file_snapshot(root) == before


def test_campaign_producer_treats_create_only_collision_as_failure(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    layout = _producer_layout(root)
    context = _producer_context(root)
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    attempt = "producer-attempt-collision"
    _log_producer_attempt(
        layout, build_attempt_id=attempt, result=result, first_ts=10
    )
    receipt = _execution_receipt()
    _issue_producer_record(
        layout=layout,
        context=context,
        build_attempt_id=attempt,
        verify_result=result,
        execution_receipt=receipt,
    )

    with pytest.raises(evidence.ResultEvidenceError) as caught:
        _issue_producer_record(
            layout=layout,
            context=context,
            build_attempt_id=attempt,
            verify_result=result,
            execution_receipt=receipt,
        )
    causes = []
    current = caught.value
    while current is not None:
        causes.append(current)
        current = current.__cause__
    assert any(type(item) is FileExistsError for item in causes)


def test_campaign_producer_snapshot_survives_append_while_live_ref_breaks(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    layout = _producer_layout(root)
    context = _producer_context(root)
    result = _verify_fixture(tmp_path, "r9_dense_cycle4")
    attempt = "producer-attempt-before-append"
    _log_producer_attempt(
        layout, build_attempt_id=attempt, result=result, first_ts=10
    )
    wal_before_append = Path(layout.wal_file).read_bytes()
    record_path = _issue_producer_record(
        layout=layout,
        context=context,
        build_attempt_id=attempt,
        verify_result=result,
        execution_receipt=_execution_receipt(),
    )
    record = evidence.parse_result_evidence_bytes(record_path.read_bytes())

    wal.log(
        layout,
        "later-v",
        STAGE_BUILD_START,
        "fixture-env",
        {"build_attempt_id": "producer-attempt-later"},
        ts=100,
    )
    live_wal_ref = {
        "path": Path(layout.wal_file).relative_to(root).as_posix(),
        "sha256": _sha(wal_before_append),
    }
    with pytest.raises(evidence.ResultEvidenceError):
        evidence.resolve_content_addressed_ref(
            evidence_root=root, reference=live_wal_ref
        )

    resolved = evidence.resolve_result_evidence(record, evidence_root=root)
    assert resolved.ordered_wal.source_wal_ref.raw_bytes == wal_before_append
    assert resolved.ordered_wal.source_wal_ref.normalized_path != Path(
        layout.wal_file
    )
