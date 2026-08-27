from dataclasses import replace
from fractions import Fraction
import ast
import hashlib
import json
from pathlib import Path

import pytest

from orchestrator.campaign import p3_b4_analysis_prereg_consumer as consumer
from orchestrator.campaign.p3_b4_analysis_prereg_consumer import (
    B4PreregistrationContractError,
    PREREGISTRATION_SECTION_5_1_1_SHA256,
    assert_contract_constants_are_source_literals,
    assert_preregistration_matches_implementation,
    extract_preregistered_analysis_contract,
    generate_verified_analysis_source_closure_receipt,
    verify_repository_preregistration_contract,
)


_ROOT = Path(__file__).resolve().parents[2]
_DOCUMENT_PATH = _ROOT / "docs/phase3-b4-reflux-ablation-preregistration.md"
_CONTRACT_PATH = _ROOT / "orchestrator/campaign/p3_b4_analysis_contract.py"
_LEDGERS_PATH = _ROOT / "orchestrator/campaign/p3_b4_analysis_ledgers.py"
_ANALYSIS_PATH = _ROOT / "orchestrator/campaign/p3_b4_analysis_path.py"
_CLOSURE_PATHS = (
    "orchestrator/campaign/p3_b4_analysis_contract.py",
    "orchestrator/campaign/p3_b4_analysis_adapter.py",
    "orchestrator/campaign/p3_b4_analysis_ledgers.py",
    "orchestrator/campaign/p3_b4_analysis_path.py",
    "orchestrator/campaign/p3_b4_analysis_prereg_consumer.py",
)

_ANALYSIS_INVALID_REASONS = (
    "block_count_mismatch",
    "duplicate_block_id",
    "unknown_block_id",
    "precursor_hash_mismatch",
    "reference_binding_mismatch",
    "reference_value_domain_error",
    "status_domain_error",
    "throughput_contract_error",
    "floor_domain_error",
    "violation_count_domain_error",
    "binding_domain_error",
    "field_missing_or_ill_typed",
)
_REGISTRY_VIOLATION_REASONS = (
    "arm_digest_contaminated_precursor",
    "assignment_schedule_violated",
    "arm_asymmetric_gate",
    "env_tag_mismatch",
    "manifest_mutated_after_freeze",
)


def _document() -> bytes:
    return _DOCUMENT_PATH.read_bytes()


def _sources() -> dict[str, bytes]:
    return {
        "contract_source_bytes": _CONTRACT_PATH.read_bytes(),
        "ledgers_source_bytes": _LEDGERS_PATH.read_bytes(),
        "path_source_bytes": _ANALYSIS_PATH.read_bytes(),
    }


def _assert_document(document_bytes: bytes, **overrides: bytes):
    sources = _sources()
    sources.update(overrides)
    return assert_preregistration_matches_implementation(
        document_bytes=document_bytes,
        **sources,
    )


def _replace_once(document: bytes, old: bytes, new: bytes) -> bytes:
    assert old in document
    mutated = document.replace(old, new, 1)
    assert mutated != document
    return mutated


def _independent_exact_section(document: bytes) -> bytes:
    start_marker = "#### 5.1.1 分析契約の一括凍結 (D1082)\n".encode("utf-8")
    end_marker = "## 6. 実走の前提条件".encode("utf-8")
    assert document.count(start_marker) == 1
    start = document.index(start_marker)
    end = document.index(end_marker, start)
    return document[start:end]


def test_current_document_contract_literals_match_implementation() -> None:
    document = _document()
    independent_section = _independent_exact_section(document)
    independently_computed = hashlib.sha256(independent_section).hexdigest()
    assert independently_computed == PREREGISTRATION_SECTION_5_1_1_SHA256

    parsed = verify_repository_preregistration_contract(repository_root=_ROOT)
    assert parsed.section_sha256 == independently_computed
    assert parsed.analysis_invalid_reasons == _ANALYSIS_INVALID_REASONS
    assert parsed.registry_violation_reasons == _REGISTRY_VIOLATION_REASONS
    assert parsed.expected_block_count == 201
    assert parsed.test_unit == "block"
    assert parsed.a_min_is_verdict_threshold is False

    receipt = generate_verified_analysis_source_closure_receipt(
        repository_root=_ROOT
    )
    assert receipt.preregistration_section_sha256 == independently_computed
    assert receipt.consumer_result_sha256 == hashlib.sha256(
        receipt.consumer_result_canonical_bytes
    ).hexdigest()
    consumer_result = json.loads(receipt.consumer_result_canonical_bytes)
    assert consumer_result["schema_version"] == (
        consumer.analysis_path.B4_PREREGISTRATION_CONSUMER_RESULT_SCHEMA_VERSION
    )
    assert consumer_result["contract"]["section_sha256"] == independently_computed
    closure_payload = json.loads(receipt.canonical_bytes)
    assert closure_payload["consumer_result"] == consumer_result
    assert closure_payload["consumer_result_sha256"] == (
        receipt.consumer_result_sha256
    )


