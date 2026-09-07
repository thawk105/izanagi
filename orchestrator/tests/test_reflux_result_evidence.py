from __future__ import annotations

import copy
import hashlib
import json
import os
from dataclasses import fields
from pathlib import Path

import pytest

from orchestrator.campaign import reflux_origin_ledger as ledger
from orchestrator.campaign import reflux_result_evidence as evidence
from orchestrator.campaign import wal
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.campaign.model import STAGE_BUILD_START, STAGE_VERIFY_DONE
from orchestrator.tests.reflux_origin_fixture_builder import (
    build_execution_provenance,
    build_ordered_wal_projection,
    build_result_evidence_record,
)


_RECORD_RAW_GOLDEN = "5c0ac03d7ccd53153f70c2e10dde301aa4097eeee61f9118eeefc49b3ad24767"
_LEDGER_EVIDENCE_DIGEST_GOLDEN = "5c0ac03d7ccd53153f70c2e10dde301aa4097eeee61f9118eeefc49b3ad24767"
_OUTER_SALTED_COMMITMENT_GOLDEN = "b9e20f457bec0bb2ed7e866c7bd175cee9fba8779a96fe2085fd7f79d5cb6365"
_WRONG_DOMAIN_PREFIXED_RAW_GOLDEN = "610867ca65d585909812e468368f931a76fdf0a7faca488a0a294554ed97735f"
_SALT = "0123456789abcdef0123456789abcdef"


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
