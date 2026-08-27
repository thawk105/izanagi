from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import dataclass, replace
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from orchestrator.campaign import p3_b4_analysis_prereg_consumer as prereg_consumer
from orchestrator.campaign import p3_b4_analysis_path as analysis_path
from orchestrator.campaign.p3_b4_analysis_adapter import (
    RAW_ANALYSIS_SCHEMA_VERSION,
)
from orchestrator.campaign.p3_b4_analysis_contract import (
    B4AnalysisInvalidReason,
    B4RegistryViolationReason,
    B4Verdict,
)
from orchestrator.campaign.p3_b4_analysis_ledgers import (
    B4_ANALYSIS_MANIFEST_SCHEMA_VERSION,
    B4_ASSIGNMENT_SEED_SCHEMA_VERSION,
    B4_SCHEDULED_ATTEMPT_SCHEMA_VERSION,
    B4_SCHEDULE_RECEIPT_SCHEMA_VERSION,
    B4AnalysisManifest,
    B4DigestRedClass,
    B4RandomizationSeedRecord,
    B4ScheduleReceipt,
    B4ScheduledAttemptInput,
    B4ScheduledAttemptReason,
    B4WhiteboardResult,
    append_registry_violation,
    build_contract_binding,
    generate_analysis_manifest,
    scheduled_attempts_sha256,
    seal_scheduled_attempt_registry,
)
from orchestrator.campaign.p3_b4_analysis_path import (
    B4AnalysisSourceClosureError,
    evaluate_b4_artifacts,
)


_SHA_A = "a" * 64
_SHA_B = "b" * 64
_SHA_C = "c" * 64
_SHA_D = "d" * 64
_SHA_E = "e" * 64
_SOURCE_PATHS = (
    "orchestrator/campaign/p3_b4_analysis_contract.py",
    "orchestrator/campaign/p3_b4_analysis_adapter.py",
    "orchestrator/campaign/p3_b4_analysis_ledgers.py",
    "orchestrator/campaign/p3_b4_analysis_path.py",
    "orchestrator/campaign/p3_b4_analysis_prereg_consumer.py",
)
_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class _Artifacts:
    registry: object
    manifest: B4AnalysisManifest
    binding: object
    registry_bytes: bytes
    manifest_bytes: bytes
    raw_bytes: bytes
    source_bytes: tuple[bytes, ...]


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _attempt(
    index: int,
    *,
    eligible: bool = True,
    ordinal: int | None = None,
) -> B4ScheduledAttemptInput:
    suffix = f"{index:03d}"
    if ordinal is None:
        ordinal = index
    return B4ScheduledAttemptInput(
        schema_version=B4_SCHEDULED_ATTEMPT_SCHEMA_VERSION,
        attempt_id=f"attempt-{suffix}",
        registry_ordinal=ordinal,
        block_id=f"block-{suffix}",
        driver="sort",
        reason=(
            B4ScheduledAttemptReason.SCHEDULED
            if eligible
            else B4ScheduledAttemptReason.SCREENING_ONLY_RED
        ),
        whiteboard_result=B4WhiteboardResult.REJECTED,
        digest_red_classes=(
            B4DigestRedClass.VERIFY_RED
            if eligible
            else B4DigestRedClass.SCREENING,
        ),
        workload="fixed-workload",
        calibrated_workload_member=True,
        initial_proposal_sha256=_hash_text(f"proposal-{suffix}"),
        bootstrap_member=True,
        reference_tps=100,
        reference_snapshot_hash=_hash_text(f"snapshot-{suffix}"),
        reference_receipt_hash=_hash_text(f"receipt-{suffix}"),
        reference_is_unique=True,
        arm_digest_received=False,
    )


def _arm_payload(
    *,
    block_index: int,
    arm: str,
    source_bytes: bytes,
    contaminated: bool,
) -> dict[str, object]:
    on_win = block_index < 6
    if arm == "on" and on_win:
        disposition = "executed"
        whiteboard = "success"
        terminal_stage = "COMMIT"
        terminal_reason = "commit"
        throughput = 120
    elif arm == "on":
        disposition = "executed"
        whiteboard = "rejected"
        terminal_stage = "ABORT"
        terminal_reason = "diff-quarantine"
        throughput = None
    else:
        disposition = "executed"
        whiteboard = "rejected" if on_win else "fail"
        terminal_stage = "ABORT"
        terminal_reason = "diff-quarantine" if on_win else "other-abort"
        throughput = None
    return {
        "arm": arm,
        "execution_disposition": disposition,
        "whiteboard_result": whiteboard,
        "terminal_stage": terminal_stage,
        "terminal_reason": terminal_reason,
        "throughput": throughput,
        "precursor_hash": _hash_text(f"precursor-{block_index:03d}"),
        "treatment_fired": True,
        "contaminated": contaminated,
        "protocol_ok": True,
        "source_artifact_sha256": hashlib.sha256(source_bytes).hexdigest(),
    }