@pytest.mark.parametrize("literal", _ANALYSIS_INVALID_REASONS)
def test_each_analysis_invalid_literal_mutation_is_rejected(literal: str) -> None:
    document = _document()
    old = f"`{literal}`".encode("ascii")
    mutated = _replace_once(document, old, f"`mutated_{literal}`".encode("ascii"))
    with pytest.raises(B4PreregistrationContractError):
        extract_preregistered_analysis_contract(mutated)


@pytest.mark.parametrize("literal", _REGISTRY_VIOLATION_REASONS)
def test_each_registry_violation_literal_mutation_is_rejected(literal: str) -> None:
    document = _document()
    old = f"`{literal}`".encode("ascii")
    mutated = _replace_once(document, old, f"`mutated_{literal}`".encode("ascii"))
    with pytest.raises(B4PreregistrationContractError):
        extract_preregistered_analysis_contract(mutated)


def test_status_rank_and_threshold_mutations_are_rejected() -> None:
    document = _document()
    document_mutations = (
        _replace_once(
            document,
            "`certified` / `rejected` / `aborted` / `missing` のちょうど 4 値".encode("utf-8"),
            "`certified-x` / `rejected` / `aborted` / `missing` のちょうど 4 値".encode("utf-8"),
        ),
        _replace_once(
            document,
            "この 2 つの間だけが常に tie".encode("utf-8"),
            "この 3 つの間が常に tie".encode("utf-8"),
        ),
        _replace_once(
            document,
            "`A_min = 0.60`".encode("utf-8"),
            "`A_min = 0.61`".encode("utf-8"),
        ),
    )
    for mutated in document_mutations:
        with pytest.raises(B4PreregistrationContractError):
            extract_preregistered_analysis_contract(mutated)

    source = _CONTRACT_PATH.read_bytes()
    source_mutations = (
        _replace_once(source, b"EXPECTED_BLOCK_COUNT = 201", b"EXPECTED_BLOCK_COUNT = 202"),
        _replace_once(source, b"A_MIN = Fraction(3, 5)", b"A_MIN = Fraction(4, 5)"),
    )
    for mutated_source in source_mutations:
        with pytest.raises(B4PreregistrationContractError):
            _assert_document(
                document,
                contract_source_bytes=mutated_source,
            )


def test_sign_test_and_clopper_pearson_literal_mutations_are_rejected() -> None:
    document = _document()
    mutations = (
        _replace_once(
            document,
            "`Bin(m, 1/2)`".encode("utf-8"),
            "`Bin(m, 1/3)`".encode("utf-8"),
        ),
        _replace_once(
            document,
            "Clopper-Pearson の厳密両側 95% 区間".encode("utf-8"),
            "Clopper-Pearson の近似両側 95% 区間".encode("utf-8"),
        ),
        _replace_once(
            document,
            "`m = 0` のときは区間を `[0, 1]` とし、`theta` は推定不能".encode("utf-8"),
            "`m = 0` のときは区間を `[0, 1/2]` とし、`theta` は推定不能".encode("utf-8"),
        ),
    )
    for mutated in mutations:
        with pytest.raises(B4PreregistrationContractError):
            extract_preregistered_analysis_contract(mutated)

    source = _CONTRACT_PATH.read_bytes()
    alpha_mutation = _replace_once(
        source,
        b"ONE_SIDED_ALPHA = Fraction(1, 40)",
        b"ONE_SIDED_ALPHA = Fraction(1, 20)",
    )
    with pytest.raises(B4PreregistrationContractError):
        _assert_document(document, contract_source_bytes=alpha_mutation)


def test_formatting_equivalent_raw_byte_changes_are_rejected() -> None:
    document = _document()
    original_heading = "#### 5.1.1 分析契約の一括凍結 (D1082)".encode("utf-8")
    emphasized_heading = "#### **5.1.1**  分析契約の一括凍結  (D1082)".encode("utf-8")
    mutated = _replace_once(document, original_heading, emphasized_heading)
    original_paragraph = (
        "raw な試行記録から本節の入力型を作る経路 (adapter) と、その実装が本節の定義と一致することを\n"
        "  検査する consumer。"
    ).encode("utf-8")
    reflowed_paragraph = (
        "raw な試行記録から本節の入力型を作る経路 (adapter) と、その実装が本節の定義と一致することを "
        "検査する consumer。"
    ).encode("utf-8")
    mutated = _replace_once(mutated, original_paragraph, reflowed_paragraph)

    with pytest.raises(B4PreregistrationContractError, match="exact raw"):
        _assert_document(mutated)


