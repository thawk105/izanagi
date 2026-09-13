# -*- coding: utf-8 -*-
from __future__ import annotations

from orchestrator.tests.s8b_v2_freeze_fixture import in_sealed_fixture_process

import copy
import hashlib
import json
import pickle
from types import SimpleNamespace
import tempfile
from pathlib import Path

import pytest

from orchestrator.campaign import s8b_binary_admission as A
from orchestrator.tests.s8b_v2_freeze_fixture import (
    portable_binary_admission_receipt_fixture, sealed_source_protection_fixture,
)
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
    compiler_schema: str = "v1", before_issue=None,
    provide_dependency_context: bool = True,
    issuer=None, issue_arguments=None,
) -> dict:
    source_root = Path(tempfile.mkdtemp(prefix=f"{root_name}-", dir=tmp_path))
    compiler_input = source_root / "include" / "fixture.hh"
    compiler_input.parent.mkdir()
    compiler_input.write_bytes(b"fixture compiler input\n")
    compiler_input_manifest = {
        "schema_version": f"s8b-compiler-input/{compiler_schema}",
        "metadata_schema": "cmake-unix-makefiles-cxx-depfile/v1",
        "target": "ycsb_fixture.exe",
        "depfile_count": 1,
        "inputs": [{
            "path": "include/fixture.hh",
            "sha256": hashlib.sha256(compiler_input.read_bytes()).hexdigest(),
        }],
    }
    current_masstree_root = None
    current_dependency_roots = None
    if compiler_schema == "v2":
        current_masstree_root = tmp_path / f"{root_name}-masstree"
        current_input = current_masstree_root / "include" / "fixture.hh"
        current_input.parent.mkdir(parents=True)
        current_input.write_bytes(b"fixture compiler input\n")
        compiler_input_manifest["input_policy"] = (
            "snapshot-and-external-hashes/v1"
        )
        compiler_input_manifest["inputs"] = [{
            "root": "fetchcontent-masstree",
            "path": "include/fixture.hh",
            "sha256": hashlib.sha256(current_input.read_bytes()).hexdigest(),
        }]
    elif compiler_schema == "v3":
        first = tmp_path / f"{root_name}-dependency-a"
        second = tmp_path / f"{root_name}-dependency-b"
        current_input = first / "include" / "fixture.hh"
        current_input.parent.mkdir(parents=True)
        current_input.write_bytes(b"fixture compiler input\n")
        second.mkdir()
        current_dependency_roots = (first, second)
        compiler_input_manifest["input_policy"] = (
            "snapshot-and-external-hashes/v1"
        )
        compiler_input_manifest["inputs"] = [{
            "root": "dependency-prefix",
            "path": "include/fixture.hh",
            "sha256": hashlib.sha256(current_input.read_bytes()).hexdigest(),
        }]
    elif compiler_schema != "v1":
        raise ValueError(compiler_schema)
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
    # Portable reader fixtures carry a dict. Issuer coverage keeps the real API
    # and real seal/cleanup/issue mechanism; only unrelated Git replay/evidence
    # inputs use this tiny fixed source tree.
    issue = portable_binary_admission_receipt_fixture
    extra = {}
    snapshot_sha = _EXPECTED_MATERIALIZATION_SHA
    if issuer is not None or before_issue is not None or not provide_dependency_context:
        issue = A.issue_binary_admission_receipt if issuer is None else issuer
        protection = sealed_source_protection_fixture(
            source=source, binary_sha256=binary_sha,
            compiler_input_manifest_sha256=compiler_input_manifest_sha256,
        )
        snapshot_sha = protection.source_snapshot_sha256
        extra = {
            "source_protection": protection,
            "current_compiler_input_masstree_root": current_masstree_root,
            "current_compiler_input_dependency_prefix_roots": (
                current_dependency_roots if provide_dependency_context else None
            ),
        }
    if before_issue is not None:
        before_issue(
            current_masstree_root
            if current_masstree_root is not None
            else current_dependency_roots[0]
        )
    issue_kwargs = dict(
        admission=admission, expected_policy=context.policy, source=source,
        cell_id=cell_id, holdout_id=holdout_id, configuration_id=configuration_id,
        binding=binding, binary=binary, binary_sha256=binary_sha,
        contract_sha256=_CONTRACT_SHA, trace=False,
        source_snapshot_sha256=snapshot_sha,
        expected_materialization_sha256=snapshot_sha,
        compiler_input_manifest=compiler_input_manifest,
        compiler_input_manifest_sha256=compiler_input_manifest_sha256,
        **extra,
    )
    if issue_arguments is not None:
        issue_arguments.update(issue_kwargs)
    receipt = issue(**issue_kwargs)
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


