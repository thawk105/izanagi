from fractions import Fraction
import json

import pytest

from orchestrator.campaign.p3_b4_analysis_adapter import (
    RAW_ANALYSIS_SCHEMA_VERSION,
    B4ExecutionDisposition,
    B4RawAnalysisRecords,
    adapt_raw_blocks,
    parse_raw_analysis_records,
)
from orchestrator.campaign.p3_b4_analysis_contract import (
    B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
    EXPECTED_BLOCK_COUNT,
    B4AnalysisInvalid,
    B4AnalysisInvalidReason,
    B4Arm,
    B4BlockStatus,
    B4ContractBinding,
    B4ContractBlockBinding,
    block_score,
    evaluate_analysis,
)


_MANIFEST_HASH = "1" * 64
_REGISTRY_HASH = "2" * 64
_REFERENCE_SNAPSHOT_HASH = "3" * 64
_REFERENCE_RECEIPT_HASH = "4" * 64
_PRECURSOR_HASH = "5" * 64
_SOURCE_ARTIFACT_HASH = "6" * 64


def _block_id(index: int) -> str:
    return f"b4-block-{index:03d}"


def _binding() -> B4ContractBinding:
    return B4ContractBinding(
        schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
        manifest_sha256=_MANIFEST_HASH,
        registry_sha256=_REGISTRY_HASH,
        blocks=tuple(
            B4ContractBlockBinding(
                schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
                block_id=_block_id(index),
                reference_tps=Fraction(1),
                reference_snapshot_hash=_REFERENCE_SNAPSHOT_HASH,
                reference_receipt_hash=_REFERENCE_RECEIPT_HASH,
                assignment_schedule=(B4Arm.ON, B4Arm.OFF),
            )
            for index in range(EXPECTED_BLOCK_COUNT)
        ),
        expected_block_count=EXPECTED_BLOCK_COUNT,
    )


def _raw_arm(arm: str) -> dict[str, object]:
    return {
        "arm": arm,
        "execution_disposition": "executed",
        "whiteboard_result": "success",
        "terminal_stage": "COMMIT",
        "terminal_reason": None,
        "throughput": 1,
        "precursor_hash": _PRECURSOR_HASH,
        "treatment_fired": True,
        "contaminated": False,
        "protocol_ok": True,
        "source_artifact_sha256": _SOURCE_ARTIFACT_HASH,
    }


def _raw_document() -> dict[str, object]:
    return {
        "schema_version": RAW_ANALYSIS_SCHEMA_VERSION,
        "blocks": [
            {
                "block_id": _block_id(index),
                "reference_tps": 1,
                "reference_snapshot_hash": _REFERENCE_SNAPSHOT_HASH,
                "reference_receipt_hash": _REFERENCE_RECEIPT_HASH,
                "assignment_observation": ["on", "off"],
                "arms": [_raw_arm("on"), _raw_arm("off")],
            }
            for index in range(EXPECTED_BLOCK_COUNT)
        ],
    }


def _bytes(document: dict[str, object]) -> bytes:
    return json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _first_block(document: dict[str, object]) -> dict[str, object]:
    blocks = document["blocks"]
    assert isinstance(blocks, list)
    block = blocks[0]
    assert isinstance(block, dict)
    return block


def _first_arm(document: dict[str, object]) -> dict[str, object]:
    block = _first_block(document)
    arms = block["arms"]
    assert isinstance(arms, list)
    arm = arms[0]
    assert isinstance(arm, dict)
    return arm


def _adapt(document: dict[str, object]):
    return adapt_raw_blocks(_bytes(document), contract_binding=_binding())


def _assert_invalid(
    value: object,
    reason: B4AnalysisInvalidReason | None = None,
) -> B4AnalysisInvalid:
    assert isinstance(value, B4AnalysisInvalid)
    if reason is not None:
        assert reason in value.reasons
    return value


