"""Pure, exact B-4 analysis contract.

The four inputs to :func:`evaluate_analysis` are the only observations used here.
This module validates every observable binding inside those inputs: block ids and
count, each reference value and its two source hashes, assignment compliance, and
the registry violation count.  ``manifest_sha256`` and ``registry_sha256`` have no
observed counterpart among the four inputs, so this module validates their domain
but deliberately does not compare them.  The artifact integration unit must
recompute and compare both hashes from the actual bytes.

All contract numbers are exact rational values.  Public analysis entry points
accept ``Fraction``, exact integers, or explicit ``(numerator, denominator)``
integer ratios.  They reject ``float`` values as ``analysis_invalid`` domain
errors; decimal lexical conversion belongs to the adapter.

The implementation is pure: it does not read files, clocks, environment state,
randomness, networks, models, or mutable process state.

``evaluate_analysis`` remains a public pure function because the frozen prose
defines that function independently of artifact integration.  The repository
tests pin its production caller inventory to the artifact integration path; this
does not make direct Python calls impossible, and no downstream acceptance point
exists in this unit to distinguish their results.
"""

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from math import comb
from typing import TypeAlias


B4_ANALYSIS_CONTRACT_SCHEMA_VERSION = "p3-b4-analysis-contract/v1"
EXPECTED_BLOCK_COUNT = 201
A_MIN = Fraction(3, 5)
ONE_SIDED_ALPHA = Fraction(1, 40)
TWO_SIDED_ALPHA = Fraction(1, 20)
TEST_UNIT = "block"
_ROOT_BISECTION_STEPS = 80


class B4AnalysisInvalidReason(str, Enum):
    """Closed wire vocabulary for invalid B-4 analysis inputs."""

    BLOCK_COUNT_MISMATCH = "block_count_mismatch"
    DUPLICATE_BLOCK_ID = "duplicate_block_id"
    UNKNOWN_BLOCK_ID = "unknown_block_id"
    PRECURSOR_HASH_MISMATCH = "precursor_hash_mismatch"
    REFERENCE_BINDING_MISMATCH = "reference_binding_mismatch"
    REFERENCE_VALUE_DOMAIN_ERROR = "reference_value_domain_error"
    STATUS_DOMAIN_ERROR = "status_domain_error"
    THROUGHPUT_CONTRACT_ERROR = "throughput_contract_error"
    FLOOR_DOMAIN_ERROR = "floor_domain_error"
    VIOLATION_COUNT_DOMAIN_ERROR = "violation_count_domain_error"
    BINDING_DOMAIN_ERROR = "binding_domain_error"
    FIELD_MISSING_OR_ILL_TYPED = "field_missing_or_ill_typed"


class B4RegistryViolationReason(str, Enum):
    """Closed wire vocabulary for registry protocol violations."""

    ARM_DIGEST_CONTAMINATED_PRECURSOR = "arm_digest_contaminated_precursor"
    ASSIGNMENT_SCHEDULE_VIOLATED = "assignment_schedule_violated"
    ARM_ASYMMETRIC_GATE = "arm_asymmetric_gate"
    ENV_TAG_MISMATCH = "env_tag_mismatch"
    MANIFEST_MUTATED_AFTER_FREEZE = "manifest_mutated_after_freeze"


class B4Arm(str, Enum):
    """B-4 treatment arm identity."""

    ON = "on"
    OFF = "off"


class B4BlockStatus(str, Enum):
    """Closed B-4 block status vocabulary."""

    CERTIFIED = "certified"
    REJECTED = "rejected"
    ABORTED = "aborted"
    MISSING = "missing"


class B4Verdict(str, Enum):
    """The four exhaustive B-4 report classifications."""

    ESTABLISHED = "established"
    NOT_ESTABLISHED = "not_established"
    INDETERMINATE = "indeterminate"
    PROTOCOL_VIOLATION = "protocol_violation"


B4ExactRatio: TypeAlias = Fraction | int | tuple[int, int]


@dataclass(frozen=True, slots=True)
class B4SampleAHat:
    """Exact sample estimate of probability superiority; never population A."""

    schema_version: str
    value: Fraction