@in_sealed_fixture_process
def test_issue_and_validate_binary_admission_receipt_round_trip(tmp_path: Path):
    record = _honest_record(tmp_path, issuer=A.issue_binary_admission_receipt)
    assert _validate(record) == record["admission_receipt"]
    assert set(record) == set(A.PORTABLE_BUILT_KEYS)


@in_sealed_fixture_process
def test_issue_v2_receipt_rechecks_current_fetchcontent_root(
        tmp_path: Path, monkeypatch):
    original_validate = A.s8b_compiler_input.validate_compiler_input_manifest

    def issuer_boundary_validate(
            manifest, expected_sha256, *, snapshot_root, target=None,
            expected_evolve_block_sources=None,
            current_fetchcontent_masstree_root=None,
            current_dependency_prefix_roots=None):
        # Isolate the issuer boundary: omitting the live root must not receive
        # an independent fail-closed assist from the lower validator.
        if current_fetchcontent_masstree_root is None:
            return A.s8b_compiler_input._normalized_manifest(
                manifest, target=target,
            )
        return original_validate(
            manifest, expected_sha256,
            snapshot_root=snapshot_root,
            target=target,
            expected_evolve_block_sources=expected_evolve_block_sources,
            current_fetchcontent_masstree_root=(
                current_fetchcontent_masstree_root
            ),
            current_dependency_prefix_roots=(
                current_dependency_prefix_roots
            ),
        )

    monkeypatch.setattr(
        A.s8b_compiler_input,
        "validate_compiler_input_manifest",
        issuer_boundary_validate,
    )

    def drift(root):
        (root / "include" / "fixture.hh").write_bytes(b"receipt-time drift\n")

    with pytest.raises(A.BinaryAdmissionError, match="compiler input manifest"):
        _honest_record(
            tmp_path, compiler_schema="v2", before_issue=drift,
        )


@in_sealed_fixture_process
def test_issue_v3_receipt_rechecks_current_dependency_prefix_roots(
        tmp_path: Path):
    def drift(root):
        (root / "include" / "fixture.hh").write_bytes(
            b"receipt-time dependency drift\n"
        )

    with pytest.raises(A.BinaryAdmissionError, match="compiler input manifest"):
        _honest_record(
            tmp_path, compiler_schema="v3", before_issue=drift,
        )


@pytest.mark.parametrize("mutation", ["missing", "ambiguous"])
@in_sealed_fixture_process
def test_issue_v3_receipt_rejects_missing_and_ambiguous_dependency_root(
        tmp_path: Path, mutation):
    def mutate(root):
        leaf = root / "include" / "fixture.hh"
        if mutation == "missing":
            leaf.unlink()
        else:
            assert root.name.endswith("-a")
            other = root.with_name(root.name[:-2] + "-b")
            candidate = other / "include" / "fixture.hh"
            candidate.parent.mkdir()
            candidate.write_bytes(leaf.read_bytes())

    with pytest.raises(A.BinaryAdmissionError, match="compiler input manifest"):
        _honest_record(
            tmp_path, root_name=f"v3-{mutation}", compiler_schema="v3",
            before_issue=mutate,
        )


