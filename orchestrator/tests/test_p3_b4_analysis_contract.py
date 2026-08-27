from dataclasses import fields, replace
from fractions import Fraction

import pytest

from orchestrator.campaign import p3_b4_analysis_contract as contract
from orchestrator.campaign.p3_b4_analysis_contract import (
    A_MIN,
    B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
    EXPECTED_BLOCK_COUNT,
    ONE_SIDED_ALPHA,
    B4AnalysisInvalid,
    B4AnalysisInvalidReason,
    B4AnalysisResult,
    B4Arm,
    B4ArmObservation,
    B4BlockObservation,
    B4BlockStatus,
    B4ContractBinding,
    B4ContractBlockBinding,
    B4RegistryViolationReason,
    B4ThetaRootOutwardEnclosure,
    B4Verdict,
    block_score,
    clopper_pearson_theta_95,
    evaluate_analysis,
    exact_sign_pvalues,
    validate_analysis_inputs,
)


SCHEMA = B4_ANALYSIS_CONTRACT_SCHEMA_VERSION
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


def _arm(
    *,
    status: object = B4BlockStatus.CERTIFIED,
    throughput: object = Fraction(1),
    precursor_hash: object = HASH_A,
    treatment_fired: object = True,
    contaminated: object = False,
    protocol_ok: object = True,
) -> B4ArmObservation:
    return B4ArmObservation(
        schema_version=SCHEMA,
        precursor_hash=precursor_hash,
        status=status,
        throughput=throughput,
        treatment_fired=treatment_fired,
        contaminated=contaminated,
        protocol_ok=protocol_ok,
    )


def _score_arms(score: str) -> tuple[B4ArmObservation, B4ArmObservation]:
    if score == "on":
        return _arm(throughput=Fraction(2)), _arm(throughput=Fraction(1))
    if score == "off":
        return _arm(throughput=Fraction(1)), _arm(throughput=Fraction(2))
    if score == "tie":
        return _arm(), _arm()
    raise AssertionError(f"unknown test score: {score}")


def _valid_case(
    scores: list[str] | None = None,
) -> dict[str, object]:
    score_values = scores or ["tie"] * EXPECTED_BLOCK_COUNT
    assert len(score_values) == EXPECTED_BLOCK_COUNT
    bindings: list[B4ContractBlockBinding] = []
    blocks: list[B4BlockObservation] = []
    for index, score in enumerate(score_values):
        block_id = f"block-{index:03d}"
        bindings.append(
            B4ContractBlockBinding(
                schema_version=SCHEMA,
                block_id=block_id,
                reference_tps=Fraction(1),
                reference_snapshot_hash=HASH_B,
                reference_receipt_hash=HASH_C,
                assignment_schedule=(B4Arm.ON, B4Arm.OFF),
            )
        )
        on, off = _score_arms(score)
        blocks.append(
            B4BlockObservation(
                schema_version=SCHEMA,
                block_id=block_id,
                reference_tps=Fraction(1),
                reference_snapshot_hash=HASH_B,
                reference_receipt_hash=HASH_C,
                assignment_followed=True,
                on=on,
                off=off,
            )
        )
    return {
        "floor": Fraction(1, 10),
        "contract_binding": B4ContractBinding(
            schema_version=SCHEMA,
            manifest_sha256=HASH_A,
            registry_sha256=HASH_D,
            blocks=tuple(bindings),
            expected_block_count=EXPECTED_BLOCK_COUNT,
        ),
        "registry_violation_count": 0,
        "blocks": tuple(blocks),
    }


def _replace_block(
    case: dict[str, object],
    index: int,
    block: B4BlockObservation,
) -> dict[str, object]:
    updated = dict(case)
    blocks = list(case["blocks"])
    blocks[index] = block
    updated["blocks"] = tuple(blocks)
    return updated


@pytest.fixture
def invalid_block_count_mismatch() -> dict[str, object]:
    case = _valid_case()
    case["blocks"] = case["blocks"][:-1]
    return case


@pytest.fixture
def invalid_duplicate_block_id() -> dict[str, object]:
    case = _valid_case()
    blocks = case["blocks"]
    return _replace_block(case, 1, replace(blocks[1], block_id=blocks[0].block_id))


@pytest.fixture
def invalid_unknown_block_id() -> dict[str, object]:
    case = _valid_case()
    blocks = case["blocks"]
    return _replace_block(case, 0, replace(blocks[0], block_id="unknown-block"))