@dataclass(frozen=True, slots=True)
class B4ArmObservation:
    """One arm observation retained for a B-4 block."""

    schema_version: str
    precursor_hash: str
    status: B4BlockStatus
    throughput: B4ExactRatio | None
    treatment_fired: bool
    contaminated: bool
    protocol_ok: bool


@dataclass(frozen=True, slots=True)
class B4BlockObservation:
    """The complete paired observation for one manifest block."""

    schema_version: str
    block_id: str
    reference_tps: B4ExactRatio
    reference_snapshot_hash: str
    reference_receipt_hash: str
    assignment_followed: bool
    on: B4ArmObservation
    off: B4ArmObservation


@dataclass(frozen=True, slots=True)
class B4ContractBlockBinding:
    """Frozen expected reference and execution order for one B-4 block."""

    schema_version: str
    block_id: str
    reference_tps: B4ExactRatio
    reference_snapshot_hash: str
    reference_receipt_hash: str
    assignment_schedule: tuple[B4Arm, B4Arm]


@dataclass(frozen=True, slots=True)
class B4ContractBinding:
    """Frozen B-4 manifest and registry binding supplied to the pure contract."""

    schema_version: str
    manifest_sha256: str
    registry_sha256: str
    blocks: tuple[B4ContractBlockBinding, ...]
    expected_block_count: int


@dataclass(frozen=True, slots=True)
class B4AnalysisInvalid:
    """All detected input-contract failures, in closed-enum order."""

    schema_version: str
    reasons: tuple[B4AnalysisInvalidReason, ...]


@dataclass(frozen=True, slots=True)
class B4ExactSignPValues:
    """Exact rational tails of the symmetric sign-test distribution."""

    schema_version: str
    on_wins: int
    non_ties: int
    p_on: Fraction
    p_off: Fraction


@dataclass(frozen=True, slots=True)
class B4ThetaRootOutwardEnclosure:
    """Outward rational enclosure of the two Clopper-Pearson roots.

    ``lower`` and ``upper`` are conservative rational reporting bounds, not the
    generally irrational Clopper-Pearson endpoints themselves.  Each root bracket
    encloses its exact root; the reported lower bound takes the lower side of the
    lower-root bracket and the reported upper bound takes the upper side of the
    upper-root bracket, so the nominal coverage is never narrowed.
    """

    schema_version: str
    lower: Fraction
    upper: Fraction
    lower_root_bracket: tuple[Fraction, Fraction]
    upper_root_bracket: tuple[Fraction, Fraction]
    theta_estimable: bool
    bisection_steps: int


@dataclass(frozen=True, slots=True)
class B4ValidatedAnalysis:
    """Validated four-input bundle; only this type may enter verdict evaluation."""

    schema_version: str
    floor: Fraction
    contract_binding: B4ContractBinding
    registry_violation_count: int
    blocks: tuple[B4BlockObservation, ...]


@dataclass(frozen=True, slots=True)
class B4AnalysisResult:
    """Total B-4 verdict and its exact analysis details."""

    schema_version: str
    verdict: B4Verdict
    analysis_invalid: B4AnalysisInvalid | None
    a_hat: B4SampleAHat | None
    ties: int | None
    m: int | None
    on_wins: int | None
    p_values: B4ExactSignPValues | None
    theta_interval: B4ThetaRootOutwardEnclosure | None
    effect_below_a_min: bool


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_block_id(value: object) -> bool:
    return type(value) is str and bool(value) and value.strip() == value


def as_b4_exact_fraction(value: object) -> Fraction | None:
    """Return an exact B-4 ratio without widening the accepted value domain.

    ``bool``, ``float``, ``Decimal``, zero-denominator ratios, and objects that
    merely offer numeric coercions are rejected.  This is the single conversion
    authority shared by the contract, adapter, and artifact integration path.
    """

    if type(value) is int:
        return Fraction(value)
    if isinstance(value, Fraction):
        return value
    if (
        type(value) is tuple
        and len(value) == 2
        and type(value[0]) is int
        and type(value[1]) is int
        and value[1] != 0
    ):
        return Fraction(value[0], value[1])
    return None