@in_sealed_fixture_process
def test_issue_v3_receipt_rejects_unpresented_dependency_context(tmp_path: Path):
    with pytest.raises(A.BinaryAdmissionError, match="compiler input manifest"):
        _honest_record(
            tmp_path, compiler_schema="v3",
            provide_dependency_context=False,
        )


def test_portable_validator_accepts_v1_and_v2_without_live_paths(tmp_path: Path):
    legacy = _honest_record(tmp_path, root_name="legacy", compiler_schema="v1")
    current = _honest_record(tmp_path, root_name="current", compiler_schema="v2")
    assert _validate(legacy) == legacy["admission_receipt"]
    current_manifest = current["admission_receipt"]["proof"][
        "compiler_input_manifest"
    ]
    current_root = tmp_path / "current-masstree"
    import shutil
    shutil.rmtree(current_root)
    assert current_manifest["schema_version"] == "s8b-compiler-input/v2"
    assert _validate(current) == current["admission_receipt"]


def test_portable_validator_accepts_v3_after_live_dependency_roots_disappear(
        tmp_path: Path):
    record = _honest_record(
        tmp_path, root_name="portable-v3", compiler_schema="v3",
    )
    receipt_text = json.dumps(record["admission_receipt"], sort_keys=True)
    assert "portable-v3-dependency-a" not in receipt_text
    assert "portable-v3-dependency-b" not in receipt_text

    import shutil
    shutil.rmtree(tmp_path / "portable-v3-dependency-a")
    shutil.rmtree(tmp_path / "portable-v3-dependency-b")
    assert _validate(record) == record["admission_receipt"]


def test_portable_validator_rejects_nonexact_v2_manifest_after_resealing(
        tmp_path: Path):
    record = _honest_record(tmp_path, compiler_schema="v2")
    receipt = record["admission_receipt"]
    manifest = receipt["proof"]["compiler_input_manifest"]
    manifest["inputs"][0]["unexpected"] = True
    receipt["subject"]["compiler_input_manifest_sha256"] = _canonical_sha(
        manifest
    )
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256")
    receipt["receipt_sha256"] = _canonical_sha(unsigned)

    with pytest.raises(A.BinaryAdmissionError, match="manifest が不正"):
        _validate(record)


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


def _reseal_receipt(record):
    receipt = record["admission_receipt"]
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256")
    receipt["receipt_sha256"] = _canonical_sha(unsigned)


@pytest.mark.parametrize("kind", ["sealed-build", "sealed-cache-hit"])
def test_portable_validator_accepts_v3_source_protection(tmp_path, kind):
    record = _honest_record(tmp_path)
    receipt = record["admission_receipt"]
    receipt["proof"]["source_protection"]["kind"] = kind
    _reseal_receipt(record)
    assert receipt["schema"] == "s8b-binary-admission/v3"
    assert _validate(record) == receipt


@pytest.mark.parametrize("policy", [None, "invalid-policy"])
def test_portable_validator_rejects_v1_schema_before_policy(tmp_path, policy):
    record = _honest_record(tmp_path)
    record["admission_receipt"]["schema"] = "s8b-binary-admission/v1"
    _reseal_receipt(record)
    with pytest.raises(A.BinaryAdmissionError, match="receipt schema"):
        A.validate_portable_binary_record(record, expected_policy=policy)


@pytest.mark.parametrize("policy", [None, "invalid-policy"])
def test_portable_validator_rejects_v2_schema_before_policy(tmp_path, policy):
    record = _honest_record(tmp_path)
    record["admission_receipt"]["schema"] = "s8b-binary-admission/v2"
    _reseal_receipt(record)
    with pytest.raises(A.BinaryAdmissionError, match="receipt schema"):
        A.validate_portable_binary_record(record, expected_policy=policy)