@pytest.fixture
def invalid_precursor_hash_mismatch() -> dict[str, object]:
    case = _valid_case()
    block = case["blocks"][0]
    return _replace_block(
        case,
        0,
        replace(block, off=replace(block.off, precursor_hash=HASH_D)),
    )


@pytest.fixture
def invalid_reference_binding_mismatch() -> dict[str, object]:
    case = _valid_case()
    block = case["blocks"][0]
    return _replace_block(
        case,
        0,
        replace(block, reference_snapshot_hash=HASH_D),
    )


@pytest.fixture
def invalid_reference_value_domain_error() -> dict[str, object]:
    case = _valid_case()
    block = case["blocks"][0]
    return _replace_block(case, 0, replace(block, reference_tps=Fraction(0)))


@pytest.fixture
def invalid_status_domain_error() -> dict[str, object]:
    case = _valid_case()
    block = case["blocks"][0]
    return _replace_block(
        case,
        0,
        replace(block, on=replace(block.on, status="certified")),
    )


@pytest.fixture
def invalid_throughput_contract_error() -> dict[str, object]:
    case = _valid_case()
    block = case["blocks"][0]
    return _replace_block(
        case,
        0,
        replace(block, on=replace(block.on, throughput=None)),
    )


@pytest.fixture
def invalid_floor_domain_error() -> dict[str, object]:
    case = _valid_case()
    case["floor"] = 0.1
    return case


@pytest.fixture
def invalid_violation_count_domain_error() -> dict[str, object]:
    case = _valid_case()
    case["registry_violation_count"] = -1
    return case


@pytest.fixture
def invalid_binding_domain_error() -> dict[str, object]:
    case = _valid_case()
    binding = case["contract_binding"]
    case["contract_binding"] = replace(binding, manifest_sha256="not-a-sha256")
    return case


@pytest.fixture
def invalid_field_missing_or_ill_typed() -> dict[str, object]:
    case = _valid_case()
    block = case["blocks"][0]
    return _replace_block(
        case,
        0,
        replace(block, on=replace(block.on, protocol_ok=1)),
    )


INVALID_FIXTURES = (
    ("invalid_block_count_mismatch", B4AnalysisInvalidReason.BLOCK_COUNT_MISMATCH),
    ("invalid_duplicate_block_id", B4AnalysisInvalidReason.DUPLICATE_BLOCK_ID),
    ("invalid_unknown_block_id", B4AnalysisInvalidReason.UNKNOWN_BLOCK_ID),
    (
        "invalid_precursor_hash_mismatch",
        B4AnalysisInvalidReason.PRECURSOR_HASH_MISMATCH,
    ),
    (
        "invalid_reference_binding_mismatch",
        B4AnalysisInvalidReason.REFERENCE_BINDING_MISMATCH,
    ),
    (
        "invalid_reference_value_domain_error",
        B4AnalysisInvalidReason.REFERENCE_VALUE_DOMAIN_ERROR,
    ),
    ("invalid_status_domain_error", B4AnalysisInvalidReason.STATUS_DOMAIN_ERROR),
    (
        "invalid_throughput_contract_error",
        B4AnalysisInvalidReason.THROUGHPUT_CONTRACT_ERROR,
    ),
    ("invalid_floor_domain_error", B4AnalysisInvalidReason.FLOOR_DOMAIN_ERROR),
    (
        "invalid_violation_count_domain_error",
        B4AnalysisInvalidReason.VIOLATION_COUNT_DOMAIN_ERROR,
    ),
    ("invalid_binding_domain_error", B4AnalysisInvalidReason.BINDING_DOMAIN_ERROR),
    (
        "invalid_field_missing_or_ill_typed",
        B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED,
    ),
)


@pytest.mark.parametrize(
    ("fixture_name", "expected_reason"),
    INVALID_FIXTURES,
    ids=[name.removeprefix("invalid_") for name, _ in INVALID_FIXTURES],
)
def test_each_analysis_invalid_reason_fires_alone(
    request: pytest.FixtureRequest,
    fixture_name: str,
    expected_reason: B4AnalysisInvalidReason,
) -> None:
    case = request.getfixturevalue(fixture_name)
    invalid = validate_analysis_inputs(**case)
    assert isinstance(invalid, B4AnalysisInvalid)
    assert invalid.reasons == (expected_reason,)


def test_analysis_invalid_reason_enum_is_exact() -> None:
    assert [reason.value for reason in B4AnalysisInvalidReason] == [
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
    ]