def test_decimal_lexical_is_read_exactly_not_via_float() -> None:
    binary_float_excess = (
        abs(Fraction(1.1) - Fraction(1.0)) / Fraction(1.0) - Fraction(0.1)
    )
    assert binary_float_excess == Fraction(3, 36028797018963968)

    document = _raw_document()
    first = _first_block(document)
    arms = first["arms"]
    assert isinstance(arms, list)
    on = arms[0]
    off = arms[1]
    assert isinstance(on, dict)
    assert isinstance(off, dict)
    first["reference_tps"] = 1001
    on["throughput"] = 1101
    off["throughput"] = 1001
    raw = _bytes(document)
    raw = raw.replace(b'"reference_tps":1001', b'"reference_tps":1.0', 1)
    raw = raw.replace(b'"throughput":1101', b'"throughput":1.1', 1)
    raw = raw.replace(b'"throughput":1001', b'"throughput":1.0', 1)

    parsed = parse_raw_analysis_records(raw)
    assert isinstance(parsed, B4RawAnalysisRecords)
    assert parsed.blocks[0].reference_tps == Fraction(1)
    assert parsed.blocks[0].arms[0].throughput == Fraction(11, 10)
    assert parsed.blocks[0].arms[1].throughput == Fraction(1)

    blocks = adapt_raw_blocks(raw, contract_binding=_binding())
    assert isinstance(blocks, tuple)
    assert block_score(blocks[0], floor=Fraction(1, 10)) == Fraction(1, 2)
    result = evaluate_analysis(
        floor=Fraction(1, 10),
        contract_binding=_binding(),
        registry_violation_count=0,
        blocks=blocks,
    )
    assert result.analysis_invalid is None
    assert result.ties == EXPECTED_BLOCK_COUNT
    assert result.a_hat is not None
    assert result.a_hat.value == Fraction(1, 2)


def test_raw_schema_version_and_exact_key_sets_are_closed() -> None:
    mutations = []

    wrong_version = _raw_document()
    wrong_version["schema_version"] = "p3-b4-raw-analysis/v2"
    mutations.append(wrong_version)

    unknown_top = _raw_document()
    unknown_top["extra"] = None
    mutations.append(unknown_top)

    unknown_block = _raw_document()
    _first_block(unknown_block)["extra"] = None
    mutations.append(unknown_block)

    unknown_arm = _raw_document()
    _first_arm(unknown_arm)["extra"] = None
    mutations.append(unknown_arm)

    for mutation in mutations:
        _assert_invalid(
            parse_raw_analysis_records(_bytes(mutation)),
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED,
        )


def test_raw_schema_rejects_missing_unknown_and_non_boolean_fields() -> None:
    missing = _raw_document()
    del _first_block(missing)["block_id"]
    _assert_invalid(
        parse_raw_analysis_records(_bytes(missing)),
        B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED,
    )

    unknown = _raw_document()
    _first_arm(unknown)["not_in_schema"] = False
    _assert_invalid(
        parse_raw_analysis_records(_bytes(unknown)),
        B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED,
    )

    for field in ("treatment_fired", "contaminated", "protocol_ok"):
        non_boolean = _raw_document()
        _first_arm(non_boolean)[field] = 1
        _assert_invalid(
            parse_raw_analysis_records(_bytes(non_boolean)),
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED,
        )


def test_duplicate_maps_to_missing_even_with_success_whiteboard() -> None:
    document = _raw_document()
    arm = _first_arm(document)
    arm["execution_disposition"] = "duplicate"
    arm["whiteboard_result"] = "success"
    arm["terminal_stage"] = "COMMIT"
    arm["throughput"] = 99

    blocks = _adapt(document)
    assert isinstance(blocks, tuple)
    assert blocks[0].on.status is B4BlockStatus.MISSING
    assert blocks[0].on.throughput is None


@pytest.mark.parametrize(
    "disposition",
    [
        "dry-pass",
        "stopped-before",
        "crash",
        "terminal-record-absent",
    ],
)
def test_dry_pass_stop_crash_and_absent_terminal_map_to_missing(
    disposition: str,
) -> None:
    document = _raw_document()
    arm = _first_arm(document)
    arm["execution_disposition"] = disposition
    arm["whiteboard_result"] = None
    arm["terminal_stage"] = None
    arm["terminal_reason"] = None
    arm["throughput"] = None

    blocks = _adapt(document)
    assert isinstance(blocks, tuple)
    assert blocks[0].on.status is B4BlockStatus.MISSING


def test_executed_success_commit_maps_to_certified() -> None:
    blocks = _adapt(_raw_document())
    assert isinstance(blocks, tuple)
    assert blocks[0].on.status is B4BlockStatus.CERTIFIED
    assert blocks[0].on.throughput == Fraction(1)


def test_executed_diff_quarantine_maps_to_rejected() -> None:
    document = _raw_document()
    arm = _first_arm(document)
    arm["whiteboard_result"] = "rejected"
    arm["terminal_stage"] = "ABORT"
    arm["terminal_reason"] = "diff-quarantine"
    arm["throughput"] = None

    blocks = _adapt(document)
    assert isinstance(blocks, tuple)
    assert blocks[0].on.status is B4BlockStatus.REJECTED