def _invalid(
    reasons: set[B4AnalysisInvalidReason] | tuple[B4AnalysisInvalidReason, ...],
) -> B4AnalysisInvalid:
    reason_set = set(reasons)
    return B4AnalysisInvalid(
        schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
        reasons=tuple(reason for reason in B4AnalysisInvalidReason if reason in reason_set),
    )


def b4_binding_domain_is_valid(binding: object) -> bool:
    """Return whether a contract binding is in the exact frozen B-4 domain."""

    if not isinstance(binding, B4ContractBinding):
        return False

    valid = (
        binding.schema_version == B4_ANALYSIS_CONTRACT_SCHEMA_VERSION
        and _is_sha256(binding.manifest_sha256)
        and _is_sha256(binding.registry_sha256)
        and type(binding.expected_block_count) is int
        and binding.expected_block_count == EXPECTED_BLOCK_COUNT
        and type(binding.blocks) is tuple
        and len(binding.blocks) == EXPECTED_BLOCK_COUNT
    )
    by_id: dict[str, B4ContractBlockBinding] = {}
    for block in binding.blocks if type(binding.blocks) is tuple else ():
        if not isinstance(block, B4ContractBlockBinding):
            valid = False
            continue
        reference = as_b4_exact_fraction(block.reference_tps)
        block_valid = (
            block.schema_version == B4_ANALYSIS_CONTRACT_SCHEMA_VERSION
            and _is_block_id(block.block_id)
            and reference is not None
            and reference > 0
            and _is_sha256(block.reference_snapshot_hash)
            and _is_sha256(block.reference_receipt_hash)
            and type(block.assignment_schedule) is tuple
            and block.assignment_schedule
            in ((B4Arm.ON, B4Arm.OFF), (B4Arm.OFF, B4Arm.ON))
        )
        if _is_block_id(block.block_id) and block.block_id in by_id:
            block_valid = False
        if _is_block_id(block.block_id):
            by_id[block.block_id] = block
        valid = valid and block_valid
    return valid


