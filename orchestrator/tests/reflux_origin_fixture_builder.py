"""Frozen fixtures for the reflux origin wiring tests.

The values in this module are deliberately synthetic.  In particular, no
working-tree bytes, clock, absolute path, or production canonicalizer is used
to derive an expected outer-artifact digest.  The trigger binding commitment
is derived through the production binding contract so the raw WAL binding and
ledger projection describe the same value.  A ``__`` in an override name
descends into a nested mapping or sequence, so every exact-schema leaf can be
changed by a consumer test without changing this shared fixture.  The value
``...`` removes the selected key or sequence element for an exact-key
missing-field negative.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from orchestrator.campaign import trigger_gate_binding
from orchestrator.campaign.model import STAGE_ABORT


__all__ = [
    "build_fixture_repository",
    "build_authority_manifest",
    "build_source_closure_record",
    "build_result_evidence_record",
    "build_ordered_wal_projection",
    "build_execution_provenance",
    "build_recovery_envelope_inputs",
    "build_launch_admission_inputs",
    "write_evidence_tree",
    "baseline",
]


_BASELINE_PATH = Path(__file__).with_name("reflux_origin_fixture_baseline.json")
_SOURCE_MASK = 7
_BATCH_ID = "fixture-batch-0000"
_CAMPAIGN_ID = "fixture-campaign-0000"
_TRIAL_WORKLOAD = "ycsb-a"
_CONSTRAINT_SHA256 = hashlib.sha256(
    b"fixture:single-candidate-attributable-witness-class"
).hexdigest()
_FIXTURE_TRIGGER_NONCE = "a" * 64


@dataclass(frozen=True, slots=True)
class FixtureRepository:
    """Paths written by :func:`build_fixture_repository`."""

    root: Path
    authority_manifest_path: Path
    source_closure_path: Path
    recovery_envelope_path: Path
    launch_admission_inputs_path: Path
    evidence_root: Path
    result_evidence_paths: tuple[Path, ...]


def _canonical_bytes(value: object) -> bytes:
    """Independent canonical JSON: UTF-8, sorted, compact, and no final LF."""

    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256(value: object) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def _label_sha256(label: str) -> str:
    return _sha256_bytes(("fixture:" + label).encode("utf-8"))


def _wire(mask: int) -> str:
    if type(mask) is not int or not 0 <= mask < 32:
        raise ValueError("mask must be an integer in [0, 31]")
    return "".join("1" if mask & (1 << bit) else "0" for bit in range(5))


def _replace_path(root: object, path: Sequence[str], value: object) -> None:
    target = root
    for component in path[:-1]:
        if isinstance(target, dict):
            if component not in target:
                raise KeyError("unknown override path component: " + component)
            target = target[component]
        elif isinstance(target, list):
            try:
                target = target[int(component)]
            except (ValueError, IndexError) as exc:
                raise KeyError("invalid sequence override component: " + component) from exc
        else:
            raise KeyError("override path descends through a scalar: " + component)

    final = path[-1]
    if isinstance(target, dict):
        if value is Ellipsis:
            if final not in target:
                raise KeyError("cannot remove unknown override key: " + final)
            del target[final]
        else:
            target[final] = copy.deepcopy(value)
    elif isinstance(target, list):
        try:
            index = int(final)
            if value is Ellipsis:
                del target[index]
            else:
                target[index] = copy.deepcopy(value)
        except (ValueError, IndexError) as exc:
            raise KeyError("invalid sequence override component: " + final) from exc
    else:
        raise KeyError("override path ends in a scalar: " + final)


def _apply_overrides(base: dict, overrides: Mapping[str, object]) -> dict:
    result = copy.deepcopy(base)
    for name, value in overrides.items():
        if type(name) is not str or not name:
            raise TypeError("override names must be non-empty strings")
        _replace_path(result, name.split("__"), value)
    return result


def _descriptor() -> dict:
    return {
        "schema_version": "izanagi-workload-descriptor/v1",
        "records": 100003,
        "threads": 7,
        "workload": _TRIAL_WORKLOAD,
        "ycsb_rratio": 50,
    }


def _axis_semantics() -> dict:
    return {
        "schema_version": "izanagi-axis-semantics/v1",
        "marker": "trigger-gating",
        "reasons": [
            "lock-conflict",
            "update-absent",
            "readvali-tid",
            "readvali-locked",
            "node-vali",
        ],
        "wire": {"width": 5, "bit_order": "lsb-first", "masks": [0, 31]},
        "sentinel": "kUnset",
    }


def _verifier_policy() -> dict:
    return {
        "schema_version": "izanagi-verifier-policy/v1",
        "ordered_passes": ["legacy", "s2"],
        "accepted": "all-passes-complete",
        "candidate_attributable_rejected": "single-normalized-witness-class",
        "fail_closed": True,
        "witness_class_cardinality": 1,
    }


def _environment_contract() -> dict:
    return {
        "schema_version": "izanagi-execution-environment-contract/v1",
        "env_tag": "fixture-local-no-measurement",
        "attestation_mode": "fixture",
    }


def _artifact_bytes() -> dict[str, bytes]:
    return {
        "workload-descriptor.json": _canonical_bytes(_descriptor()),
        "axis-semantics.json": _canonical_bytes(_axis_semantics()),
        "verifier-policy.json": _canonical_bytes(_verifier_policy()),
        "environment-contract.json": _canonical_bytes(_environment_contract()),
    }


def build_authority_manifest(**overrides) -> dict:
    artifacts = _artifact_bytes()
    base = {
        "authority_series_id": "fixture-series-v1",
        "spec_content_sha256": _label_sha256("ratified-spec-content"),
        "ccbench_commit_oid": "2" * 40,
        "axis_semantics_sha256": _sha256_bytes(artifacts["axis-semantics.json"]),
        "workload": {
            "descriptor_sha256": _sha256_bytes(artifacts["workload-descriptor.json"]),
            "records": 100003,
            "threads": 7,
        },
        "verifier_policy_sha256": _sha256_bytes(artifacts["verifier-policy.json"]),
        "environment_contract_sha256": _sha256_bytes(
            artifacts["environment-contract.json"]
        ),
        "candidate_ir": {
            "schema_ref": "izanagi-trigger-gate-ir/v1",
            "canonical_emitter_sha256": _label_sha256("canonical-emitter"),
        },
        "role_bundle_sha256": _label_sha256("role-bundle"),
        "recipient_projection_schema_sha256": _label_sha256(
            "recipient-projection-schema"
        ),
        "budget_policy": {
            "imax": 4,
            "qmax": 68,
            "kmax": 1,
            "batch_member_row_count_min": 2,
            "batch_distinct_candidate_count_min": 1,
            "query_floor_constraints": [
                {
                    "formula_id": "q-lower-bound/base+perRound*R+Emin/v1",
                    "base_queries": 1,
                    "queries_per_round": 32,
                    "rounds": 1,
                    "evidence_min": 0,
                }
            ],
        },
        "stock_certification_ref": {
            "path": "evidence/stock-certification.json",
            "sha256": _label_sha256("stock-certification"),
        },
        "structural_zero_evidence_ref": {
            "path": "evidence/structural-zero.json",
            "sha256": _label_sha256("structural-zero"),
        },
    }
    return _apply_overrides(base, overrides)


def _origin_id(manifest: Mapping) -> str:
    return _sha256_bytes(
        b"izanagi-reflux-origin-manifest/v2\0" + _canonical_bytes(manifest)
    )


def _cell_key(manifest: Mapping) -> str:
    preimage = [
        manifest["workload"]["descriptor_sha256"],
        manifest["axis_semantics_sha256"],
        manifest["verifier_policy_sha256"],
        manifest["environment_contract_sha256"],
    ]
    return _sha256_bytes(
        b"izanagi-reflux-origin-cell/v1\0" + _canonical_bytes(preimage)
    )


def _authority_document(manifest: Mapping) -> dict:
    return {
        "authority_schema": "izanagi-reflux-origin-authority/v2",
        "origins": [
            {
                "cell_key": _cell_key(manifest),
                "manifest": copy.deepcopy(dict(manifest)),
                "origin_id": _origin_id(manifest),
            }
        ],
    }


def _authority_bytes(manifest: Mapping) -> bytes:
    # The existing authority-v2 file format is line-terminated; record formats are not.
    return _canonical_bytes(_authority_document(manifest)) + b"\n"


def build_source_closure_record(**overrides) -> dict:
    manifest = build_authority_manifest()
    referent_specs = {
        "authority.workload.descriptor_sha256": {
            "path": "artifacts/workload-descriptor.json",
            "sha256": manifest["workload"]["descriptor_sha256"],
            "digest_rule": "raw-git-blob-sha256",
            "producer_field": "authority.workload.descriptor_sha256",
            "runtime_field_paths": [
                "report.cells[*].descriptor",
                "report.cells[*].descriptor_binding.output_sha256",
            ],
        },
        "axis_semantics_sha256": {
            "path": "artifacts/axis-semantics.json",
            "sha256": manifest["axis_semantics_sha256"],
            "digest_rule": "raw-git-blob-sha256",
            "producer_field": "axis_semantics_sha256",
            "runtime_field_paths": [
                "wal.TriggerGateBinding.mask",
                "wal.TriggerGateBinding.predicate_sha256",
                "wal.TriggerGateBinding.source",
            ],
        },
        "verifier_policy_sha256": {
            "path": "artifacts/verifier-policy.json",
            "sha256": manifest["verifier_policy_sha256"],
            "digest_rule": "raw-git-blob-sha256",
            "producer_field": "verifier_policy_sha256",
            "runtime_field_paths": [
                "wal.commit.payload.verify_configs",
                "wal.abort.payload.witnesses",
            ],
        },
        "environment_contract_sha256": {
            "path": "artifacts/environment-contract.json",
            "sha256": manifest["environment_contract_sha256"],
            "digest_rule": "raw-git-blob-sha256",
            "producer_field": "environment_contract_sha256",
            "runtime_field_paths": ["execution_provenance.contract_sha256"],
        },
    }
    referents = {
        name: {
            "preimage_ref": {"path": spec["path"], "sha256": spec["sha256"]},
            "digest_rule": spec["digest_rule"],
            "producer_field": spec["producer_field"],
            "runtime_field_paths": spec["runtime_field_paths"],
        }
        for name, spec in referent_specs.items()
    }
    base = {
        "schema_version": "source-closure/v1",
        "captured_commit_oid": "c" * 40,
        "authority_series_id": manifest["authority_series_id"],
        "origin_id": _origin_id(manifest),
        "cell_key": _cell_key(manifest),
        "referents": referents,
    }
    return _apply_overrides(base, overrides)


def _fixture_trigger_gate_binding(
    mask: int,
) -> trigger_gate_binding.TriggerGateBinding:
    return trigger_gate_binding.TriggerGateBinding(
        mask=mask,
        predicate_sha256=trigger_gate_binding.expected_predicate_sha256(mask),
        nonce=_FIXTURE_TRIGGER_NONCE,
        source=None,
    )


def _trigger_binding(mask: int) -> dict:
    binding = _fixture_trigger_gate_binding(mask)
    return {
        "mask": mask,
        "candidate_wire": _wire(mask),
        "trigger_gate_binding_commitment": trigger_gate_binding.commitment(binding),
    }


def _wal_records(build_attempt_id: str, mask: int) -> list[dict]:
    binding = _fixture_trigger_gate_binding(mask)
    return [
        {
            "variant": "fixture-v",
            "stage": trigger_gate_binding.WAL_RECORD_STAGE,
            "env_tag": "fixture-env",
            "ts": 0,
            "payload": {
                "build_attempt_id": build_attempt_id,
                "trigger_gate_binding": trigger_gate_binding.to_record(binding),
            },
        },
        {
            "variant": "fixture-v",
            "stage": STAGE_ABORT,
            "env_tag": "fixture-env",
            "ts": 0,
            "payload": {
                "build_attempt_id": build_attempt_id,
                "candidate_attributable": True,
                "truncated": False,
                "witness_class_sha256s": [_CONSTRAINT_SHA256],
            },
        },
    ]


def build_ordered_wal_projection(**overrides) -> dict:
    build_attempt_id = "fixture-build-attempt-0000"
    records = _wal_records(build_attempt_id, _SOURCE_MASK)
    source_bytes = _canonical_bytes(records)
    base = {
        "schema_version": "ordered-wal-projection/v1",
        "source_wal_ref": {
            "path": "wal/source/0000.json",
            "sha256": _sha256_bytes(source_bytes),
        },
        "byte_start": 0,
        "byte_end": len(source_bytes),
        "build_attempt_id": build_attempt_id,
        "records": records,
    }
    return _apply_overrides(base, overrides)


def build_execution_provenance(**overrides) -> dict:
    manifest = build_authority_manifest()
    base = {
        "schema_version": "execution-provenance/v2",
        "build_attempt_id": "fixture-build-attempt-0000",
        "campaign_id": _CAMPAIGN_ID,
        "campaign_run_identity": "fixture-run-00000000",
        "workload": _TRIAL_WORKLOAD,
        "contract_sha256": manifest["environment_contract_sha256"],
        "trigger_binding": _trigger_binding(_SOURCE_MASK),
        "execution_receipt_sha256": _label_sha256("execution-receipt-0000"),
    }
    return _apply_overrides(base, overrides)


def build_result_evidence_record(**overrides) -> dict:
    manifest = build_authority_manifest()
    closure = build_source_closure_record()
    authority_sha256 = _sha256_bytes(_authority_bytes(manifest))
    wal = build_ordered_wal_projection()
    provenance = build_execution_provenance()
    base = {
        "schema_version": "result-evidence/v1",
        "issuer": {"kind": "trusted-physical-harness"},
        "origin_binding": {
            "authority_blob_sha256": authority_sha256,
            "source_closure_sha256": _sha256(closure),
            "origin_id": closure["origin_id"],
            "cell_key": closure["cell_key"],
            "workload": _TRIAL_WORKLOAD,
            "axis_semantics_sha256": manifest["axis_semantics_sha256"],
            "verifier_policy_sha256": manifest["verifier_policy_sha256"],
            "environment_contract_sha256": manifest[
                "environment_contract_sha256"
            ],
        },
        "trial_binding": {
            "launch_admission_record_sha256": _label_sha256(
                "launch-admission-record"
            ),
            "campaign_id": _CAMPAIGN_ID,
            "workload": _TRIAL_WORKLOAD,
        },
        "ledger_member": {
            "batch_id": _BATCH_ID,
            "iteration_index": 0,
            "query_ordinal": 0,
            "replicate_ordinal": 0,
        },
        "p6_plan": {
            "purpose": "source",
            "hypothesis_sha256": _label_sha256("source-hypothesis"),
            "validation_plan_sha256": _label_sha256("validation-plan"),
        },
        "trigger_binding": _trigger_binding(_SOURCE_MASK),
        "physical_result": {
            "build_attempt_id": wal["build_attempt_id"],
            "outcome": "rejected",
            "constraint_sha256": _CONSTRAINT_SHA256,
        },
        "evidence": {
            "ordered_wal_ref": {
                "path": "wal/projections/0000.json",
                "sha256": _sha256(wal),
            },
            "execution_provenance_ref": {
                "path": "provenance/0000.json",
                "sha256": _sha256(provenance),
            },
        },
    }
    return _apply_overrides(base, overrides)


def _member(query_ordinal: int, mask: int, replicate_ordinal: int) -> dict:
    purpose = "source" if query_ordinal == 0 else "p6-validation"
    return {
        "iteration_index": 0,
        "query_ordinal": query_ordinal,
        "replicate_ordinal": replicate_ordinal,
        "purpose": purpose,
        "candidate_wire": _wire(mask),
        "candidate_salt": _label_sha256(f"candidate-salt:{query_ordinal}")[:32],
        "result_evidence_salt": _label_sha256(
            f"result-evidence-salt:{query_ordinal}"
        )[:32],
        "constraint_salt": _label_sha256(f"constraint-salt:{query_ordinal}")[:32],
        "evidence_path": (
            "reports/reflux-result-evidence/"
            f"{build_source_closure_record()['origin_id']}/{_BATCH_ID}/"
            f"{query_ordinal}.json"
        ),
    }


def build_recovery_envelope_inputs(**overrides) -> dict:
    capability = build_launch_admission_inputs()
    closure = build_source_closure_record()
    members = [_member(0, _SOURCE_MASK, 0)]
    members.extend(
        _member(1 + mask, mask, 1 if mask == _SOURCE_MASK else 0)
        for mask in range(32)
    )
    base = {
        "schema_version": "reflux-recovery-envelope/v1",
        "origin_binding_capability_sha256": _sha256(capability),
        "source_closure_sha256": _sha256(closure),
        "hypothesis_sha256": _label_sha256("source-hypothesis"),
        "validation_plan_sha256": _label_sha256("validation-plan"),
        "reserve_attempts": [
            {
                "attempt": 0,
                "batch_id": _BATCH_ID,
                "iteration_index": 0,
                "query_ordinal_start": 0,
                "operation_id": "fixture-reserve-0000",
            },
            {
                "attempt": 1,
                "batch_id": "fixture-batch-0001",
                "iteration_index": 1,
                "query_ordinal_start": 33,
                "operation_id": "fixture-reserve-0001",
            },
        ],
        "event_operation_ids": {
            "reserve_attempt_0": "fixture-reserve-0000",
            "abandon_attempt_0": "fixture-abandon-0000",
            "reserve_attempt_1": "fixture-reserve-0001",
            "batch_commit": "fixture-batch-commit-0001",
            "results_prepare": "fixture-results-prepare-0001",
            "results_open": "fixture-results-open-0001",
            "origin_terminal": "fixture-origin-terminal-0001",
        },
        "members": members,
        "expected_state_commitment": _label_sha256("initial-state-commitment"),
    }
    return _apply_overrides(base, overrides)


def build_launch_admission_inputs(**overrides) -> dict:
    manifest = build_authority_manifest()
    closure = build_source_closure_record()
    base = {
        "authority_blob_sha256": _sha256_bytes(_authority_bytes(manifest)),
        "source_closure_sha256": _sha256(closure),
        "origin_id": closure["origin_id"],
        "cell_key": closure["cell_key"],
        "authority_workload": {
            "descriptor_sha256": manifest["workload"]["descriptor_sha256"],
            "records": manifest["workload"]["records"],
            "threads": manifest["workload"]["threads"],
        },
        "axis_semantics_sha256": manifest["axis_semantics_sha256"],
        "verifier_policy_sha256": manifest["verifier_policy_sha256"],
        "environment_contract_sha256": manifest["environment_contract_sha256"],
        "campaign_id": _CAMPAIGN_ID,
        "trial_workload": _TRIAL_WORKLOAD,
        "measurement_head": "d" * 40,
        "store_scope": "fixture",
        "issuer_seal": "fixture-launch-admission-issuer-seal",
    }
    return _apply_overrides(base, overrides)


def _write_create_only(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)


def _path_token(value: object, *, label: str) -> str:
    if (
        type(value) is not str
        or not value
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
    ):
        raise ValueError(f"{label} is not a safe path token")
    return value


def write_evidence_tree(root: Path, records: Sequence[Mapping]) -> Path:
    evidence_root = Path(root)
    for record in records:
        origin = _path_token(record["origin_binding"]["origin_id"], label="origin_id")
        batch = _path_token(record["ledger_member"]["batch_id"], label="batch_id")
        query = record["ledger_member"]["query_ordinal"]
        if type(query) is not int or query < 0:
            raise ValueError("query_ordinal must be a non-negative integer")
        path = (
            evidence_root
            / "reports"
            / "reflux-result-evidence"
            / origin
            / batch
            / f"{query}.json"
        )
        _write_create_only(path, _canonical_bytes(record))
    return evidence_root


def _record_for_query(root: Path, query_ordinal: int, mask: int) -> dict:
    attempt = f"fixture-build-attempt-{query_ordinal:04d}"
    wal_records = _wal_records(attempt, mask)
    source_raw = _canonical_bytes(wal_records)
    source_rel = f"wal/source/{query_ordinal:04d}.json"
    projection_rel = f"wal/projections/{query_ordinal:04d}.json"
    provenance_rel = f"provenance/{query_ordinal:04d}.json"
    _write_create_only(root / source_rel, source_raw)
    projection = build_ordered_wal_projection(
        source_wal_ref={"path": source_rel, "sha256": _sha256_bytes(source_raw)},
        byte_end=len(source_raw),
        build_attempt_id=attempt,
        records=wal_records,
    )
    provenance = build_execution_provenance(
        build_attempt_id=attempt,
        campaign_run_identity=f"fixture-run-{query_ordinal:08x}",
        trigger_binding=_trigger_binding(mask),
        execution_receipt_sha256=_label_sha256(
            f"execution-receipt-{query_ordinal:04d}"
        ),
    )
    _write_create_only(root / projection_rel, _canonical_bytes(projection))
    _write_create_only(root / provenance_rel, _canonical_bytes(provenance))
    return build_result_evidence_record(
        ledger_member={
            "batch_id": _BATCH_ID,
            "iteration_index": 0,
            "query_ordinal": query_ordinal,
            "replicate_ordinal": (
                0 if query_ordinal == 0 else (1 if mask == _SOURCE_MASK else 0)
            ),
        },
        p6_plan={
            "purpose": "source" if query_ordinal == 0 else "p6-validation",
            "hypothesis_sha256": _label_sha256("source-hypothesis"),
            "validation_plan_sha256": _label_sha256("validation-plan"),
        },
        trigger_binding=_trigger_binding(mask),
        physical_result={
            "build_attempt_id": attempt,
            "outcome": "rejected",
            "constraint_sha256": _CONSTRAINT_SHA256,
        },
        evidence={
            "ordered_wal_ref": {
                "path": projection_rel,
                "sha256": _sha256(projection),
            },
            "execution_provenance_ref": {
                "path": provenance_rel,
                "sha256": _sha256(provenance),
            },
        },
    )


def build_fixture_repository(root: Path) -> FixtureRepository:
    fixture_root = Path(root)
    fixture_root.mkdir(parents=True, exist_ok=True)
    manifest = build_authority_manifest()
    authority_path = fixture_root / "authority" / "reflux_origin_authority_v2.json"
    closure_path = fixture_root / "source-closure.json"
    recovery_path = fixture_root / "recovery-envelope.json"
    launch_path = fixture_root / "launch-admission-inputs.json"
    _write_create_only(authority_path, _authority_bytes(manifest))
    _write_create_only(closure_path, _canonical_bytes(build_source_closure_record()))
    _write_create_only(
        recovery_path, _canonical_bytes(build_recovery_envelope_inputs())
    )
    _write_create_only(launch_path, _canonical_bytes(build_launch_admission_inputs()))
    for name, raw in _artifact_bytes().items():
        _write_create_only(fixture_root / "artifacts" / name, raw)

    records = [_record_for_query(fixture_root, 0, _SOURCE_MASK)]
    records.extend(
        _record_for_query(fixture_root, 1 + mask, mask) for mask in range(32)
    )
    write_evidence_tree(fixture_root, records)
    origin = records[0]["origin_binding"]["origin_id"]
    result_paths = tuple(
        fixture_root
        / "reports"
        / "reflux-result-evidence"
        / origin
        / _BATCH_ID
        / f"{query}.json"
        for query in range(33)
    )
    return FixtureRepository(
        root=fixture_root,
        authority_manifest_path=authority_path,
        source_closure_path=closure_path,
        recovery_envelope_path=recovery_path,
        launch_admission_inputs_path=launch_path,
        evidence_root=fixture_root,
        result_evidence_paths=result_paths,
    )


def baseline() -> dict:
    return copy.deepcopy(json.loads(_BASELINE_PATH.read_text(encoding="utf-8")))
