from dataclasses import replace
import ast
import hashlib
import hmac
import inspect
from itertools import permutations
import json

import pytest

from orchestrator.campaign import p3_b4_analysis_ledgers as ledgers
from orchestrator.campaign.p3_b4_analysis_contract import (
    B4Arm,
    B4RegistryViolationReason,
    EXPECTED_BLOCK_COUNT,
)


def _hash(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _attempt(
    index: int,
    *,
    ordinal: int | None = None,
    reason: ledgers.B4ScheduledAttemptReason = ledgers.B4ScheduledAttemptReason.SCHEDULED,
    red_classes: tuple[ledgers.B4DigestRedClass, ...] = (
        ledgers.B4DigestRedClass.VERIFY_RED,
    ),
    driver: str = "base-driver",
) -> ledgers.B4ScheduledAttemptInput:
    if ordinal is None:
        ordinal = index
    return ledgers.B4ScheduledAttemptInput(
        schema_version=ledgers.B4_SCHEDULED_ATTEMPT_SCHEMA_VERSION,
        attempt_id=f"attempt-{index:04d}",
        registry_ordinal=ordinal,
        block_id=f"block-{index:04d}",
        driver=driver,
        reason=reason,
        whiteboard_result=ledgers.B4WhiteboardResult.REJECTED,
        digest_red_classes=red_classes,
        workload="calibrated-workload",
        calibrated_workload_member=True,
        initial_proposal_sha256=_hash(f"proposal-{index}"),
        bootstrap_member=True,
        reference_tps=(10_000 + index, 1),
        reference_snapshot_hash=_hash(f"snapshot-{index}"),
        reference_receipt_hash=_hash(f"reference-{index}"),
        reference_is_unique=True,
        arm_digest_received=False,
    )


def _receipt(
    attempts: tuple[ledgers.B4ScheduledAttemptInput, ...],
    *,
    issuer_sha256: str | None = None,
) -> ledgers.B4ScheduleReceipt:
    return ledgers.B4ScheduleReceipt(
        schema_version=ledgers.B4_SCHEDULE_RECEIPT_SCHEMA_VERSION,
        issuer_sha256=issuer_sha256 or _hash("schedule-issuer"),
        scheduled_inputs_sha256=ledgers.scheduled_attempts_sha256(attempts),
        scheduled_attempt_count=len(attempts),
    )


def _seal(
    attempts: tuple[ledgers.B4ScheduledAttemptInput, ...],
) -> tuple[ledgers.B4ScheduleReceipt, ledgers.B4ScheduledAttemptRegistry]:
    receipt = _receipt(attempts)
    registry = ledgers.seal_scheduled_attempt_registry(
        scheduled_inputs=attempts,
        schedule_receipt=receipt,
    )
    return receipt, registry


def _seed(
    registry: ledgers.B4ScheduledAttemptRegistry,
) -> ledgers.B4RandomizationSeedRecord:
    return ledgers.B4RandomizationSeedRecord(
        schema_version=ledgers.B4_ASSIGNMENT_SEED_SCHEMA_VERSION,
        seed_hex=_hash("seed-material"),
        registry_prefix_sha256=registry.sealed_prefix_sha256,
        issuer_sha256=_hash("seed-issuer"),
        source_receipt_sha256=_hash("seed-source-receipt"),
    )


def _manifest_bundle(
    count: int = EXPECTED_BLOCK_COUNT + 2,
) -> tuple[
    ledgers.B4ScheduleReceipt,
    ledgers.B4ScheduledAttemptRegistry,
    ledgers.B4RandomizationSeedRecord,
    ledgers.B4AnalysisManifest,
]:
    attempts = tuple(_attempt(index) for index in range(count))
    receipt, registry = _seal(attempts)
    seed = _seed(registry)
    manifest = ledgers.generate_analysis_manifest(
        registry=registry,
        schedule_receipt=receipt,
        seed_receipt=seed,
    )
    assert isinstance(manifest, ledgers.B4AnalysisManifest)
    return receipt, registry, seed, manifest


def _assert_complete(
    *,
    registry: ledgers.B4ScheduledAttemptRegistry,
    manifest: ledgers.B4AnalysisManifest,
    receipt: ledgers.B4ScheduleReceipt,
    seed: ledgers.B4RandomizationSeedRecord,
) -> ledgers.B4ManifestCompletenessReceipt:
    return ledgers.assert_analysis_manifest_complete(
        registry=registry,
        manifest=manifest,
        schedule_receipt=receipt,
        seed_receipt=seed,
    )


def test_batch_seal_is_permutation_invariant() -> None:
    attempts = (
        _attempt(3, ordinal=1),
        _attempt(1, ordinal=0),
        _attempt(2, ordinal=1),
        _attempt(0, ordinal=0),
    )
    receipt = _receipt(attempts)

    registries = [
        ledgers.seal_scheduled_attempt_registry(
            scheduled_inputs=candidate,
            schedule_receipt=receipt,
        )
        for candidate in permutations(attempts)
    ]

    assert len({registry.canonical_bytes for registry in registries}) == 1
    assert len({registry.sha256 for registry in registries}) == 1
    assert [item.attempt_id for item in registries[0].scheduled_attempts] == [
        "attempt-0000",
        "attempt-0001",
        "attempt-0002",
        "attempt-0003",
    ]
    assert (
        ledgers.load_scheduled_attempt_registry(registries[0].canonical_bytes)
        == registries[0]
    )


def test_registry_seal_preserves_finite_decimal_reference() -> None:
    candidate = replace(_attempt(0), reference_tps=(1, 10))

    _, registry = _seal((candidate,))

    assert registry.scheduled_attempts[0].reference_tps == (1, 10)


def test_registry_seal_preserves_optional_none_reference() -> None:
    candidate = replace(
        _attempt(
            0,
            reason=ledgers.B4ScheduledAttemptReason.GENERATION_FAILED,
        ),
        block_id=None,
        reference_tps=None,
        reference_snapshot_hash=None,
        reference_receipt_hash=None,
    )

    _, registry = _seal((candidate,))

    assert registry.scheduled_attempts[0].reference_tps is None


@pytest.mark.parametrize(
    "reference_tps",
    ((1, 3), (1, 30)),
    ids=("one-third", "one-thirtieth"),
)
def test_registry_hash_rejects_nonterminating_reference_ratio(
    reference_tps: tuple[int, int],
) -> None:
    assert ledgers._ratio_from_payload(list(reference_tps)) == reference_tps
    candidate = replace(_attempt(0), reference_tps=reference_tps)

    with pytest.raises(ledgers.B4LedgerError) as exc_info:
        ledgers.scheduled_attempts_sha256((candidate,))

    assert str(exc_info.value) == "reference_tps has no finite decimal expansion"


def test_registry_completeness_requires_issuer_bound_schedule_receipt() -> None:
    attempts = tuple(_attempt(index) for index in range(EXPECTED_BLOCK_COUNT)) + (
        _attempt(
            800,
            reason=ledgers.B4ScheduledAttemptReason.GENERATION_FAILED,
        ),
    )
    receipt, registry = _seal(attempts)
    ledgers.assert_scheduled_registry_complete(
        registry=registry,
        schedule_receipt=receipt,
    )

    different_receipt = replace(receipt, issuer_sha256=_hash("different-issuer"))
    assert different_receipt != receipt
    with pytest.raises(ledgers.B4LedgerError):
        ledgers.assert_scheduled_registry_complete(
            registry=registry,
            schedule_receipt=different_receipt,
        )
    with pytest.raises(ledgers.B4LedgerError):
        ledgers.seal_scheduled_attempt_registry(
            scheduled_inputs=attempts,
            schedule_receipt=None,
        )
    success_only_subset = attempts[:-1]
    assert success_only_subset != attempts
    with pytest.raises(ledgers.B4LedgerError):
        ledgers.seal_scheduled_attempt_registry(
            scheduled_inputs=success_only_subset,
            schedule_receipt=receipt,
        )

    seed = _seed(registry)
    with pytest.raises(ledgers.B4LedgerError):
        ledgers.generate_analysis_manifest(
            registry=registry,
            schedule_receipt=None,
            seed_receipt=seed,
        )
    assert "scheduled_inputs" not in inspect.signature(
        ledgers.assert_scheduled_registry_complete
    ).parameters


def test_derive_assignment_requires_seed_receipt() -> None:
    receipt, registry, seed, _ = _manifest_bundle()
    block_id = registry.scheduled_attempts[0].block_id
    positive = ledgers.derive_assignment(seed_receipt=seed, block_id=block_id)
    assert isinstance(positive, ledgers.B4AssignmentArmOrder)

    invalid = replace(seed, issuer_sha256="f" * 63)
    assert invalid != seed
    with pytest.raises(ledgers.B4LedgerError):
        ledgers.derive_assignment(seed_receipt=invalid, block_id=block_id)
    with pytest.raises(ledgers.B4LedgerError):
        ledgers.derive_assignment(seed_receipt=None, block_id=block_id)

    with pytest.raises(ledgers.B4LedgerError):
        ledgers.generate_analysis_manifest(
            registry=registry,
            schedule_receipt=receipt,
            seed_receipt=None,
        )


def test_assignment_is_deterministic_from_seed_and_block_id() -> None:
    receipt, registry, seed, manifest = _manifest_bundle()
    block_id = registry.scheduled_attempts[17].block_id

    first = ledgers.derive_assignment(seed_receipt=seed, block_id=block_id)
    second = ledgers.derive_assignment(seed_receipt=seed, block_id=block_id)

    assert first is second
    matching_row = next(row for row in manifest.rows if row.block_id == block_id)
    assert matching_row.assignment_order is first
    ledgers.verify_assignment_schedule(manifest=manifest, seed_receipt=seed)
    binding = ledgers.build_contract_binding(
        registry=registry,
        manifest=manifest,
        schedule_receipt=receipt,
        seed_receipt=seed,
    )
    assert binding.expected_block_count == EXPECTED_BLOCK_COUNT
    assert binding.blocks[17].assignment_schedule == matching_row.assignment_schedule


@pytest.mark.parametrize(
    ("block_id", "expected_digest", "expected_order"),
    [
        (
            "vector-block-000",
            "a01f7a7996964382afcf68d750d61cc7a30d27e558e3d969e418509e6a39e6e5",
            ledgers.B4AssignmentArmOrder.ON_FIRST,
        ),
        (
            "vector-block-003",
            "4b8917fb898ef2bb49873d8cec329af13d957987de57567be496e2482efedf83",
            ledgers.B4AssignmentArmOrder.OFF_FIRST,
        ),
        (
            "vector-block-007",
            "057f8b8cf83b4ec702be45e6d88f96458ecf85f6a096ecb282add7fa1a8649fa",
            ledgers.B4AssignmentArmOrder.OFF_FIRST,
        ),
    ],
)
def test_assignment_matches_independent_fixed_hmac_vectors(
    block_id: str,
    expected_digest: str,
    expected_order: ledgers.B4AssignmentArmOrder,
) -> None:
    seed = ledgers.B4RandomizationSeedRecord(
        schema_version=ledgers.B4_ASSIGNMENT_SEED_SCHEMA_VERSION,
        seed_hex="00" * 32,
        registry_prefix_sha256="11" * 32,
        issuer_sha256="22" * 32,
        source_receipt_sha256="33" * 32,
    )
    independent_payload = json.dumps(
        {
            "block_id": block_id,
            "registry_prefix_sha256": "11" * 32,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    independent_digest = hmac.new(
        bytes.fromhex("00" * 32),
        b"p3-b4-assignment/v1\x00" + independent_payload,
        hashlib.sha256,
    ).hexdigest()

    assert independent_digest == expected_digest
    assert (
        ledgers.derive_assignment(seed_receipt=seed, block_id=block_id)
        is expected_order
    )


def test_fixed_assignment_vectors_are_concretely_nonconstant() -> None:
    seed = ledgers.B4RandomizationSeedRecord(
        schema_version=ledgers.B4_ASSIGNMENT_SEED_SCHEMA_VERSION,
        seed_hex="00" * 32,
        registry_prefix_sha256="11" * 32,
        issuer_sha256="22" * 32,
        source_receipt_sha256="33" * 32,
    )
    actual = tuple(
        ledgers.derive_assignment(
            seed_receipt=seed,
            block_id=f"vector-block-{index:03d}",
        )
        for index in range(8)
    )
    assert actual == (
        ledgers.B4AssignmentArmOrder.ON_FIRST,
        ledgers.B4AssignmentArmOrder.ON_FIRST,
        ledgers.B4AssignmentArmOrder.ON_FIRST,
        ledgers.B4AssignmentArmOrder.OFF_FIRST,
        ledgers.B4AssignmentArmOrder.ON_FIRST,
        ledgers.B4AssignmentArmOrder.ON_FIRST,
        ledgers.B4AssignmentArmOrder.ON_FIRST,
        ledgers.B4AssignmentArmOrder.OFF_FIRST,
    )


def test_registry_preserves_failed_duplicate_corrupt_and_screening_rows() -> None:
    eligible = tuple(_attempt(index) for index in range(EXPECTED_BLOCK_COUNT))
    exceptional = (
        _attempt(
            300,
            reason=ledgers.B4ScheduledAttemptReason.GENERATION_FAILED,
        ),
        _attempt(
            301,
            reason=ledgers.B4ScheduledAttemptReason.RED_NOT_REPRODUCED,
        ),
        _attempt(302, reason=ledgers.B4ScheduledAttemptReason.DUPLICATE),
        _attempt(303, reason=ledgers.B4ScheduledAttemptReason.CORRUPT),
        _attempt(
            304,
            reason=ledgers.B4ScheduledAttemptReason.SCREENING_ONLY_RED,
            red_classes=(ledgers.B4DigestRedClass.SCREENING,),
        ),
    )
    receipt, registry = _seal(eligible + exceptional)
    loaded = ledgers.load_scheduled_attempt_registry(registry.canonical_bytes)

    assert len(loaded.scheduled_attempts) == EXPECTED_BLOCK_COUNT + len(exceptional)
    assert {
        item.reason for item in loaded.scheduled_attempts[-len(exceptional) :]
    } == {
        ledgers.B4ScheduledAttemptReason.GENERATION_FAILED,
        ledgers.B4ScheduledAttemptReason.RED_NOT_REPRODUCED,
        ledgers.B4ScheduledAttemptReason.DUPLICATE,
        ledgers.B4ScheduledAttemptReason.CORRUPT,
        ledgers.B4ScheduledAttemptReason.SCREENING_ONLY_RED,
    }
    for item in exceptional:
        assert item.attempt_id.encode("ascii") in registry.canonical_bytes

    seed = _seed(registry)
    manifest = ledgers.generate_analysis_manifest(
        registry=registry,
        schedule_receipt=receipt,
        seed_receipt=seed,
    )
    assert isinstance(manifest, ledgers.B4AnalysisManifest)
    assert len(manifest.rows) == EXPECTED_BLOCK_COUNT
    assert {row.attempt_id for row in manifest.rows}.isdisjoint(
        {item.attempt_id for item in exceptional}
    )


def test_manifest_selects_first_201_eligible_rows_only() -> None:
    attempts = tuple(
        _attempt(index, ordinal=index // 2)
        for index in range(EXPECTED_BLOCK_COUNT + 4)
    )
    receipt, registry = _seal(tuple(reversed(attempts)))
    seed = _seed(registry)

    manifest = ledgers.generate_analysis_manifest(
        registry=registry,
        schedule_receipt=receipt,
        seed_receipt=seed,
    )

    assert isinstance(manifest, ledgers.B4AnalysisManifest)
    assert [row.attempt_id for row in manifest.rows] == [
        item.attempt_id for item in registry.scheduled_attempts[:EXPECTED_BLOCK_COUNT]
    ]
    assert len(manifest.rows) == EXPECTED_BLOCK_COUNT
    _assert_complete(
        registry=registry,
        manifest=manifest,
        receipt=receipt,
        seed=seed,
    )


@pytest.mark.parametrize(
    ("predicate", "changes"),
    [
        (
            "scheduled_reason",
            {"reason": ledgers.B4ScheduledAttemptReason.GENERATION_FAILED},
        ),
        (
            "rejected_whiteboard",
            {"whiteboard_result": ledgers.B4WhiteboardResult.SUCCESS},
        ),
        (
            "eligible_red_class",
            {"digest_red_classes": (ledgers.B4DigestRedClass.SCREENING,)},
        ),
        ("calibrated_workload", {"calibrated_workload_member": False}),
        ("bootstrap_membership", {"bootstrap_member": False}),
        ("unique_reference", {"reference_is_unique": False}),
        ("uncontaminated_precursor", {"arm_digest_received": True}),
    ],
    ids=(
        "scheduled_reason",
        "rejected_whiteboard",
        "eligible_red_class",
        "calibrated_workload",
        "bootstrap_membership",
        "unique_reference",
        "uncontaminated_precursor",
    ),
)
def test_each_reachable_eligibility_predicate_excludes_a_precutoff_row(
    predicate: str,
    changes: dict[str, object],
) -> None:
    ineligible = replace(_attempt(900, ordinal=0), **changes)
    eligible = tuple(
        _attempt(index, ordinal=index + 1)
        for index in range(EXPECTED_BLOCK_COUNT + 1)
    )
    receipt, registry = _seal((ineligible, *eligible))
    if predicate == "uncontaminated_precursor":
        registry = ledgers.append_registry_violation(
            registry,
            schedule_receipt=receipt,
            attempt_id=ineligible.attempt_id,
            block_id=ineligible.block_id,
            reason=(
                B4RegistryViolationReason.ARM_DIGEST_CONTAMINATED_PRECURSOR
            ),
            evidence_sha256=_hash("precutoff-contamination"),
        )
    seed = _seed(registry)

    manifest = ledgers.generate_analysis_manifest(
        registry=registry,
        schedule_receipt=receipt,
        seed_receipt=seed,
    )

    assert isinstance(manifest, ledgers.B4AnalysisManifest)
    assert tuple(row.attempt_id for row in manifest.rows) == tuple(
        attempt.attempt_id for attempt in eligible[:EXPECTED_BLOCK_COUNT]
    )
    assert ineligible.attempt_id not in {
        row.attempt_id for row in manifest.rows
    }
    assert eligible[EXPECTED_BLOCK_COUNT].attempt_id not in {
        row.attempt_id for row in manifest.rows
    }


@pytest.mark.parametrize(
    ("predicate", "changes"),
    [
        ("block_id", {"block_id": None}),
        ("reference_tps", {"reference_tps": None}),
        ("reference_snapshot_hash", {"reference_snapshot_hash": None}),
        ("reference_receipt_hash", {"reference_receipt_hash": None}),
    ],
    ids=(
        "block_id",
        "reference_tps",
        "reference_snapshot_hash",
        "reference_receipt_hash",
    ),
)
def test_each_structural_eligibility_predicate_is_independently_pinned(
    predicate: str,
    changes: dict[str, object],
) -> None:
    del predicate
    candidate = replace(_attempt(900, ordinal=0), **changes)

    # Strict registry sealing rejects these rows earlier.  Calling the predicate
    # directly isolates its otherwise unreachable conjunct so deleting exactly
    # that conjunct still turns this parameterized node red.
    assert ledgers._attempt_is_eligible(candidate) is False


def test_fewer_than_201_eligible_rows_is_design_not_feasible() -> None:
    attempts = tuple(_attempt(index) for index in range(EXPECTED_BLOCK_COUNT - 1))
    receipt, registry = _seal(attempts)
    seed = _seed(registry)

    result = ledgers.generate_analysis_manifest(
        registry=registry,
        schedule_receipt=receipt,
        seed_receipt=seed,
    )

    assert isinstance(result, ledgers.B4DesignNotFeasible)
    assert result.reason is ledgers.B4ManifestState.DESIGN_NOT_FEASIBLE
    assert result.eligible_count == EXPECTED_BLOCK_COUNT - 1
    assert result.required_count == EXPECTED_BLOCK_COUNT
    assert not hasattr(result, "rows")


def test_manifest_added_deleted_reordered_or_driver_swapped_is_rejected() -> None:
    receipt, registry, seed, manifest = _manifest_bundle()
    _assert_complete(
        registry=registry,
        manifest=manifest,
        receipt=receipt,
        seed=seed,
    )

    extra = replace(
        manifest.rows[-1],
        attempt_id="attempt-extra",
        block_id="block-extra",
    )
    swapped_driver = replace(manifest.rows[0], driver="different-driver")
    mutations = (
        replace(manifest, rows=manifest.rows + (extra,)),
        replace(manifest, rows=manifest.rows[:-1]),
        replace(
            manifest,
            rows=(manifest.rows[1], manifest.rows[0], *manifest.rows[2:]),
        ),
        replace(manifest, rows=(swapped_driver, *manifest.rows[1:])),
    )

    for mutated in mutations:
        assert mutated.rows != manifest.rows
        with pytest.raises(ledgers.B4DesignNotFeasibleError):
            _assert_complete(
                registry=registry,
                manifest=mutated,
                receipt=receipt,
                seed=seed,
            )


def test_manifest_hash_without_row_equality_is_not_completeness() -> None:
    receipt, registry, seed, manifest = _manifest_bundle()
    _assert_complete(
        registry=registry,
        manifest=manifest,
        receipt=receipt,
        seed=seed,
    )

    changed_row = replace(manifest.rows[0], driver="hash-is-not-row-proof")
    forged = replace(manifest, rows=(changed_row, *manifest.rows[1:]))

    assert forged.rows != manifest.rows
    assert forged.sha256 == manifest.sha256
    assert forged.canonical_bytes == manifest.canonical_bytes
    with pytest.raises(ledgers.B4DesignNotFeasibleError):
        _assert_complete(
            registry=registry,
            manifest=forged,
            receipt=receipt,
            seed=seed,
        )


def test_registry_violation_count_is_derived_before_eligibility_filter() -> None:
    eligible = tuple(_attempt(index) for index in range(EXPECTED_BLOCK_COUNT))
    contaminated = replace(_attempt(900), arm_digest_received=True)
    receipt, registry = _seal(eligible + (contaminated,))
    with pytest.raises(ledgers.B4LedgerError):
        ledgers.derive_registry_violation_count(
            registry=registry,
            schedule_receipt=receipt,
        )
    registry = ledgers.append_registry_violation(
        registry,
        schedule_receipt=receipt,
        attempt_id=contaminated.attempt_id,
        block_id=contaminated.block_id,
        reason=B4RegistryViolationReason.ARM_DIGEST_CONTAMINATED_PRECURSOR,
        evidence_sha256=_hash("contamination-violation-evidence"),
    )
    seed = _seed(registry)

    assert (
        ledgers.derive_registry_violation_count(
            registry=registry,
            schedule_receipt=receipt,
        )
        == 1
    )
    manifest = ledgers.generate_analysis_manifest(
        registry=registry,
        schedule_receipt=receipt,
        seed_receipt=seed,
    )
    assert isinstance(manifest, ledgers.B4AnalysisManifest)
    assert contaminated.attempt_id not in {row.attempt_id for row in manifest.rows}
    completeness = _assert_complete(
        registry=registry,
        manifest=manifest,
        receipt=receipt,
        seed=seed,
    )
    assert completeness.registry_violation_count == 1

    unrecognized = replace(registry.violations[0], reason="future-reason")
    forged = replace(registry, violations=(unrecognized,))
    assert forged.violations != registry.violations
    with pytest.raises(ledgers.B4LedgerError):
        ledgers.derive_registry_violation_count(
            registry=forged,
            schedule_receipt=receipt,
        )


def test_registry_append_is_strict_prefix_and_hash_chained() -> None:
    attempts = tuple(_attempt(index) for index in range(EXPECTED_BLOCK_COUNT))
    receipt, registry = _seal(attempts)
    appended = ledgers.append_registry_violation(
        registry,
        schedule_receipt=receipt,
        attempt_id=attempts[0].attempt_id,
        block_id=attempts[0].block_id,
        reason=B4RegistryViolationReason.ENV_TAG_MISMATCH,
        evidence_sha256=_hash("env-evidence"),
    )

    assert appended.canonical_bytes.startswith(registry.canonical_bytes)
    assert appended.canonical_bytes != registry.canonical_bytes
    assert appended.sealed_prefix_sha256 == registry.sealed_prefix_sha256
    assert appended.sha256 != registry.sha256
    assert ledgers.load_scheduled_attempt_registry(appended.canonical_bytes) == appended


def test_assignment_observation_is_compared_with_frozen_row() -> None:
    receipt, registry, seed, manifest = _manifest_bundle()
    del receipt, registry, seed
    row = manifest.rows[0]
    followed = ledgers.B4ExecutionAssignmentObservation(
        schema_version=ledgers.B4_EXECUTION_ASSIGNMENT_SCHEMA_VERSION,
        block_id=row.block_id,
        observed_schedule=row.assignment_schedule,
    )
    assert ledgers.assignment_followed(manifest=manifest, observation=followed)

    reversed_observation = replace(
        followed,
        observed_schedule=tuple(reversed(followed.observed_schedule)),
    )
    assert reversed_observation != followed
    assert not ledgers.assignment_followed(
        manifest=manifest,
        observation=reversed_observation,
    )


def test_assignment_regeneration_rejects_a_changed_schedule() -> None:
    _receipt_value, _registry, seed, manifest = _manifest_bundle()
    ledgers.verify_assignment_schedule(manifest=manifest, seed_receipt=seed)
    row = manifest.rows[0]
    other_order = (
        ledgers.B4AssignmentArmOrder.OFF_FIRST
        if row.assignment_order is ledgers.B4AssignmentArmOrder.ON_FIRST
        else ledgers.B4AssignmentArmOrder.ON_FIRST
    )
    changed_row = replace(row, assignment_order=other_order)
    changed_schedule = replace(manifest, rows=(changed_row, *manifest.rows[1:]))
    assert changed_schedule.rows != manifest.rows
    with pytest.raises(ledgers.B4LedgerError):
        ledgers.verify_assignment_schedule(
            manifest=changed_schedule,
            seed_receipt=seed,
        )


def test_manifest_completeness_rejects_a_changed_schedule() -> None:
    receipt, registry, seed, manifest = _manifest_bundle()
    row = manifest.rows[0]
    other_order = (
        ledgers.B4AssignmentArmOrder.OFF_FIRST
        if row.assignment_order is ledgers.B4AssignmentArmOrder.ON_FIRST
        else ledgers.B4AssignmentArmOrder.ON_FIRST
    )
    changed_row = replace(row, assignment_order=other_order)
    changed_schedule = replace(manifest, rows=(changed_row, *manifest.rows[1:]))
    assert changed_schedule.rows != manifest.rows
    with pytest.raises(ledgers.B4DesignNotFeasibleError):
        _assert_complete(
            registry=registry,
            manifest=changed_schedule,
            receipt=receipt,
            seed=seed,
        )


def test_postfreeze_byte_gate_rejects_distinct_valid_canonical_manifest() -> None:
    _receipt_value, _registry, _seed_value, manifest = _manifest_bundle()
    other_attempts = tuple(
        _attempt(index, driver="other-driver")
        for index in range(EXPECTED_BLOCK_COUNT)
    )
    other_receipt, other_registry = _seal(other_attempts)
    other_seed = _seed(other_registry)
    other_manifest = ledgers.generate_analysis_manifest(
        registry=other_registry,
        schedule_receipt=other_receipt,
        seed_receipt=other_seed,
    )
    assert isinstance(other_manifest, ledgers.B4AnalysisManifest)
    assert other_manifest.canonical_bytes != manifest.canonical_bytes

    ledgers.assert_manifest_unchanged_before_run(
        frozen_manifest_bytes=manifest.canonical_bytes,
        observed_manifest_bytes=manifest.canonical_bytes,
    )
    with pytest.raises(ledgers.B4DesignNotFeasibleError):
        ledgers.assert_manifest_unchanged_before_run(
            frozen_manifest_bytes=manifest.canonical_bytes,
            observed_manifest_bytes=other_manifest.canonical_bytes,
        )


def test_ledgers_have_no_random_time_or_environment_import() -> None:
    tree = ast.parse(inspect.getsource(ledgers))
    imported_roots: set[str] = set()
    forbidden_calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Attribute):
            forbidden_calls.add(node.attr)

    assert imported_roots.isdisjoint({"datetime", "os", "random", "secrets", "time"})
    assert forbidden_calls.isdisjoint({"environ", "getenv", "urandom"})


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