def test_semantic_change_with_identical_literals_is_rejected_by_section_hash() -> None:
    document = _document()
    mutated = _replace_once(
        document,
        "先頭 n 行".encode("utf-8"),
        "末尾 n 行".encode("utf-8"),
    )
    for literal in (
        *_ANALYSIS_INVALID_REASONS,
        *_REGISTRY_VIOLATION_REASONS,
        "0.60",
        "201",
        "0.025",
        "0.05",
    ):
        assert document.count(literal.encode("utf-8")) == mutated.count(
            literal.encode("utf-8")
        )
    with pytest.raises(B4PreregistrationContractError, match="sha256"):
        extract_preregistered_analysis_contract(mutated)


def test_duplicate_h4_or_h5_anchor_fails_closed() -> None:
    document = _document()
    h4 = "#### 5.1.1 分析契約の一括凍結 (D1082)\n".encode("utf-8")
    duplicate_h4 = document.replace(h4, h4 + h4, 1)
    assert duplicate_h4 != document
    with pytest.raises(B4PreregistrationContractError):
        extract_preregistered_analysis_contract(duplicate_h4)

    h5 = "##### n と検定単位\n".encode("utf-8")
    duplicate_h5 = document.replace(h5, h5 + h5, 1)
    assert duplicate_h5 != document
    with pytest.raises(B4PreregistrationContractError):
        extract_preregistered_analysis_contract(duplicate_h5)


def test_fenced_and_html_commented_heading_decoys_are_ignored() -> None:
    document = _document()
    h4 = "#### 5.1.1 分析契約の一括凍結 (D1082)\n".encode("utf-8")
    decoys = (
        "```text\n"
        "#### 5.1.1 分析契約の一括凍結 (D1082)\n"
        "##### n と検定単位\n"
        "```\n"
        "<!--\n"
        "#### 5.1.1 分析契約の一括凍結 (D1082)\n"
        "##### n と検定単位\n"
        "-->\n"
    ).encode("utf-8")
    mutated = _replace_once(document, h4, decoys + h4)
    parsed = extract_preregistered_analysis_contract(mutated)
    assert parsed.section_sha256 == PREREGISTRATION_SECTION_5_1_1_SHA256


def test_missing_section_or_literal_fails_closed() -> None:
    document = _document()
    h4 = "#### 5.1.1 分析契約の一括凍結 (D1082)\n".encode("utf-8")
    missing_section = _replace_once(document, h4, b"")
    with pytest.raises(B4PreregistrationContractError):
        extract_preregistered_analysis_contract(missing_section)

    missing_literal = _replace_once(
        document,
        b"`block_count_mismatch`",
        b"`removed-reason`",
    )
    with pytest.raises(B4PreregistrationContractError):
        extract_preregistered_analysis_contract(missing_literal)


def test_non_utf8_document_fails_closed() -> None:
    document = _document() + b"\xff"
    with pytest.raises(B4PreregistrationContractError, match="UTF-8"):
        extract_preregistered_analysis_contract(document)


def test_contract_constant_derived_from_document_is_not_a_source_literal() -> None:
    source = _CONTRACT_PATH.read_bytes()
    derived = _replace_once(
        source,
        b"EXPECTED_BLOCK_COUNT = 201",
        b"EXPECTED_BLOCK_COUNT = int(PREREGISTRATION_TEXT.split(\"n = \" )[1])",
    )
    ast.parse(derived.decode("utf-8"))
    with pytest.raises(B4PreregistrationContractError, match="derived"):
        assert_contract_constants_are_source_literals(derived)


def test_contract_enum_values_must_be_literal_assignments() -> None:
    source = _CONTRACT_PATH.read_bytes()
    derived = _replace_once(
        source,
        b'BLOCK_COUNT_MISMATCH = "block_count_mismatch"',
        b'BLOCK_COUNT_MISMATCH = str("block_count_mismatch")',
    )
    with pytest.raises(B4PreregistrationContractError, match="derived"):
        assert_contract_constants_are_source_literals(derived)