def validate_analysis_inputs(
    *,
    floor: object,
    contract_binding: object,
    registry_violation_count: object,
    blocks: object,
) -> B4ValidatedAnalysis | B4AnalysisInvalid:
    """Validate all 12 invalid reasons before any verdict branch is evaluated.

    Observable block references, ids, block count, assignment compliance types,
    and violation count are checked here.  The two ledger hashes are domain-checked
    only: no observed ledger bytes or hashes exist among these four inputs, so the
    later artifact integration unit must recompute and compare them.
    """

    reasons: set[B4AnalysisInvalidReason] = set()

    exact_floor = as_b4_exact_fraction(floor)
    if exact_floor is None or exact_floor < 0 or exact_floor >= 1:
        reasons.add(B4AnalysisInvalidReason.FLOOR_DOMAIN_ERROR)

    if type(registry_violation_count) is not int or registry_violation_count < 0:
        reasons.add(B4AnalysisInvalidReason.VIOLATION_COUNT_DOMAIN_ERROR)

    binding_valid = b4_binding_domain_is_valid(contract_binding)
    expected_by_id = (
        {block.block_id: block for block in contract_binding.blocks}
        if binding_valid and isinstance(contract_binding, B4ContractBinding)
        else {}
    )
    if not binding_valid:
        reasons.add(B4AnalysisInvalidReason.BINDING_DOMAIN_ERROR)

    block_sequence_valid = type(blocks) in (list, tuple)
    observed_blocks = tuple(blocks) if block_sequence_valid else ()
    if not block_sequence_valid:
        reasons.add(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)

    if (
        block_sequence_valid
        and isinstance(contract_binding, B4ContractBinding)
        and type(contract_binding.expected_block_count) is int
        and len(observed_blocks) != contract_binding.expected_block_count
    ):
        reasons.add(B4AnalysisInvalidReason.BLOCK_COUNT_MISMATCH)

    seen_ids: set[str] = set()
    for block in observed_blocks:
        if not isinstance(block, B4BlockObservation):
            reasons.add(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)
            continue

        if block.schema_version != B4_ANALYSIS_CONTRACT_SCHEMA_VERSION:
            reasons.add(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)

        block_id_valid = _is_block_id(block.block_id)
        if not block_id_valid:
            reasons.add(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)
        else:
            if block.block_id in seen_ids:
                reasons.add(B4AnalysisInvalidReason.DUPLICATE_BLOCK_ID)
            seen_ids.add(block.block_id)
            if expected_by_id and block.block_id not in expected_by_id:
                reasons.add(B4AnalysisInvalidReason.UNKNOWN_BLOCK_ID)

        reference = as_b4_exact_fraction(block.reference_tps)
        reference_valid = reference is not None and reference > 0
        if not reference_valid:
            reasons.add(B4AnalysisInvalidReason.REFERENCE_VALUE_DOMAIN_ERROR)

        reference_hashes_valid = _is_sha256(
            block.reference_snapshot_hash
        ) and _is_sha256(block.reference_receipt_hash)
        if not reference_hashes_valid:
            reasons.add(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)

        expected = expected_by_id.get(block.block_id) if block_id_valid else None
        if expected is not None and reference_valid and reference_hashes_valid:
            expected_reference = as_b4_exact_fraction(expected.reference_tps)
            if (
                expected_reference is not None
                and (
                    reference != expected_reference
                    or block.reference_snapshot_hash
                    != expected.reference_snapshot_hash
                    or block.reference_receipt_hash
                    != expected.reference_receipt_hash
                )
            ):
                reasons.add(B4AnalysisInvalidReason.REFERENCE_BINDING_MISMATCH)

        if type(block.assignment_followed) is not bool:
            reasons.add(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)

        arms: list[B4ArmObservation] = []
        for arm in (block.on, block.off):
            if not isinstance(arm, B4ArmObservation):
                reasons.add(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)
                continue
            arms.append(arm)
            if (
                arm.schema_version != B4_ANALYSIS_CONTRACT_SCHEMA_VERSION
                or not _is_sha256(arm.precursor_hash)
                or type(arm.treatment_fired) is not bool
                or type(arm.contaminated) is not bool
                or type(arm.protocol_ok) is not bool
            ):
                reasons.add(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)

            if not isinstance(arm.status, B4BlockStatus):
                reasons.add(B4AnalysisInvalidReason.STATUS_DOMAIN_ERROR)
                continue

            throughput = as_b4_exact_fraction(arm.throughput)
            if arm.status is B4BlockStatus.CERTIFIED:
                if throughput is None or throughput <= 0:
                    reasons.add(B4AnalysisInvalidReason.THROUGHPUT_CONTRACT_ERROR)
            elif arm.throughput is not None:
                reasons.add(B4AnalysisInvalidReason.THROUGHPUT_CONTRACT_ERROR)

        if (
            len(arms) == 2
            and _is_sha256(arms[0].precursor_hash)
            and _is_sha256(arms[1].precursor_hash)
            and arms[0].precursor_hash != arms[1].precursor_hash
        ):
            reasons.add(B4AnalysisInvalidReason.PRECURSOR_HASH_MISMATCH)

    if reasons:
        return _invalid(reasons)

    assert exact_floor is not None
    assert isinstance(contract_binding, B4ContractBinding)
    assert type(registry_violation_count) is int
    return B4ValidatedAnalysis(
        schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
        floor=exact_floor,
        contract_binding=contract_binding,
        registry_violation_count=registry_violation_count,
        blocks=observed_blocks,
    )