def test_registry_violation_reason_enum_is_exact() -> None:
    assert [reason.value for reason in B4RegistryViolationReason] == [
        "arm_digest_contaminated_precursor",
        "assignment_schedule_violated",
        "arm_asymmetric_gate",
        "env_tag_mismatch",
        "manifest_mutated_after_freeze",
    ]


def test_all_public_wire_dataclasses_require_schema_version() -> None:
    wire_types = [
        value
        for name, value in vars(contract).items()
        if name.startswith("B4")
        and isinstance(value, type)
        and hasattr(value, "__dataclass_fields__")
    ]
    assert wire_types
    for wire_type in wire_types:
        schema_field = next(field for field in fields(wire_type) if field.name == "schema_version")
        assert schema_field.default is schema_field.default_factory


def test_public_contract_types_are_b4_prefixed() -> None:
    local_types = {
        name
        for name, value in vars(contract).items()
        if isinstance(value, type) and value.__module__ == contract.__name__
    }
    assert local_types
    assert all(name.startswith("B4") for name in local_types)


def test_certified_gain_boundary_is_inclusive_tie() -> None:
    block = _valid_case()["blocks"][0]
    boundary = replace(
        block,
        on=replace(block.on, throughput=Fraction(11, 10)),
        off=replace(block.off, throughput=Fraction(1)),
    )
    outside = replace(boundary, on=replace(boundary.on, throughput=Fraction(111, 100)))
    assert block_score(boundary, floor=Fraction(1, 10)) == Fraction(1, 2)
    assert block_score(outside, floor=Fraction(1, 10)) == Fraction(1)


@pytest.mark.parametrize("other_status", [B4BlockStatus.REJECTED, B4BlockStatus.ABORTED, B4BlockStatus.MISSING])
def test_certified_outranks_every_non_certified_status(
    other_status: B4BlockStatus,
) -> None:
    block = _valid_case()["blocks"][0]
    certified = _arm(status=B4BlockStatus.CERTIFIED, throughput=Fraction(1, 1000))
    other = _arm(status=other_status, throughput=None)
    assert block_score(replace(block, on=certified, off=other), floor=Fraction(9, 10)) == 1
    assert block_score(replace(block, on=other, off=certified), floor=Fraction(9, 10)) == 0


def test_missing_is_not_excluded_and_loses_to_rejected() -> None:
    block = _valid_case()["blocks"][0]
    missing = _arm(status=B4BlockStatus.MISSING, throughput=None)
    rejected = _arm(status=B4BlockStatus.REJECTED, throughput=None)
    assert block_score(replace(block, on=missing, off=rejected), floor=Fraction(1, 10)) == 0
    assert block_score(replace(block, on=rejected, off=missing), floor=Fraction(1, 10)) == 1


def test_missing_against_missing_has_exact_half_score() -> None:
    block = _valid_case()["blocks"][0]
    missing = _arm(status=B4BlockStatus.MISSING, throughput=None)

    assert (
        block_score(
            replace(block, on=missing, off=missing),
            floor=Fraction(1, 10),
        )
        == Fraction(1, 2)
    )


def test_missing_does_not_tie_rejected_or_aborted() -> None:
    block = _valid_case()["blocks"][0]
    missing = _arm(status=B4BlockStatus.MISSING, throughput=None)
    for middle_status in (B4BlockStatus.REJECTED, B4BlockStatus.ABORTED):
        middle = _arm(status=middle_status, throughput=None)
        scores = {
            block_score(replace(block, on=missing, off=middle), floor=Fraction(1, 10)),
            block_score(replace(block, on=middle, off=missing), floor=Fraction(1, 10)),
        }
        assert scores == {Fraction(0), Fraction(1)}


def test_rejected_and_aborted_are_always_tied() -> None:
    block = _valid_case()["blocks"][0]
    rejected = _arm(status=B4BlockStatus.REJECTED, throughput=None)
    aborted = _arm(status=B4BlockStatus.ABORTED, throughput=None)
    assert block_score(replace(block, on=rejected, off=aborted), floor=Fraction(0)) == Fraction(1, 2)
    assert block_score(replace(block, on=aborted, off=rejected), floor=Fraction(0)) == Fraction(1, 2)


