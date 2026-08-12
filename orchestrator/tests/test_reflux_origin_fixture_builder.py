from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest

from orchestrator.tests import reflux_origin_fixture_builder as F


EXPORTS = {
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
}
BASELINED_BUILDERS = {
    name: getattr(F, name)
    for name in (
        "build_authority_manifest",
        "build_source_closure_record",
        "build_result_evidence_record",
        "build_ordered_wal_projection",
        "build_execution_provenance",
        "build_recovery_envelope_inputs",
        "build_launch_admission_inputs",
    )
}


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest_entry(value: object) -> dict:
    raw = _canonical(value)
    return {"canonical_sha256": hashlib.sha256(raw).hexdigest(), "byte_length": len(raw)}


def _leaf_paths(value: object, prefix: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    if isinstance(value, dict):
        return [
            path
            for key, child in value.items()
            for path in _leaf_paths(child, prefix + (str(key),))
        ]
    if isinstance(value, list):
        return [
            path
            for index, child in enumerate(value)
            for path in _leaf_paths(child, prefix + (str(index),))
        ]
    return [prefix]


def _replacement(value: object) -> object:
    if value is None:
        return "fixture-negative"
    if type(value) is bool:
        return not value
    if type(value) is int:
        return value + 1
    if type(value) is str:
        return value + "-negative"
    raise AssertionError(f"unsupported fixture leaf type: {type(value)!r}")


def _lookup(value: object, path: tuple[str, ...]) -> object:
    current = value
    for component in path:
        current = current[int(component)] if isinstance(current, list) else current[component]
    return current


def test_export_api_and_signatures_are_exactly_frozen() -> None:
    assert set(F.__all__) == EXPORTS
    assert len(F.__all__) == len(EXPORTS)
    for name in EXPORTS:
        assert inspect.isfunction(getattr(F, name))

    root_signature = inspect.signature(F.build_fixture_repository)
    assert tuple(root_signature.parameters) == ("root",)
    evidence_signature = inspect.signature(F.write_evidence_tree)
    assert tuple(evidence_signature.parameters) == ("root", "records")
    assert not inspect.signature(F.baseline).parameters
    for name in BASELINED_BUILDERS:
        parameters = tuple(inspect.signature(getattr(F, name)).parameters.values())
        assert len(parameters) == 1
        assert parameters[0].kind is inspect.Parameter.VAR_KEYWORD
        assert parameters[0].name == "overrides"


def test_baseline_schema_and_every_entry_match_independent_recalculation() -> None:
    frozen = F.baseline()
    assert set(frozen) == {"schema_version", "entries"}
    assert frozen["schema_version"] == "izanagi-reflux-fixture-baseline/v1"
    assert set(frozen["entries"]) == set(BASELINED_BUILDERS)
    assert frozen["entries"] == {
        name: _digest_entry(builder()) for name, builder in BASELINED_BUILDERS.items()
    }
    for entry in frozen["entries"].values():
        assert set(entry) == {"canonical_sha256", "byte_length"}
        assert len(entry["canonical_sha256"]) == 64
        int(entry["canonical_sha256"], 16)
        assert type(entry["byte_length"]) is int and entry["byte_length"] > 0


def test_one_field_builder_mutation_is_detected_by_frozen_baseline() -> None:
    changed = F.build_result_evidence_record(
        physical_result__build_attempt_id="fixture-build-attempt-mutated"
    )
    assert _digest_entry(changed) != F.baseline()["entries"][
        "build_result_evidence_record"
    ]


@pytest.mark.parametrize("name", tuple(BASELINED_BUILDERS))
def test_every_existing_leaf_is_individually_overrideable(name: str) -> None:
    builder = BASELINED_BUILDERS[name]
    original = builder()
    for path in _leaf_paths(original):
        replacement = _replacement(_lookup(original, path))
        changed = builder(**{"__".join(path): replacement})
        assert _lookup(changed, path) == replacement, (name, path)
        assert changed != original, (name, path)


def test_overrides_can_add_or_remove_keys_for_exact_schema_negative_cases() -> None:
    result = F.build_result_evidence_record(
        unexpected="top-level",
        origin_binding__unexpected="nested",
    )
    assert result["unexpected"] == "top-level"
    assert result["origin_binding"]["unexpected"] == "nested"
    missing = F.build_result_evidence_record(
        issuer=...,
        origin_binding__authority_blob_sha256=...,
    )
    assert "issuer" not in missing
    assert "authority_blob_sha256" not in missing["origin_binding"]
    shortened = F.build_source_closure_record(
        referents__axis_semantics_sha256__runtime_field_paths__0=...
    )
    assert len(
        shortened["referents"]["axis_semantics_sha256"]["runtime_field_paths"]
    ) == 2


def test_exact_schema_key_sets_and_canonical_bytes_contract() -> None:
    closure = F.build_source_closure_record()
    assert set(closure) == {
        "schema_version",
        "captured_commit_oid",
        "authority_series_id",
        "origin_id",
        "cell_key",
        "referents",
    }
    assert set(closure["referents"]) == {
        "authority.workload.descriptor_sha256",
        "axis_semantics_sha256",
        "verifier_policy_sha256",
        "environment_contract_sha256",
    }
    for referent in closure["referents"].values():
        assert set(referent) == {
            "preimage_ref",
            "digest_rule",
            "producer_field",
            "runtime_field_paths",
        }
        assert set(referent["preimage_ref"]) == {"path", "sha256"}

    result = F.build_result_evidence_record()
    assert set(result) == {
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
    exact_nested = {
        "issuer": {"kind"},
        "origin_binding": {
            "authority_blob_sha256",
            "source_closure_sha256",
            "origin_id",
            "cell_key",
            "workload",
            "axis_semantics_sha256",
            "verifier_policy_sha256",
            "environment_contract_sha256",
        },
        "trial_binding": {"launch_admission_record_sha256", "campaign_id", "workload"},
        "ledger_member": {"batch_id", "iteration_index", "query_ordinal", "replicate_ordinal"},
        "p6_plan": {"purpose", "hypothesis_sha256", "validation_plan_sha256"},
        "trigger_binding": {"mask", "candidate_wire", "trigger_gate_binding_commitment"},
        "physical_result": {"build_attempt_id", "outcome", "constraint_sha256"},
        "evidence": {"ordered_wal_ref", "execution_provenance_ref"},
    }
    for key, expected in exact_nested.items():
        assert set(result[key]) == expected
    for ref in result["evidence"].values():
        assert set(ref) == {"path", "sha256"}
    assert "sha256" not in result
    raw = _canonical(result)
    assert not raw.endswith(b"\n")
    assert raw.decode("utf-8").startswith('{"evidence":')


def test_capability_and_recovery_topology_match_exact_contracts() -> None:
    capability = F.build_launch_admission_inputs()
    assert set(capability) == {
        "authority_blob_sha256",
        "source_closure_sha256",
        "origin_id",
        "cell_key",
        "authority_workload",
        "axis_semantics_sha256",
        "verifier_policy_sha256",
        "environment_contract_sha256",
        "campaign_id",
        "trial_workload",
        "measurement_head",
        "store_scope",
        "issuer_seal",
    }
    assert set(capability["authority_workload"]) == {
        "descriptor_sha256",
        "records",
        "threads",
    }
    assert capability["store_scope"] == "fixture"

    envelope = F.build_recovery_envelope_inputs()
    assert set(envelope) == {
        "schema_version",
        "origin_binding_capability_sha256",
        "source_closure_sha256",
        "hypothesis_sha256",
        "validation_plan_sha256",
        "reserve_attempts",
        "event_operation_ids",
        "members",
        "expected_state_commitment",
    }
    assert len(envelope["reserve_attempts"]) == 2
    assert [item["attempt"] for item in envelope["reserve_attempts"]] == [0, 1]
    assert set(envelope["event_operation_ids"]) == {
        "reserve_attempt_0",
        "abandon_attempt_0",
        "reserve_attempt_1",
        "batch_commit",
        "results_prepare",
        "results_open",
        "origin_terminal",
    }
    members = envelope["members"]
    assert len(members) == 33
    assert members[0]["query_ordinal"] == 0
    assert members[0]["candidate_wire"] == "11100"
    assert members[0]["replicate_ordinal"] == 0
    for mask, member in enumerate(members[1:]):
        assert member["query_ordinal"] == 1 + mask
        assert member["iteration_index"] == 0
        assert member["candidate_wire"] == "".join(
            "1" if mask & (1 << bit) else "0" for bit in range(5)
        )
        assert member["replicate_ordinal"] == (1 if mask == 7 else 0)
        assert set(member) == {
            "iteration_index",
            "query_ordinal",
            "replicate_ordinal",
            "purpose",
            "candidate_wire",
            "candidate_salt",
            "result_evidence_salt",
            "constraint_salt",
            "evidence_path",
        }


def test_fixture_repository_writes_33_consistent_create_only_records(
    tmp_path: Path,
) -> None:
    repository = F.build_fixture_repository(tmp_path / "fixture")
    assert repository.root == tmp_path / "fixture"
    assert len(repository.result_evidence_paths) == 33
    assert all(path.is_file() for path in repository.result_evidence_paths)
    records = [json.loads(path.read_bytes()) for path in repository.result_evidence_paths]
    assert [record["ledger_member"]["query_ordinal"] for record in records] == list(range(33))
    assert len({record["physical_result"]["build_attempt_id"] for record in records}) == 33
    assert all(not path.read_bytes().endswith(b"\n") for path in repository.result_evidence_paths)
    for path, record in zip(repository.result_evidence_paths, records):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == hashlib.sha256(
            _canonical(record)
        ).hexdigest()
        wal_ref = record["evidence"]["ordered_wal_ref"]
        projection_path = repository.root / wal_ref["path"]
        projection_raw = projection_path.read_bytes()
        assert hashlib.sha256(projection_raw).hexdigest() == wal_ref["sha256"]
        projection = json.loads(projection_raw)
        source_ref = projection["source_wal_ref"]
        source_raw = (repository.root / source_ref["path"]).read_bytes()
        assert hashlib.sha256(source_raw).hexdigest() == source_ref["sha256"]
        interval = source_raw[projection["byte_start"]:projection["byte_end"]]
        assert interval == _canonical(projection["records"])
        provenance_ref = record["evidence"]["execution_provenance_ref"]
        provenance_raw = (repository.root / provenance_ref["path"]).read_bytes()
        assert hashlib.sha256(provenance_raw).hexdigest() == provenance_ref["sha256"]
    with pytest.raises(FileExistsError):
        F.build_fixture_repository(repository.root)


def test_defaults_ignore_volatile_cwd_environment_and_unrelated_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = {name: _canonical(builder()) for name, builder in BASELINED_BUILDERS.items()}
    volatile = tmp_path / "volatile"
    volatile.mkdir()
    (volatile / "untracked-diagnostic-payload").write_text(
        "working-tree-sha=changed\ntime=2099-01-01\n/absolute/path\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(volatile)
    monkeypatch.setenv("GIT_AUTHOR_DATE", "2099-01-01T00:00:00Z")
    monkeypatch.setenv("PWD", str(volatile))
    after = {name: _canonical(builder()) for name, builder in BASELINED_BUILDERS.items()}
    assert after == before