def block_score(
    block: B4BlockObservation,
    *,
    floor: B4ExactRatio,
) -> Fraction | B4AnalysisInvalid:
    """Return exact on superiority score, or an invalid domain result.

    The only unconditional non-certified tie is rejected versus aborted.  Missing
    is retained below both, and every certified observation outranks every
    non-certified observation regardless of throughput.
    """

    exact_floor = as_b4_exact_fraction(floor)
    if exact_floor is None or exact_floor < 0 or exact_floor >= 1:
        return _invalid((B4AnalysisInvalidReason.FLOOR_DOMAIN_ERROR,))
    if not isinstance(block, B4BlockObservation):
        return _invalid((B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED,))
    if not isinstance(block.on, B4ArmObservation) or not isinstance(
        block.off, B4ArmObservation
    ):
        return _invalid((B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED,))
    reasons: set[B4AnalysisInvalidReason] = set()
    reference = as_b4_exact_fraction(block.reference_tps)
    if reference is None or reference <= 0:
        reasons.add(B4AnalysisInvalidReason.REFERENCE_VALUE_DOMAIN_ERROR)
    if (
        block.schema_version != B4_ANALYSIS_CONTRACT_SCHEMA_VERSION
        or not _is_block_id(block.block_id)
        or not _is_sha256(block.reference_snapshot_hash)
        or not _is_sha256(block.reference_receipt_hash)
        or type(block.assignment_followed) is not bool
    ):
        reasons.add(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)
    for arm in (block.on, block.off):
        if (
            arm.schema_version != B4_ANALYSIS_CONTRACT_SCHEMA_VERSION
            or not _is_sha256(arm.precursor_hash)
            or type(arm.treatment_fired) is not bool
            or type(arm.contaminated) is not bool
            or type(arm.protocol_ok) is not bool
        ):
            reasons.add(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)
        if not isinstance(arm.status, B4BlockStatus):
            reasons.add(B4AnalysisInvalidReason.STATUS_DOMAIN_ERROR)
            continue
        throughput = as_b4_exact_fraction(arm.throughput)
        if arm.status is B4BlockStatus.CERTIFIED:
            if throughput is None or throughput <= 0:
                reasons.add(B4AnalysisInvalidReason.THROUGHPUT_CONTRACT_ERROR)
        elif arm.throughput is not None:
            reasons.add(B4AnalysisInvalidReason.THROUGHPUT_CONTRACT_ERROR)
    if (
        _is_sha256(block.on.precursor_hash)
        and _is_sha256(block.off.precursor_hash)
        and block.on.precursor_hash != block.off.precursor_hash
    ):
        reasons.add(B4AnalysisInvalidReason.PRECURSOR_HASH_MISMATCH)
    if reasons:
        return _invalid(reasons)

    if (
        block.on.status is B4BlockStatus.CERTIFIED
        and block.off.status is B4BlockStatus.CERTIFIED
    ):
        reference = as_b4_exact_fraction(block.reference_tps)
        on_throughput = as_b4_exact_fraction(block.on.throughput)
        off_throughput = as_b4_exact_fraction(block.off.throughput)
        if reference is None or reference <= 0:
            return _invalid((B4AnalysisInvalidReason.REFERENCE_VALUE_DOMAIN_ERROR,))
        if (
            on_throughput is None
            or on_throughput <= 0
            or off_throughput is None
            or off_throughput <= 0
        ):
            return _invalid((B4AnalysisInvalidReason.THROUGHPUT_CONTRACT_ERROR,))
        gain_difference = abs(on_throughput - off_throughput) / reference
        if gain_difference <= exact_floor:
            return Fraction(1, 2)
        return Fraction(1) if on_throughput > off_throughput else Fraction(0)

    if block.on.status is B4BlockStatus.CERTIFIED:
        return Fraction(1)
    if block.off.status is B4BlockStatus.CERTIFIED:
        return Fraction(0)

    middle = {B4BlockStatus.REJECTED, B4BlockStatus.ABORTED}
    if block.on.status in middle and block.off.status in middle:
        return Fraction(1, 2)
    if block.on.status is B4BlockStatus.MISSING:
        if block.off.status is B4BlockStatus.MISSING:
            return Fraction(1, 2)
        return Fraction(0)
    return Fraction(1)