def _raw_artifacts(
    manifest: B4AnalysisManifest,
    *,
    contaminate_first_on: bool = False,
) -> tuple[bytes, tuple[bytes, ...]]:
    blocks: list[dict[str, object]] = []
    sources: list[bytes] = []
    for index, row in enumerate(manifest.rows):
        on_source = f"source-{index:03d}-on".encode("ascii")
        off_source = f"source-{index:03d}-off".encode("ascii")
        sources.extend((on_source, off_source))
        blocks.append(
            {
                "block_id": row.block_id,
                "reference_tps": 100,
                "reference_snapshot_hash": row.reference_snapshot_hash,
                "reference_receipt_hash": row.reference_receipt_hash,
                "assignment_observation": [
                    arm.value for arm in row.assignment_schedule
                ],
                "arms": [
                    _arm_payload(
                        block_index=index,
                        arm="on",
                        source_bytes=on_source,
                        contaminated=contaminate_first_on and index == 0,
                    ),
                    _arm_payload(
                        block_index=index,
                        arm="off",
                        source_bytes=off_source,
                        contaminated=False,
                    ),
                ],
            }
        )
    payload = {
        "schema_version": RAW_ANALYSIS_SCHEMA_VERSION,
        "blocks": blocks,
    }
    return _json_bytes(payload), tuple(sources)


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _artifacts(
    *,
    extra_ineligible: bool = False,
    violation: B4RegistryViolationReason | None = None,
    contaminate_first_on: bool = False,
) -> _Artifacts:
    attempts = [_attempt(index) for index in range(201)]
    if extra_ineligible:
        attempts = [
            _attempt(201, eligible=False, ordinal=0),
            *(_attempt(index, ordinal=index + 1) for index in range(201)),
        ]
    receipt = B4ScheduleReceipt(
        schema_version=B4_SCHEDULE_RECEIPT_SCHEMA_VERSION,
        issuer_sha256=_SHA_A,
        scheduled_inputs_sha256=scheduled_attempts_sha256(attempts),
        scheduled_attempt_count=len(attempts),
    )
    registry = seal_scheduled_attempt_registry(
        scheduled_inputs=attempts,
        schedule_receipt=receipt,
    )
    if violation is not None:
        target = attempts[0]
        registry = append_registry_violation(
            registry,
            schedule_receipt=receipt,
            attempt_id=target.attempt_id,
            block_id=target.block_id,
            reason=violation,
            evidence_sha256=_SHA_B,
        )
    seed = B4RandomizationSeedRecord(
        schema_version=B4_ASSIGNMENT_SEED_SCHEMA_VERSION,
        seed_hex=_SHA_C,
        registry_prefix_sha256=registry.sealed_prefix_sha256,
        issuer_sha256=_SHA_D,
        source_receipt_sha256=_SHA_E,
    )
    manifest = generate_analysis_manifest(
        registry=registry,
        schedule_receipt=receipt,
        seed_receipt=seed,
    )
    assert isinstance(manifest, B4AnalysisManifest)
    assert manifest.schema_version == B4_ANALYSIS_MANIFEST_SCHEMA_VERSION
    binding = build_contract_binding(
        registry=registry,
        manifest=manifest,
        schedule_receipt=receipt,
        seed_receipt=seed,
    )
    raw_bytes, source_bytes = _raw_artifacts(
        manifest,
        contaminate_first_on=contaminate_first_on,
    )
    return _Artifacts(
        registry=registry,
        manifest=manifest,
        binding=binding,
        registry_bytes=registry.canonical_bytes,
        manifest_bytes=manifest.canonical_bytes,
        raw_bytes=raw_bytes,
        source_bytes=source_bytes,
    )


def _evaluate(value: _Artifacts):
    return evaluate_b4_artifacts(
        floor=0,
        contract_binding=value.binding,
        scheduled_registry_bytes=value.registry_bytes,
        analysis_manifest_bytes=value.manifest_bytes,
        raw_analysis_records_bytes=value.raw_bytes,
        source_artifact_bytes=value.source_bytes,
    )