def test_executed_other_abort_maps_to_aborted() -> None:
    document = _raw_document()
    arm = _first_arm(document)
    arm["whiteboard_result"] = "fail"
    arm["terminal_stage"] = "ABORT"
    arm["terminal_reason"] = "budget-exhausted"
    arm["throughput"] = None

    blocks = _adapt(document)
    assert isinstance(blocks, tuple)
    assert blocks[0].on.status is B4BlockStatus.ABORTED


def test_inconsistent_whiteboard_terminal_pair_fails_closed() -> None:
    document = _raw_document()
    arm = _first_arm(document)
    arm["whiteboard_result"] = "rejected"
    arm["terminal_stage"] = "COMMIT"
    arm["terminal_reason"] = None
    arm["throughput"] = None

    _assert_invalid(
        _adapt(document),
        B4AnalysisInvalidReason.STATUS_DOMAIN_ERROR,
    )


@pytest.mark.parametrize(
    ("scope", "field", "value"),
    [
        ("arm", "arm", "sideways"),
        ("arm", "execution_disposition", "future-disposition"),
        ("arm", "whiteboard_result", "future-result"),
        ("arm", "terminal_stage", "FUTURE"),
        ("block", "assignment_observation", ["on", "sideways"]),
    ],
)
def test_non_status_enum_errors_use_the_ill_typed_catchall(
    scope: str,
    field: str,
    value: object,
) -> None:
    document = _raw_document()
    target = _first_arm(document) if scope == "arm" else _first_block(document)
    target[field] = value

    invalid = _assert_invalid(_adapt(document))
    assert invalid.reasons == (
        B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED,
    )


def test_adapter_never_drops_a_missing_block() -> None:
    document = _raw_document()
    arm = _first_arm(document)
    arm["execution_disposition"] = "crash"
    arm["whiteboard_result"] = None
    arm["terminal_stage"] = None
    arm["terminal_reason"] = None
    arm["throughput"] = None

    blocks = _adapt(document)
    assert isinstance(blocks, tuple)
    assert len(blocks) == EXPECTED_BLOCK_COUNT
    assert tuple(block.block_id for block in blocks) == tuple(
        _block_id(index) for index in range(EXPECTED_BLOCK_COUNT)
    )
    assert blocks[0].on.status is B4BlockStatus.MISSING


@pytest.mark.parametrize(
    ("scope", "field"),
    [
        ("arm", "treatment_fired"),
        ("arm", "contaminated"),
        ("arm", "protocol_ok"),
        ("arm", "precursor_hash"),
        ("block", "reference_snapshot_hash"),
        ("block", "reference_receipt_hash"),
        ("block", "assignment_observation"),
        ("arm", "execution_disposition"),
    ],
)
def test_adapter_requires_all_currently_unproduced_fields(
    scope: str,
    field: str,
) -> None:
    document = _raw_document()
    target = _first_arm(document) if scope == "arm" else _first_block(document)
    del target[field]

    _assert_invalid(
        _adapt(document),
        B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED,
    )


@pytest.mark.parametrize(
    "malformed",
    [
        b"{",
        b'{"schema_version":"p3-b4-raw-analysis/v1","blocks":NaN}',
        {"schema_version": RAW_ANALYSIS_SCHEMA_VERSION, "blocks": []},
    ],
)
def test_adapter_failure_is_returned_as_analysis_invalid_not_raised(
    malformed: object,
) -> None:
    result = adapt_raw_blocks(malformed, contract_binding=_binding())
    _assert_invalid(result)


def test_execution_slot_order_is_compared_not_assumed() -> None:
    document = _raw_document()
    _first_block(document)["assignment_observation"] = ["off", "on"]

    blocks = _adapt(document)
    assert isinstance(blocks, tuple)
    assert blocks[0].assignment_followed is False
    assert all(block.assignment_followed for block in blocks[1:])


def test_unknown_block_id_is_returned_as_analysis_invalid() -> None:
    document = _raw_document()
    _first_block(document)["block_id"] = "not-in-the-frozen-binding"

    _assert_invalid(
        _adapt(document),
        B4AnalysisInvalidReason.UNKNOWN_BLOCK_ID,
    )


def test_execution_disposition_vocabulary_is_exact() -> None:
    assert tuple(member.value for member in B4ExecutionDisposition) == (
        "executed",
        "duplicate",
        "dry-pass",
        "stopped-before",
        "crash",
        "terminal-record-absent",
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