def exact_sign_pvalues(*, on_wins: int, non_ties: int) -> B4ExactSignPValues:
    """Return exact upper and lower symmetric-binomial tail probabilities."""

    if (
        type(on_wins) is not int
        or type(non_ties) is not int
        or non_ties < 0
        or on_wins < 0
        or on_wins > non_ties
    ):
        raise ValueError("on_wins and non_ties must satisfy 0 <= on_wins <= non_ties")
    if non_ties == 0:
        p_on = p_off = Fraction(1)
    else:
        denominator = 1 << non_ties
        p_on = Fraction(
            sum(comb(non_ties, k) for k in range(on_wins, non_ties + 1)),
            denominator,
        )
        p_off = Fraction(
            sum(comb(non_ties, k) for k in range(0, on_wins + 1)),
            denominator,
        )
    return B4ExactSignPValues(
        schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
        on_wins=on_wins,
        non_ties=non_ties,
        p_on=p_on,
        p_off=p_off,
    )


def _binomial_tail(
    *,
    probability: Fraction,
    trials: int,
    lower: int,
    upper: int,
) -> Fraction:
    numerator = probability.numerator
    denominator = probability.denominator
    complement = denominator - numerator
    total = sum(
        comb(trials, k)
        * numerator**k
        * complement ** (trials - k)
        for k in range(lower, upper + 1)
    )
    return Fraction(total, denominator**trials)


def _increasing_tail_root_bracket(*, on_wins: int, non_ties: int) -> tuple[Fraction, Fraction]:
    low = Fraction(0)
    high = Fraction(1)
    for _ in range(_ROOT_BISECTION_STEPS):
        middle = (low + high) / 2
        tail = _binomial_tail(
            probability=middle,
            trials=non_ties,
            lower=on_wins,
            upper=non_ties,
        )
        if tail < ONE_SIDED_ALPHA:
            low = middle
        else:
            high = middle
    return low, high


def _decreasing_tail_root_bracket(*, on_wins: int, non_ties: int) -> tuple[Fraction, Fraction]:
    low = Fraction(0)
    high = Fraction(1)
    for _ in range(_ROOT_BISECTION_STEPS):
        middle = (low + high) / 2
        tail = _binomial_tail(
            probability=middle,
            trials=non_ties,
            lower=0,
            upper=on_wins,
        )
        if tail > ONE_SIDED_ALPHA:
            low = middle
        else:
            high = middle
    return low, high


def clopper_pearson_theta_95(
    *,
    on_wins: int,
    non_ties: int,
) -> B4ThetaRootOutwardEnclosure:
    """Return an outward rational enclosure of the exact 95% CP roots.

    The bisection brackets, rather than pretending their rational endpoints equal
    irrational roots, are retained in the result.  The reporting bounds always
    select the outward sides.  With no non-ties, the exact result is ``[0, 1]`` and
    theta is explicitly unestimable.
    """

    if (
        type(on_wins) is not int
        or type(non_ties) is not int
        or non_ties < 0
        or on_wins < 0
        or on_wins > non_ties
    ):
        raise ValueError("on_wins and non_ties must satisfy 0 <= on_wins <= non_ties")

    if non_ties == 0:
        return B4ThetaRootOutwardEnclosure(
            schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
            lower=Fraction(0),
            upper=Fraction(1),
            lower_root_bracket=(Fraction(0), Fraction(0)),
            upper_root_bracket=(Fraction(1), Fraction(1)),
            theta_estimable=False,
            bisection_steps=0,
        )

    lower_bracket = (
        (Fraction(0), Fraction(0))
        if on_wins == 0
        else _increasing_tail_root_bracket(
            on_wins=on_wins,
            non_ties=non_ties,
        )
    )
    upper_bracket = (
        (Fraction(1), Fraction(1))
        if on_wins == non_ties
        else _decreasing_tail_root_bracket(
            on_wins=on_wins,
            non_ties=non_ties,
        )
    )
    return B4ThetaRootOutwardEnclosure(
        schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
        lower=lower_bracket[0],
        upper=upper_bracket[1],
        lower_root_bracket=lower_bracket,
        upper_root_bracket=upper_bracket,
        theta_estimable=True,
        bisection_steps=_ROOT_BISECTION_STEPS,
    )