def test_float_inputs_are_analysis_invalid_domain_errors() -> None:
    floor_case = _valid_case()
    floor_case["floor"] = 0.1
    floor_result = evaluate_analysis(**floor_case)
    assert floor_result.analysis_invalid is not None
    assert floor_result.analysis_invalid.reasons == (
        B4AnalysisInvalidReason.FLOOR_DOMAIN_ERROR,
    )

    throughput_case = _valid_case()
    block = throughput_case["blocks"][0]
    throughput_case = _replace_block(
        throughput_case,
        0,
        replace(block, on=replace(block.on, throughput=1.1)),
    )
    throughput_result = evaluate_analysis(**throughput_case)
    assert throughput_result.analysis_invalid is not None
    assert throughput_result.analysis_invalid.reasons == (
        B4AnalysisInvalidReason.THROUGHPUT_CONTRACT_ERROR,
    )

    reference_case = _valid_case()
    reference_block = reference_case["blocks"][0]
    reference_case = _replace_block(
        reference_case,
        0,
        replace(reference_block, reference_tps=1.0),
    )
    reference_result = evaluate_analysis(**reference_case)
    assert reference_result.analysis_invalid is not None
    assert reference_result.analysis_invalid.reasons == (
        B4AnalysisInvalidReason.REFERENCE_VALUE_DOMAIN_ERROR,
    )


def test_exact_integer_ratio_is_accepted_without_float_conversion() -> None:
    case = _valid_case()
    case["floor"] = (1, 10)
    block = case["blocks"][0]
    case = _replace_block(
        case,
        0,
        replace(
            block,
            reference_tps=(1, 1),
            on=replace(block.on, throughput=(1, 1)),
            off=replace(block.off, throughput=(1, 1)),
        ),
    )
    assert not isinstance(validate_analysis_inputs(**case), B4AnalysisInvalid)


def test_every_observed_reference_field_is_compared_inside_pure_function() -> None:
    base = _valid_case()
    block = base["blocks"][0]
    mutations = (
        replace(block, reference_tps=Fraction(2)),
        replace(block, reference_snapshot_hash=HASH_D),
        replace(block, reference_receipt_hash=HASH_D),
    )
    for mutation in mutations:
        case = _replace_block(base, 0, mutation)
        invalid = validate_analysis_inputs(**case)
        assert isinstance(invalid, B4AnalysisInvalid)
        assert invalid.reasons == (
            B4AnalysisInvalidReason.REFERENCE_BINDING_MISMATCH,
        )


def test_ledger_hash_values_are_not_compared_without_observed_artifact_bytes() -> None:
    case = _valid_case()
    binding = case["contract_binding"]
    case["contract_binding"] = replace(
        binding,
        manifest_sha256=HASH_B,
        registry_sha256=HASH_C,
    )
    assert not isinstance(validate_analysis_inputs(**case), B4AnalysisInvalid)


def test_a_hat_is_sample_ahat_with_exact_fraction() -> None:
    result = evaluate_analysis(
        **_valid_case(["on"] * 6 + ["off"] * 4 + ["tie"] * 191)
    )
    assert result.a_hat is not None
    assert result.a_hat.value == Fraction(2 * 6 + 191, 2 * 201)
    assert isinstance(result.a_hat.value, Fraction)


def test_exact_sign_pvalues_use_integer_binomial_tails_at_m201() -> None:
    all_on = exact_sign_pvalues(on_wins=201, non_ties=201)
    all_off = exact_sign_pvalues(on_wins=0, non_ties=201)
    assert all_on.p_on == Fraction(1, 1 << 201)
    assert all_on.p_off == 1
    assert all_off.p_on == 1
    assert all_off.p_off == Fraction(1, 1 << 201)


def test_clopper_pearson_brackets_both_exact_binomial_roots() -> None:
    zero_wins = clopper_pearson_theta_95(on_wins=0, non_ties=2)
    upper_low, upper_high = zero_wins.upper_root_bracket
    assert (1 - upper_low) ** 2 >= ONE_SIDED_ALPHA
    assert (1 - upper_high) ** 2 <= ONE_SIDED_ALPHA
    assert zero_wins.upper == upper_high
    assert upper_high - upper_low == Fraction(1, 1 << 80)

    all_wins = clopper_pearson_theta_95(on_wins=2, non_ties=2)
    lower_low, lower_high = all_wins.lower_root_bracket
    assert lower_low**2 <= ONE_SIDED_ALPHA
    assert lower_high**2 >= ONE_SIDED_ALPHA
    assert all_wins.lower == lower_low
    assert lower_high - lower_low == Fraction(1, 1 << 80)


def test_clopper_pearson_m_zero_is_unestimable_zero_one() -> None:
    interval = clopper_pearson_theta_95(on_wins=0, non_ties=0)
    assert isinstance(interval, B4ThetaRootOutwardEnclosure)
    assert (interval.lower, interval.upper) == (Fraction(0), Fraction(1))
    assert interval.lower_root_bracket == (Fraction(0), Fraction(0))
    assert interval.upper_root_bracket == (Fraction(1), Fraction(1))
    assert interval.theta_estimable is False
    assert interval.bisection_steps == 0


