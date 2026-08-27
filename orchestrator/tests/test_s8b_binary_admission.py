# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from pathlib import Path

import pytest

from orchestrator.campaign import s8b_binary_admission as A
from orchestrator.campaign.build_admission import (
    GeneratorId,
    ReviewId,
    build_run_context,
    derive_build_admission,
    resolve_current_build_admission_policy,
)
from orchestrator.campaign.s8b_materialization import reviewed_source_capability
from orchestrator.campaign.source_digest import SOURCE_EVIDENCE_SCHEMA, SourceEvidence
from orchestrator.tests.s8b_floor_evidence_fixture import (
    expected_portable_sort_swo_pass_receipt,
)


_ENTRY_SHA = hashlib.sha256(b"freeze-entry").hexdigest()
_CONTRACT_SHA = hashlib.sha256(b"contract").hexdigest()
_SOURCE_TOKEN = hashlib.sha256(b"source-token").hexdigest()
_CCBENCH_PIN = "1" * 40
_GENOME = '{"fixture":"s8b-admission"}'
_EXPECTED_MATERIALIZATION_SHA = hashlib.sha256(
    b"s8b-admission-expected-materialization"
).hexdigest()


def _canonical_sha(value: dict) -> str:
    raw = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _binding() -> dict:
    variant_id = hashlib.sha256(
        f"{_GENOME}|src={_SOURCE_TOKEN}".encode("utf-8")
    ).hexdigest()[:12]
    body = {
        "genome_canonical": _GENOME,
        "src_token": _SOURCE_TOKEN,
        "variant_id": variant_id,
        "entry_sha256": _ENTRY_SHA,
    }
    raw = json.dumps(
        body, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    body["binding_sha256"] = hashlib.sha256(raw).hexdigest()
    return body


def _honest_record(
    tmp_path: Path, *, root_name: str = "root-a", cell_id: str = "h1::cfg",
    holdout_id: str = "h1", configuration_id: str = "cfg",
    binary_bytes: bytes = b"honest-s8b-binary",
) -> dict:
    source_root = Path(tempfile.mkdtemp(prefix=f"{root_name}-", dir=tmp_path))
    compiler_input = source_root / "include" / "fixture.hh"
    compiler_input.parent.mkdir()
    compiler_input.write_bytes(b"fixture compiler input\n")
    compiler_input_manifest = {
        "schema_version": "s8b-compiler-input/v1",
        "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
        "target": "ycsb_fixture.exe",
        "depfile_count": 1,
        "inputs": [{
            "path": "include/fixture.hh",
            "sha256": hashlib.sha256(compiler_input.read_bytes()).hexdigest(),
        }],
    }
    compiler_input_manifest_sha256 = _canonical_sha(compiler_input_manifest)
    source = SourceEvidence(
        schema_version=SOURCE_EVIDENCE_SCHEMA,
        source_root=str(source_root.resolve()),
        ccbench_commit=_CCBENCH_PIN,
        genome_sha256=hashlib.sha256(_GENOME.encode("utf-8")).hexdigest(),
        src_token=_SOURCE_TOKEN,
        source_bytes_sha256=hashlib.sha256(b"source-bytes").hexdigest(),
        tracked_clean=False,
        tracked_diff_sha256=hashlib.sha256(b"tracked-diff").hexdigest(),
        tracked_paths=("include/backoff.hh",),
    )
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    review = reviewed_source_capability(
        review_id=ReviewId.S8B_FLOOR, source=source, input_sha256=_ENTRY_SHA,
    )
    admission = derive_build_admission(context, source, review_receipt=review)
    binary = tmp_path / f"{root_name}-{cell_id.replace('::', '-')}.bin"
    binary.write_bytes(binary_bytes)
    binary_sha = hashlib.sha256(binary_bytes).hexdigest()
    binding = _binding()
    receipt = A.issue_binary_admission_receipt(
        admission=admission, expected_policy=context.policy, source=source,
        cell_id=cell_id, holdout_id=holdout_id, configuration_id=configuration_id,
        binding=binding, binary=binary, binary_sha256=binary_sha,
        contract_sha256=_CONTRACT_SHA, trace=False,
        source_snapshot_sha256=_EXPECTED_MATERIALIZATION_SHA,
        expected_materialization_sha256=_EXPECTED_MATERIALIZATION_SHA,
        compiler_input_manifest=compiler_input_manifest,
        compiler_input_manifest_sha256=compiler_input_manifest_sha256,
    )
    record = {
        "cell_id": cell_id,
        "holdout_id": holdout_id,
        "configuration_id": configuration_id,
        "binary": "build/fixture.bin",
        "binary_sha256": binary_sha,
        "bin_hash_short": binary_sha[:16],
        "binding": binding,
        "configure_argv": ["cmake", "fixture"],
        "build_argv": ["cmake", "--build", "fixture"],
        "cached": False,
        "store_path": f"store/{binary_sha}",
        "admission_receipt": receipt,
    }
    if configuration_id == "sort_best":
        record["sort_swo_oracle"] = expected_portable_sort_swo_pass_receipt(
            cell_id=cell_id, holdout_id=holdout_id,
            configuration_id=configuration_id, entry_sha256=_ENTRY_SHA,
            binary_sha256=binary_sha,
        )
    return record


def _validate(
    record: dict, *, expected_ccbench_pin: str = _CCBENCH_PIN,
    expected_contract_sha256: str = _CONTRACT_SHA,
) -> dict:
    return A.validate_portable_binary_record(
        record, expected_policy=resolve_current_build_admission_policy(),
        expected_ccbench_pin=expected_ccbench_pin,
        expected_contract_sha256=expected_contract_sha256,
        expected_cell_id=record["cell_id"],
        expected_holdout_id=record["holdout_id"],
        expected_configuration_id=record["configuration_id"],
        expected_entry_sha256=record["binding"]["entry_sha256"],
        expected_binding_sha256=record["binding"]["binding_sha256"],
    )


def test_issue_and_validate_binary_admission_receipt_round_trip(tmp_path: Path):
    record = _honest_record(tmp_path)
    assert _validate(record) == record["admission_receipt"]
    assert set(record) == set(A.PORTABLE_BUILT_KEYS)


def test_conditional_portable_key_sets_and_sort_round_trip(tmp_path: Path):
    sort_record = _honest_record(
        tmp_path, cell_id="h1::sort_best", configuration_id="sort_best",
    )
    assert A.PORTABLE_SORT_BEST_BUILT_KEYS == A.PORTABLE_BUILT_KEYS | {
        "sort_swo_oracle"
    }
    assert A.portable_built_keys_for("sort_best") is A.PORTABLE_SORT_BEST_BUILT_KEYS
    assert A.portable_built_keys_for("stock_common") is A.PORTABLE_BUILT_KEYS
    assert set(sort_record) == set(A.portable_built_keys_for("sort_best"))
    assert _validate(sort_record) == sort_record["admission_receipt"]


@pytest.mark.parametrize("configuration_id", ["cfg", "sort_best"])
def test_central_validator_rejects_unexpected_top_level_key(
    tmp_path: Path, configuration_id: str,
):
    cell_id = f"h1::{configuration_id}"
    record = _honest_record(
        tmp_path, cell_id=cell_id, configuration_id=configuration_id,
    )
    record["unexpected"] = True
    with pytest.raises(A.BinaryAdmissionError, match="exact key"):
        _validate(record)


def test_sort_best_requires_receipt_and_non_sort_forbids_it(tmp_path: Path):
    sort_record = _honest_record(
        tmp_path, cell_id="h1::sort_best", configuration_id="sort_best",
    )
    sort_record.pop("sort_swo_oracle")
    with pytest.raises(A.BinaryAdmissionError, match="exact key"):
        _validate(sort_record)

    non_sort = _honest_record(tmp_path)
    non_sort["sort_swo_oracle"] = expected_portable_sort_swo_pass_receipt(
        cell_id=non_sort["cell_id"], holdout_id=non_sort["holdout_id"],
        configuration_id=non_sort["configuration_id"], entry_sha256=_ENTRY_SHA,
        binary_sha256=non_sort["binary_sha256"],
    )
    with pytest.raises(A.BinaryAdmissionError, match="exact key"):
        _validate(non_sort)


def test_sort_receipt_identity_must_match_binary_record(tmp_path: Path):
    record = _honest_record(
        tmp_path, cell_id="h1::sort_best", configuration_id="sort_best",
    )
    record["sort_swo_oracle"]["binary_sha256"] = "0" * 64
    with pytest.raises(A.BinaryAdmissionError, match="SWO receipt"):
        _validate(record)


def test_receipt_is_canonical_and_root_neutral(tmp_path: Path):
    first = _honest_record(tmp_path, root_name="checkout-a")
    second = _honest_record(tmp_path, root_name="checkout-b")
    first_raw = json.dumps(
        first["admission_receipt"], ensure_ascii=True,
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    second_raw = json.dumps(
        second["admission_receipt"], ensure_ascii=True,
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    assert first_raw == second_raw
    assert b"checkout-a" not in first_raw
    assert b"checkout-b" not in second_raw


@pytest.mark.parametrize("invalid", [None, {}])
def test_validate_rejects_present_but_empty_admission_receipt(tmp_path: Path, invalid):
    record = _honest_record(tmp_path)
    record["admission_receipt"] = invalid
    with pytest.raises(A.BinaryAdmissionError):
        _validate(record)


def test_validate_rejects_binary_sha_record_mismatch(tmp_path: Path):
    record = _honest_record(tmp_path)
    replacement = hashlib.sha256(b"other-record-and-store-bytes").hexdigest()
    record["binary_sha256"] = replacement
    record["bin_hash_short"] = replacement[:16]
    record["store_path"] = f"store/{replacement}"
    with pytest.raises(A.BinaryAdmissionError, match="subject binary SHA"):
        _validate(record)


def test_validate_rejects_external_ccbench_pin_mismatch(tmp_path: Path):
    record = _honest_record(tmp_path)
    assert _validate(record) == record["admission_receipt"]
    mismatched_pin = "2" * 40
    assert mismatched_pin != record["admission_receipt"]["admission"]["source"][
        "ccbench_commit"
    ]
    with pytest.raises(
        A.BinaryAdmissionError,
        match="receipt source ccbench pin が外部期待値と不一致",
    ):
        _validate(record, expected_ccbench_pin=mismatched_pin)


def test_validate_rejects_external_contract_sha256_mismatch(tmp_path: Path):
    record = _honest_record(tmp_path)
    assert _validate(record) == record["admission_receipt"]
    mismatched_contract = "f" * 64
    assert mismatched_contract != record["admission_receipt"]["subject"][
        "contract_sha256"
    ]
    with pytest.raises(
        A.BinaryAdmissionError,
        match="receipt subject contract が外部期待値と不一致",
    ):
        _validate(record, expected_contract_sha256=mismatched_contract)


def test_validate_rejects_foreign_cell_receipt_with_identical_other_subjects(tmp_path: Path):
    first = _honest_record(tmp_path, root_name="one", cell_id="h1::cfg", holdout_id="h1")
    second = _honest_record(tmp_path, root_name="two", cell_id="h2::cfg", holdout_id="h2")
    assert first["binary_sha256"] == second["binary_sha256"]
    assert first["binding"] == second["binding"]
    first["admission_receipt"] = second["admission_receipt"]
    with pytest.raises(A.BinaryAdmissionError, match="cell/holdout/configuration/entry/binding"):
        _validate(first)


def test_validate_binds_subject_to_record_before_external_expected_tuple(tmp_path: Path):
    record = _honest_record(tmp_path, cell_id="h1::cfg", holdout_id="h1")
    record["cell_id"] = "contradictory-record-cell"
    with pytest.raises(A.BinaryAdmissionError, match="subject が record"):
        A.validate_portable_binary_record(
            record, expected_policy=resolve_current_build_admission_policy(),
            expected_ccbench_pin=_CCBENCH_PIN,
            expected_contract_sha256=_CONTRACT_SHA,
            expected_cell_id="h1::cfg", expected_holdout_id="h1",
            expected_configuration_id="cfg",
            expected_entry_sha256=record["binding"]["entry_sha256"],
            expected_binding_sha256=record["binding"]["binding_sha256"],
        )


def test_validate_rejects_current_policy_mismatch_after_outer_sha_is_resealed(tmp_path: Path):
    record = _honest_record(tmp_path)
    receipt = copy.deepcopy(record["admission_receipt"])
    receipt["admission"]["policy_sha256"] = "f" * 64
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256")
    receipt["receipt_sha256"] = _canonical_sha(unsigned)
    record["admission_receipt"] = receipt
    with pytest.raises(A.BinaryAdmissionError, match="現行 policy"):
        _validate(record)


def test_historical_validation_does_not_require_current_policy(tmp_path: Path):
    record = _honest_record(tmp_path)
    receipt = copy.deepcopy(record["admission_receipt"])
    receipt["admission"]["policy_sha256"] = "f" * 64
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256")
    receipt["receipt_sha256"] = _canonical_sha(unsigned)
    record["admission_receipt"] = receipt
    assert A.validate_portable_binary_record(
        record, expected_policy=None, expected_ccbench_pin=_CCBENCH_PIN,
        expected_contract_sha256=_CONTRACT_SHA,
        expected_cell_id=record["cell_id"],
        expected_holdout_id=record["holdout_id"],
        expected_configuration_id=record["configuration_id"],
        expected_entry_sha256=record["binding"]["entry_sha256"],
        expected_binding_sha256=record["binding"]["binding_sha256"],
    ) == receipt


def test_historical_validation_rejects_v1_and_missing_proof(tmp_path: Path):
    record = _honest_record(tmp_path)
    for mutation in ("v1", "missing-proof"):
        candidate = copy.deepcopy(record)
        receipt = candidate["admission_receipt"]
        if mutation == "v1":
            receipt["schema"] = "s8b-binary-admission/v1"
        else:
            receipt.pop("proof")
        unsigned = dict(receipt)
        unsigned.pop("receipt_sha256")
        receipt["receipt_sha256"] = _canonical_sha(unsigned)
        with pytest.raises(A.BinaryAdmissionError):
            A.validate_portable_binary_record(
                candidate, expected_policy=None,
                expected_ccbench_pin=_CCBENCH_PIN,
                expected_contract_sha256=_CONTRACT_SHA,
            )


@pytest.mark.parametrize(
    "case", ["unknown", "nested-missing", "schema", "review-id", "outer-sha"],
)
def test_validate_rejects_unknown_missing_and_malformed_receipt_fields(
        tmp_path: Path, case: str):
    record = _honest_record(tmp_path)
    receipt = record["admission_receipt"]
    if case == "unknown":
        receipt["unknown"] = True
    elif case == "nested-missing":
        receipt["admission"].pop("input_sha256")
    elif case == "schema":
        receipt["schema"] = "unknown-receipt/v1"
    elif case == "review-id":
        receipt["admission"]["review_id"] = "unknown-review"
    else:
        receipt["receipt_sha256"] = "0" * 64
    if case != "outer-sha":
        unsigned = dict(receipt)
        unsigned.pop("receipt_sha256")
        receipt["receipt_sha256"] = _canonical_sha(unsigned)
    with pytest.raises(A.BinaryAdmissionError):
        _validate(record)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