def _evaluate_validated_analysis(validated: B4ValidatedAnalysis) -> B4AnalysisResult:
    scores: list[Fraction] = []
    for block in validated.blocks:
        score = block_score(block, floor=validated.floor)
        assert isinstance(score, Fraction)
        scores.append(score)

    on_wins = sum(score == 1 for score in scores)
    ties = sum(score == Fraction(1, 2) for score in scores)
    non_ties = len(scores) - ties
    a_hat = B4SampleAHat(
        schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
        value=Fraction(2 * on_wins + ties, 2 * len(scores)),
    )
    p_values = exact_sign_pvalues(on_wins=on_wins, non_ties=non_ties)
    theta_interval = clopper_pearson_theta_95(
        on_wins=on_wins,
        non_ties=non_ties,
    )

    if (
        validated.registry_violation_count > 0
        or any(
            not block.assignment_followed
            or not block.on.protocol_ok
            or not block.off.protocol_ok
            for block in validated.blocks
        )
    ):
        verdict = B4Verdict.PROTOCOL_VIOLATION
    elif any(
        block.on.contaminated or block.off.contaminated
        for block in validated.blocks
    ):
        verdict = B4Verdict.INDETERMINATE
    elif sum(
        block.on.treatment_fired and block.off.treatment_fired
        for block in validated.blocks
    ) < validated.contract_binding.expected_block_count:
        verdict = B4Verdict.INDETERMINATE
    elif p_values.p_on <= ONE_SIDED_ALPHA:
        verdict = B4Verdict.ESTABLISHED
    elif p_values.p_off <= ONE_SIDED_ALPHA:
        verdict = B4Verdict.NOT_ESTABLISHED
    else:
        verdict = B4Verdict.INDETERMINATE

    return B4AnalysisResult(
        schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
        verdict=verdict,
        analysis_invalid=None,
        a_hat=a_hat,
        ties=ties,
        m=non_ties,
        on_wins=on_wins,
        p_values=p_values,
        theta_interval=theta_interval,
        effect_below_a_min=(
            verdict is B4Verdict.ESTABLISHED and a_hat.value < A_MIN
        ),
    )


def evaluate_analysis(
    *,
    floor: object,
    contract_binding: object,
    registry_violation_count: object,
    blocks: object,
) -> B4AnalysisResult:
    """Evaluate the seven ordered verdict branches as a total pure function.

    All 12 invalid-reason checks finish first.  If any reason fires, no score,
    statistic, confidence-root enclosure, or later verdict predicate is evaluated.
    Protocol violation then precedes contamination, which precedes treatment or
    sample insufficiency.  ``A_MIN`` is used only for the result annotation and is
    never an establishment threshold.
    """

    validated = validate_analysis_inputs(
        floor=floor,
        contract_binding=contract_binding,
        registry_violation_count=registry_violation_count,
        blocks=blocks,
    )
    if isinstance(validated, B4AnalysisInvalid):
        return B4AnalysisResult(
            schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
            verdict=B4Verdict.PROTOCOL_VIOLATION,
            analysis_invalid=validated,
            a_hat=None,
            ties=None,
            m=None,
            on_wins=None,
            p_values=None,
            theta_interval=None,
            effect_below_a_min=False,
        )
    return _evaluate_validated_analysis(validated)


__all__ = [
    "A_MIN",
    "B4_ANALYSIS_CONTRACT_SCHEMA_VERSION",
    "B4AnalysisInvalid",
    "B4AnalysisInvalidReason",
    "B4AnalysisResult",
    "B4Arm",
    "B4ArmObservation",
    "B4BlockObservation",
    "B4BlockStatus",
    "B4ContractBinding",
    "B4ContractBlockBinding",
    "B4ExactRatio",
    "B4ExactSignPValues",
    "B4RegistryViolationReason",
    "B4SampleAHat",
    "B4ThetaRootOutwardEnclosure",
    "B4ValidatedAnalysis",
    "B4Verdict",
    "EXPECTED_BLOCK_COUNT",
    "ONE_SIDED_ALPHA",
    "TEST_UNIT",
    "TWO_SIDED_ALPHA",
    "block_score",
    "as_b4_exact_fraction",
    "b4_binding_domain_is_valid",
    "clopper_pearson_theta_95",
    "evaluate_analysis",
    "exact_sign_pvalues",
    "validate_analysis_inputs",
]