def test_validate_analysis_inputs_reports_all_reasons_before_verdict() -> None:
    case = _valid_case()
    case["floor"] = 0.1
    case["registry_violation_count"] = -1
    case["blocks"] = case["blocks"][:-1]
    result = evaluate_analysis(**case)
    assert result.verdict is B4Verdict.PROTOCOL_VIOLATION
    assert result.analysis_invalid is not None
    assert result.analysis_invalid.reasons == (
        B4AnalysisInvalidReason.BLOCK_COUNT_MISMATCH,
        B4AnalysisInvalidReason.FLOOR_DOMAIN_ERROR,
        B4AnalysisInvalidReason.VIOLATION_COUNT_DOMAIN_ERROR,
    )
    assert result.a_hat is None
    assert result.p_values is None
    assert result.theta_interval is None


def test_evaluate_analysis_does_not_call_validated_branch_for_invalid_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(_: object) -> None:
        raise AssertionError("verdict branch ran before validation completed")

    monkeypatch.setattr(contract, "_evaluate_validated_analysis", forbidden)
    case = _valid_case()
    case["floor"] = 0.1
    result = contract.evaluate_analysis(**case)
    assert result.analysis_invalid is not None


def test_registry_violation_count_forces_protocol_violation() -> None:
    case = _valid_case(["on"] * 201)
    case["registry_violation_count"] = 1
    result = evaluate_analysis(**case)
    assert result.p_values is not None and result.p_values.p_on <= ONE_SIDED_ALPHA
    assert result.verdict is B4Verdict.PROTOCOL_VIOLATION


def test_protocol_violation_precedes_contamination() -> None:
    case = _valid_case(["on"] * 201)
    block = case["blocks"][0]
    case = _replace_block(
        case,
        0,
        replace(
            block,
            assignment_followed=False,
            on=replace(block.on, contaminated=True),
        ),
    )
    result = evaluate_analysis(**case)
    assert result.verdict is B4Verdict.PROTOCOL_VIOLATION


def test_contamination_precedes_treatment_count_shortage() -> None:
    case = _valid_case()
    block = case["blocks"][0]
    case = _replace_block(
        case,
        0,
        replace(
            block,
            on=replace(block.on, contaminated=True, treatment_fired=False),
        ),
    )
    result = evaluate_analysis(**case)
    assert result.verdict is B4Verdict.INDETERMINATE
    assert result.a_hat is not None


def test_evaluate_analysis_establishes_below_a_min_when_p_on_is_significant() -> None:
    result = evaluate_analysis(
        **_valid_case(["on"] * 6 + ["tie"] * 195)
    )
    assert result.p_values is not None
    assert result.a_hat is not None
    assert result.p_values.p_on == Fraction(1, 64) <= Fraction(1, 40)
    assert result.a_hat.value == Fraction(69, 134) < A_MIN
    assert result.verdict is B4Verdict.ESTABLISHED
    assert result.effect_below_a_min is True


def test_every_valid_input_reaches_one_verdict() -> None:
    cases: list[dict[str, object]] = []

    protocol = _valid_case(["on"] * 201)
    protocol["registry_violation_count"] = 1
    cases.append(protocol)

    contaminated = _valid_case()
    contaminated_block = contaminated["blocks"][0]
    cases.append(
        _replace_block(
            contaminated,
            0,
            replace(
                contaminated_block,
                on=replace(contaminated_block.on, contaminated=True),
            ),
        )
    )

    treatment_short = _valid_case()
    treatment_block = treatment_short["blocks"][0]
    cases.append(
        _replace_block(
            treatment_short,
            0,
            replace(
                treatment_block,
                off=replace(treatment_block.off, treatment_fired=False),
            ),
        )
    )
    cases.append(_valid_case(["on"] * 6 + ["tie"] * 195))
    cases.append(_valid_case(["off"] * 6 + ["tie"] * 195))
    cases.append(_valid_case())

    observed = [evaluate_analysis(**case) for case in cases]
    assert all(isinstance(result, B4AnalysisResult) for result in observed)
    assert [result.verdict for result in observed] == [
        B4Verdict.PROTOCOL_VIOLATION,
        B4Verdict.INDETERMINATE,
        B4Verdict.INDETERMINATE,
        B4Verdict.ESTABLISHED,
        B4Verdict.NOT_ESTABLISHED,
        B4Verdict.INDETERMINATE,
    ]


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