def test_selection_and_violation_order_behavior_mutations_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Monkeypatch imports to model mutations without a production injection seam.
    Such a seam would itself permit an alternate manifest-generation universe."""

    document = _document()
    original_generate = consumer.ledgers.generate_analysis_manifest

    def last_rows(**kwargs: object):
        manifest = original_generate(**kwargs)
        if isinstance(manifest, consumer.ledgers.B4AnalysisManifest):
            return replace(manifest, rows=tuple(reversed(manifest.rows)))
        return manifest

    with monkeypatch.context() as patch:
        patch.setattr(consumer.ledgers, "generate_analysis_manifest", last_rows)
        with pytest.raises(B4PreregistrationContractError, match="first n"):
            _assert_document(document)

    with monkeypatch.context() as patch:
        patch.setattr(
            consumer.analysis_path,
            "derive_registry_violation_count",
            lambda **_kwargs: 0,
        )
        with pytest.raises(B4PreregistrationContractError, match="violation"):
            _assert_document(document)


def test_behavior_probes_react_only_to_their_owned_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_generate = consumer.ledgers.generate_analysis_manifest
    original_score = consumer.contract.block_score

    def reversed_rows(**kwargs: object):
        manifest = original_generate(**kwargs)
        if isinstance(manifest, consumer.ledgers.B4AnalysisManifest):
            return replace(manifest, rows=tuple(reversed(manifest.rows)))
        return manifest

    def missing_ties_with_middle(block: object, *, floor: object):
        if isinstance(block, consumer.contract.B4BlockObservation):
            statuses = {block.on.status, block.off.status}
            middle = {
                consumer.contract.B4BlockStatus.REJECTED,
                consumer.contract.B4BlockStatus.ABORTED,
            }
            if (
                consumer.contract.B4BlockStatus.MISSING in statuses
                and statuses & middle
            ):
                return Fraction(1, 2)
        return original_score(block, floor=floor)

    with monkeypatch.context() as patch:
        patch.setattr(
            consumer.ledgers,
            "generate_analysis_manifest",
            reversed_rows,
        )
        consumer._assert_rank_and_threshold_behavior()
        consumer._assert_violation_behavior()
        with pytest.raises(B4PreregistrationContractError, match="first n"):
            consumer._assert_selection_behavior()

    with monkeypatch.context() as patch:
        patch.setattr(
            consumer.analysis_path,
            "derive_registry_violation_count",
            lambda **_kwargs: 0,
        )
        consumer._assert_selection_behavior()
        consumer._assert_rank_and_threshold_behavior()
        with pytest.raises(B4PreregistrationContractError, match="violation"):
            consumer._assert_violation_behavior()

    with monkeypatch.context() as patch:
        patch.setattr(consumer.contract, "block_score", missing_ties_with_middle)
        consumer._assert_selection_behavior()
        consumer._assert_violation_behavior()
        with pytest.raises(B4PreregistrationContractError, match="status rank"):
            consumer._assert_rank_and_threshold_behavior()


def test_first_n_and_violation_order_source_mutations_are_rejected() -> None:
    document = _document()
    ledgers_source = _LEDGERS_PATH.read_bytes()
    last_n = _replace_once(
        ledgers_source,
        b"eligible[:EXPECTED_BLOCK_COUNT]",
        b"eligible[-EXPECTED_BLOCK_COUNT:]",
    )
    with pytest.raises(B4PreregistrationContractError, match="first-n"):
        _assert_document(document, ledgers_source_bytes=last_n)

    path_source = _ANALYSIS_PATH.read_bytes()
    bypass = _replace_once(
        path_source,
        b"violation_count = derive_registry_violation_count(",
        b"violation_count = len(",
    )
    ast.parse(bypass.decode("utf-8"))
    with pytest.raises(B4PreregistrationContractError, match="order"):
        _assert_document(document, path_source_bytes=bypass)


def test_missing_source_closure_member_fails_closed(tmp_path: Path) -> None:
    destination_document = (
        tmp_path / "docs/phase3-b4-reflux-ablation-preregistration.md"
    )
    destination_document.parent.mkdir(parents=True)
    destination_document.write_bytes(_document())
    for relative_path in _CLOSURE_PATHS[:-1]:
        destination = tmp_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((_ROOT / relative_path).read_bytes())
    with pytest.raises(B4PreregistrationContractError, match="unreadable"):
        verify_repository_preregistration_contract(repository_root=tmp_path)


def test_receipt_public_route_cannot_run_before_consumer_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assembler_called = False

    def reject_behavior() -> None:
        raise B4PreregistrationContractError("consumer behavior rejected")

    original_assembler = (
        consumer.analysis_path._generate_analysis_source_closure_receipt
    )

    def record_assembler(**kwargs: object):
        nonlocal assembler_called
        assembler_called = True
        return original_assembler(**kwargs)

    monkeypatch.setattr(consumer, "_assert_rank_and_threshold_behavior", reject_behavior)
    monkeypatch.setattr(
        consumer.analysis_path,
        "_generate_analysis_source_closure_receipt",
        record_assembler,
    )

    with pytest.raises(B4PreregistrationContractError, match="behavior rejected"):
        generate_verified_analysis_source_closure_receipt(repository_root=_ROOT)
    assert assembler_called is False


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