def test_portable_validator_requires_source_protection(tmp_path):
    record = _honest_record(tmp_path)
    del record["admission_receipt"]["proof"]["source_protection"]
    _reseal_receipt(record)
    with pytest.raises(A.BinaryAdmissionError, match="receipt proof の exact key"):
        _validate(record)


def test_portable_validator_rejects_none_source_protection(tmp_path):
    record = _honest_record(tmp_path)
    record["admission_receipt"]["proof"]["source_protection"] = None
    _reseal_receipt(record)
    with pytest.raises(A.BinaryAdmissionError, match="proof.source_protection の exact key"):
        _validate(record)


def test_portable_validator_rejects_unknown_protection_kind(tmp_path):
    record = _honest_record(tmp_path)
    record["admission_receipt"]["proof"]["source_protection"]["kind"] = "readonly"
    _reseal_receipt(record)
    with pytest.raises(A.BinaryAdmissionError, match="source_protection.kind"):
        _validate(record)


@pytest.mark.parametrize("key", [
    "kind", "source_snapshot_sha256", "expected_materialization_sha256",
    "binary_sha256", "compiler_input_manifest_sha256",
])
def test_portable_validator_rejects_missing_protection_key(tmp_path, key):
    record = _honest_record(tmp_path)
    del record["admission_receipt"]["proof"]["source_protection"][key]
    _reseal_receipt(record)
    with pytest.raises(A.BinaryAdmissionError, match="proof.source_protection の exact key"):
        _validate(record)


def test_portable_validator_rejects_extra_protection_key(tmp_path):
    record = _honest_record(tmp_path)
    record["admission_receipt"]["proof"]["source_protection"]["extra"] = True
    _reseal_receipt(record)
    with pytest.raises(A.BinaryAdmissionError, match="proof.source_protection の exact key"):
        _validate(record)


@pytest.mark.parametrize("key", [
    "source_snapshot_sha256", "expected_materialization_sha256",
    "binary_sha256", "compiler_input_manifest_sha256",
])
def test_portable_validator_rejects_protection_digest_mismatch(tmp_path, key):
    record = _honest_record(tmp_path)
    protection = record["admission_receipt"]["proof"]["source_protection"]
    replacement = hashlib.sha256(("different:" + key).encode()).hexdigest()
    assert replacement != protection[key]
    protection[key] = replacement
    _reseal_receipt(record)
    with pytest.raises(A.BinaryAdmissionError, match="source_protection." + key):
        _validate(record)


@pytest.mark.parametrize("case", ["none", "dict", "string", "lookalike", "pickle"])
def test_issuer_rejects_nonissued_source_protection(tmp_path, case):
    arguments = {}
    record = _honest_record(tmp_path, issue_arguments=arguments)
    projection = record["admission_receipt"]["proof"]["source_protection"]
    lookalike = SimpleNamespace(**projection)
    value = {
        "none": None, "dict": projection, "string": "sealed-build",
        "lookalike": lookalike, "pickle": pickle.loads(pickle.dumps(lookalike)),
    }[case]
    with pytest.raises(A.BinaryAdmissionError, match="source protection capability"):
        A.issue_binary_admission_receipt(**arguments, source_protection=value)


def test_issuer_requires_source_protection_argument(tmp_path):
    arguments = {}
    _honest_record(tmp_path, issue_arguments=arguments)
    with pytest.raises(TypeError, match="source_protection"):
        A.issue_binary_admission_receipt(**arguments)


@in_sealed_fixture_process
def test_issuer_rejects_pickle_reconstruction_of_issued_capability(tmp_path):
    def reconstructed_issuer(**arguments):
        original = arguments["source_protection"]
        reconstructed = pickle.loads(pickle.dumps(original))
        assert type(reconstructed) is type(original)
        assert reconstructed is not original
        arguments["source_protection"] = reconstructed
        return A.issue_binary_admission_receipt(**arguments)

    with pytest.raises(A.BinaryAdmissionError, match="source protection capability"):
        _honest_record(tmp_path, issuer=reconstructed_issuer)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