def _assert_established(value: _Artifacts) -> None:
    result = _evaluate(value)
    assert result.analysis_invalid is None
    assert result.verdict is B4Verdict.ESTABLISHED


def _evaluate_analysis_production_callers() -> list[tuple[str, str]]:
    module_leaf = "p3_b4_analysis_contract"
    callers: list[tuple[str, str]] = []

    def dotted_name(node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = dotted_name(node.value)
            return None if prefix is None else f"{prefix}.{node.attr}"
        return None

    for path in sorted((_ROOT / "orchestrator").rglob("*.py")):
        if "tests" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        if "evaluate_analysis" not in source:
            continue
        tree = ast.parse(source, filename=str(path))
        module_aliases: set[str] = set()
        direct_aliases: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for imported in node.names:
                    if imported.name.rsplit(".", 1)[-1] == module_leaf:
                        module_aliases.add(imported.asname or imported.name)
            elif isinstance(node, ast.ImportFrom):
                imported_module = (node.module or "").rsplit(".", 1)[-1]
                if imported_module == module_leaf:
                    for imported in node.names:
                        if imported.name == "evaluate_analysis":
                            direct_aliases.add(
                                imported.asname or imported.name
                            )
                else:
                    for imported in node.names:
                        if imported.name == module_leaf:
                            module_aliases.add(imported.asname or imported.name)

        relative = path.relative_to(_ROOT).as_posix()
        for function in (
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ):
            for call in (
                node for node in ast.walk(function) if isinstance(node, ast.Call)
            ):
                target = call.func
                if isinstance(target, ast.Name) and target.id in direct_aliases:
                    callers.append((relative, function.name))
                elif (
                    isinstance(target, ast.Attribute)
                    and target.attr == "evaluate_analysis"
                    and dotted_name(target.value) in module_aliases
                ):
                    callers.append((relative, function.name))
    return callers


def test_path_signature_has_no_caller_declared_verdict_inputs() -> None:
    parameters = inspect.signature(evaluate_b4_artifacts).parameters
    assert "registry_violation_count" not in parameters
    assert "assignment_followed" not in parameters


def test_public_evaluate_analysis_production_caller_inventory_is_pinned_not_closed() -> None:
    """Pin the production path and non-exporting verification probe exactly."""

    assert _evaluate_analysis_production_callers() == [
        # The sole production path creates verdicts from real artifacts.
        (
            "orchestrator/campaign/p3_b4_analysis_path.py",
            "evaluate_b4_artifacts",
        ),
        # This verification probe checks frozen behavior and exports no result.
        (
            "orchestrator/campaign/p3_b4_analysis_prereg_consumer.py",
            "_assert_rank_and_threshold_behavior",
        ),
    ]


def test_rank_and_threshold_verification_probe_exports_no_analysis_result() -> None:
    assert prereg_consumer._assert_rank_and_threshold_behavior() is None


def test_registry_violation_cannot_be_washed_by_manifest_filter() -> None:
    positive = _artifacts(extra_ineligible=True)
    _assert_established(positive)
    assert "block-201" not in {row.block_id for row in positive.manifest.rows}

    mutated = _artifacts(
        extra_ineligible=True,
        violation=B4RegistryViolationReason.ENV_TAG_MISMATCH,
    )
    assert mutated.manifest_bytes == positive.manifest_bytes
    assert mutated.registry_bytes != positive.registry_bytes
    result = _evaluate(mutated)
    assert result.analysis_invalid is None
    assert result.verdict is B4Verdict.PROTOCOL_VIOLATION


def test_manifest_post_generation_add_delete_reorder_each_fail_exact_regeneration() -> None:
    positive = _artifacts()
    _assert_established(positive)
    original = json.loads(positive.manifest_bytes)
    variants: list[dict[str, object]] = []

    added = deepcopy(original)
    added["rows"].append(deepcopy(added["rows"][-1]))
    variants.append(added)

    deleted = deepcopy(original)
    del deleted["rows"][-1]
    variants.append(deleted)

    reordered = deepcopy(original)
    reordered["rows"][0], reordered["rows"][1] = (
        reordered["rows"][1],
        reordered["rows"][0],
    )
    variants.append(reordered)

    for payload in variants:
        mutated_bytes = _json_bytes(payload)
        assert mutated_bytes != positive.manifest_bytes
        mutated = replace(
            positive,
            binding=replace(
                positive.binding,
                manifest_sha256=hashlib.sha256(mutated_bytes).hexdigest(),
            ),
            manifest_bytes=mutated_bytes,
        )
        result = _evaluate(mutated)
        assert result.verdict is B4Verdict.PROTOCOL_VIOLATION
        assert result.analysis_invalid is not None
        assert result.analysis_invalid.reasons == (
            B4AnalysisInvalidReason.BINDING_DOMAIN_ERROR,
        )


def test_positive_violation_count_cannot_return_established() -> None:
    positive = _artifacts()
    _assert_established(positive)
    mutated = _artifacts(
        violation=B4RegistryViolationReason.ENV_TAG_MISMATCH
    )
    assert mutated.registry_bytes != positive.registry_bytes
    result = _evaluate(mutated)
    assert result.analysis_invalid is None
    assert result.verdict is B4Verdict.PROTOCOL_VIOLATION


def test_protocol_failure_precedes_contamination_in_combined_case() -> None:
    positive = _artifacts()
    _assert_established(positive)
    contaminated_only = _artifacts(contaminate_first_on=True)
    assert contaminated_only.raw_bytes != positive.raw_bytes
    assert _evaluate(contaminated_only).verdict is B4Verdict.INDETERMINATE

    combined = _artifacts(
        violation=B4RegistryViolationReason.ENV_TAG_MISMATCH,
        contaminate_first_on=True,
    )
    result = _evaluate(combined)
    assert result.analysis_invalid is None
    assert result.verdict is B4Verdict.PROTOCOL_VIOLATION


def test_caller_declared_hash_is_not_accepted() -> None:
    positive = _artifacts()
    _assert_established(positive)
    payload = json.loads(positive.raw_bytes)
    original_hash = payload["blocks"][0]["arms"][0][
        "source_artifact_sha256"
    ]
    payload["blocks"][0]["arms"][0]["source_artifact_sha256"] = _SHA_E
    mutated_bytes = _json_bytes(payload)
    assert original_hash != _SHA_E
    assert mutated_bytes != positive.raw_bytes
    result = _evaluate(replace(positive, raw_bytes=mutated_bytes))
    assert result.verdict is B4Verdict.PROTOCOL_VIOLATION
    assert result.analysis_invalid is not None
    assert result.analysis_invalid.reasons == (
        B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED,
    )


def test_manifest_and_registry_hashes_are_recomputed_from_bytes() -> None:
    positive = _artifacts()
    _assert_established(positive)
    for field in ("manifest_sha256", "registry_sha256"):
        mutated_binding = replace(positive.binding, **{field: _SHA_E})
        assert mutated_binding != positive.binding
        result = _evaluate(replace(positive, binding=mutated_binding))
        assert result.verdict is B4Verdict.PROTOCOL_VIOLATION
        assert result.analysis_invalid is not None


def test_assignment_followed_is_derived_from_raw_slots() -> None:
    positive = _artifacts()
    _assert_established(positive)
    payload = json.loads(positive.raw_bytes)
    schedule = payload["blocks"][0]["assignment_observation"]
    payload["blocks"][0]["assignment_observation"] = list(reversed(schedule))
    mutated_bytes = _json_bytes(payload)
    assert mutated_bytes != positive.raw_bytes
    result = _evaluate(replace(positive, raw_bytes=mutated_bytes))
    assert result.analysis_invalid is None
    assert result.verdict is B4Verdict.PROTOCOL_VIOLATION


def test_source_artifact_mapping_rejects_an_extra_record() -> None:
    positive = _artifacts()
    _assert_established(positive)
    mutated_sources = positive.source_bytes + (b"unreferenced-source",)
    assert mutated_sources != positive.source_bytes
    result = _evaluate(replace(positive, source_bytes=mutated_sources))
    assert result.verdict is B4Verdict.PROTOCOL_VIOLATION
    assert result.analysis_invalid is not None


def test_source_artifact_digest_swap_between_arms_is_rejected() -> None:
    positive = _artifacts()
    _assert_established(positive)
    payload = json.loads(positive.raw_bytes)
    on = payload["blocks"][0]["arms"][0]
    off = payload["blocks"][0]["arms"][1]
    on["source_artifact_sha256"], off["source_artifact_sha256"] = (
        off["source_artifact_sha256"],
        on["source_artifact_sha256"],
    )
    mutated_raw = _json_bytes(payload)
    assert mutated_raw != positive.raw_bytes

    result = _evaluate(replace(positive, raw_bytes=mutated_raw))

    assert result.verdict is B4Verdict.PROTOCOL_VIOLATION
    assert result.analysis_invalid is not None
    assert result.analysis_invalid.reasons == (
        B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED,
    )


def test_source_artifact_mapping_rejects_duplicate_bytes() -> None:
    positive = _artifacts()
    _assert_established(positive)
    duplicated = (
        positive.source_bytes[0],
        positive.source_bytes[0],
        *positive.source_bytes[2:],
    )
    assert duplicated != positive.source_bytes

    result = _evaluate(replace(positive, source_bytes=duplicated))

    assert result.verdict is B4Verdict.PROTOCOL_VIOLATION
    assert result.analysis_invalid is not None


def test_loader_failure_is_returned_as_analysis_invalid_not_raised() -> None:
    positive = _artifacts()
    _assert_established(positive)
    malformed = positive.registry_bytes[:-1]
    assert malformed != positive.registry_bytes
    result = _evaluate(replace(positive, registry_bytes=malformed))
    assert result.verdict is B4Verdict.PROTOCOL_VIOLATION
    assert result.analysis_invalid is not None
    assert result.analysis_invalid.reasons == (
        B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED,
    )


def _write_closure_members(root: Path, *, omit_last: bool = False) -> None:
    selected = _SOURCE_PATHS[:-1] if omit_last else _SOURCE_PATHS
    for index, relative_path in enumerate(selected):
        destination = root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(f"module-{index}\n".encode("ascii"))


def _preregistration_bytes() -> bytes:
    return (
        b"## 5. values\n"
        b"#### 5.1.1 frozen analysis contract\n"
        b"exact first line\n"
        b"##### nested rule\n"
        b"exact second line\n"
        b"## 6. next section\n"
    )


def _verified_consumer_result_bytes() -> bytes:
    return _json_bytes(
        {
            "schema_version": (
                analysis_path.B4_PREREGISTRATION_CONSUMER_RESULT_SCHEMA_VERSION
            ),
            "contract": {"test_verified": True},
        }
    ) + b"\n"


def test_private_closure_assembler_is_stable_and_binds_consumer_result(
    tmp_path: Path,
) -> None:
    _write_closure_members(tmp_path)
    document = _preregistration_bytes()
    consumer_result = _verified_consumer_result_bytes()
    first = analysis_path._generate_analysis_source_closure_receipt(
        repository_root=tmp_path,
        preregistration_document_bytes=document,
        consumer_result_canonical_bytes=consumer_result,
    )
    second = analysis_path._generate_analysis_source_closure_receipt(
        repository_root=tmp_path,
        preregistration_document_bytes=document,
        consumer_result_canonical_bytes=consumer_result,
    )
    assert first == second
    assert first.canonical_bytes == second.canonical_bytes
    assert first.sha256 == hashlib.sha256(first.canonical_bytes).hexdigest()
    assert first.consumer_result_canonical_bytes == consumer_result
    assert first.consumer_result_sha256 == hashlib.sha256(
        consumer_result
    ).hexdigest()
    canonical_payload = json.loads(first.canonical_bytes)
    assert canonical_payload["consumer_result"] == json.loads(consumer_result)
    assert (
        canonical_payload["consumer_result_sha256"]
        == first.consumer_result_sha256
    )
    assert tuple(member.path for member in first.members) == _SOURCE_PATHS
    expected_section = (
        b"#### 5.1.1 frozen analysis contract\n"
        b"exact first line\n"
        b"##### nested rule\n"
        b"exact second line\n"
    )
    assert first.preregistration_section_sha256 == hashlib.sha256(
        expected_section
    ).hexdigest()


def test_closure_receipt_fails_closed_when_a_member_is_absent(
    tmp_path: Path,
) -> None:
    _write_closure_members(tmp_path, omit_last=True)
    with pytest.raises(
        B4AnalysisSourceClosureError,
        match="p3_b4_analysis_prereg_consumer.py",
    ):
        analysis_path._generate_analysis_source_closure_receipt(
            repository_root=tmp_path,
            preregistration_document_bytes=_preregistration_bytes(),
            consumer_result_canonical_bytes=_verified_consumer_result_bytes(),
        )


def test_path_has_no_public_consumer_bypass_for_closure_receipt() -> None:
    assert not hasattr(
        analysis_path,
        "generate_analysis_source_closure_receipt",
    )
    assert "_generate_analysis_source_closure_receipt" not in analysis_path.__all__


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
