"""Fail-closed path from B-4 artifact bytes to the analysis verdict.

The integration entry point accepts no caller-supplied registry violation count
or assignment-compliance flag.  It derives both from strict ledger and raw
artifact bytes, verifies every declared source-artifact digest against a unique
received byte string in the raw record's exact block/arm order, and only then
invokes the pure analysis contract.  This is a one-to-one byte binding only: there is no
authoritative source-artifact format from which this unit could independently
rederive status, throughput, treatment, contamination, or protocol meaning.

This module supplies mechanical integration and the private canonical assembler
used by the consumer-owned source-closure receipt producer.  An authoritative
artifact producer, sanctioned command, durable
writer, report generator, and certified-selection connection remain outside its
scope.  In particular, source bytes presented to this API are not made
authoritative merely by passing its consistency checks.

Ledger byte/hash and regeneration failures happen outside the pure function's
four-input reason vocabulary.  This layer maps those failures to
``binding_domain_error`` as the closest integration-layer reason; that mapping
does not redefine the pure contract's narrower binding-domain description.
"""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Sequence

from .p3_b4_analysis_adapter import (
    B4RawAnalysisRecords,
    adapt_raw_blocks,
    parse_raw_analysis_records,
)
from .p3_b4_analysis_contract import (
    B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
    B4AnalysisInvalid,
    B4AnalysisInvalidReason,
    B4AnalysisResult,
    B4ContractBinding,
    B4Verdict,
    as_b4_exact_fraction,
    b4_binding_domain_is_valid,
    evaluate_analysis,
)
from .p3_b4_analysis_ledgers import (
    B4_EXECUTION_ASSIGNMENT_SCHEMA_VERSION,
    B4AnalysisManifest,
    B4ExecutionAssignmentObservation,
    B4LedgerError,
    B4ScheduledAttemptRegistry,
    assert_analysis_manifest_complete,
    assignment_followed,
    build_contract_binding,
    derive_registry_violation_count,
    load_analysis_manifest,
    load_scheduled_attempt_registry,
    verify_assignment_schedule,
)


B4_ANALYSIS_SOURCE_CLOSURE_SCHEMA_VERSION = "p3-b4-analysis-source-closure/v1"
B4_PREREGISTRATION_CONSUMER_RESULT_SCHEMA_VERSION = (
    "p3-b4-preregistration-consumer-result/v1"
)

_SOURCE_CLOSURE_PATHS = (
    "orchestrator/campaign/p3_b4_analysis_contract.py",
    "orchestrator/campaign/p3_b4_analysis_adapter.py",
    "orchestrator/campaign/p3_b4_analysis_ledgers.py",
    "orchestrator/campaign/p3_b4_analysis_path.py",
    "orchestrator/campaign/p3_b4_analysis_prereg_consumer.py",
)
_SECTION_HEADING_PREFIX = b"#### 5.1.1 "


class B4AnalysisSourceClosureError(ValueError):
    """A required source member or preregistration section is unavailable."""


@dataclass(frozen=True, slots=True)
class B4AnalysisSourceClosureMember:
    """One fixed repository-relative source member and its byte digest."""

    path: str
    sha256: str


@dataclass(frozen=True, slots=True)
class B4AnalysisSourceClosureReceipt:
    """Canonical source closure bound to one verified consumer result."""

    schema_version: str
    members: tuple[B4AnalysisSourceClosureMember, ...]
    preregistration_section_sha256: str
    consumer_result_canonical_bytes: bytes
    consumer_result_sha256: str
    canonical_bytes: bytes
    sha256: str


def _analysis_invalid_result(
    invalid: B4AnalysisInvalid | B4AnalysisInvalidReason,
) -> B4AnalysisResult:
    if isinstance(invalid, B4AnalysisInvalidReason):
        invalid = B4AnalysisInvalid(
            schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
            reasons=(invalid,),
        )
    return B4AnalysisResult(
        schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
        verdict=B4Verdict.PROTOCOL_VIOLATION,
        analysis_invalid=invalid,
        a_hat=None,
        ties=None,
        m=None,
        on_wins=None,
        p_values=None,
        theta_interval=None,
        effect_below_a_min=False,
    )


def _load_registry(
    data: object,
) -> B4ScheduledAttemptRegistry | B4AnalysisResult:
    try:
        if type(data) is not bytes:
            raise B4LedgerError("registry input is not bytes")
        return load_scheduled_attempt_registry(data)
    except B4LedgerError:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )
    except Exception:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )


def _load_manifest(
    data: object,
) -> B4AnalysisManifest | B4AnalysisResult:
    try:
        if type(data) is not bytes:
            raise B4LedgerError("manifest input is not bytes")
        return load_analysis_manifest(data)
    except B4LedgerError:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )
    except Exception:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )


def _artifact_hashes_match(
    *,
    contract_binding: object,
    scheduled_registry_bytes: bytes,
    analysis_manifest_bytes: bytes,
) -> bool:
    return (
        b4_binding_domain_is_valid(contract_binding)
        and isinstance(contract_binding, B4ContractBinding)
        and contract_binding.registry_sha256
        == hashlib.sha256(scheduled_registry_bytes).hexdigest()
        and contract_binding.manifest_sha256
        == hashlib.sha256(analysis_manifest_bytes).hexdigest()
    )


def _source_artifacts_match(
    *,
    records: B4RawAnalysisRecords,
    source_artifact_bytes: object,
) -> bool:
    if type(source_artifact_bytes) not in (list, tuple):
        return False
    if any(type(item) is not bytes for item in source_artifact_bytes):
        return False
    declared = tuple(
        arm.source_artifact_sha256
        for block in records.blocks
        for arm in block.arms
    )
    observed = tuple(
        hashlib.sha256(item).hexdigest() for item in source_artifact_bytes
    )
    return (
        len(declared) == len(observed)
        and len(set(declared)) == len(declared)
        and len(set(observed)) == len(observed)
        and declared == observed
    )


def evaluate_b4_artifacts(
    *,
    floor: object,
    contract_binding: object,
    scheduled_registry_bytes: bytes,
    analysis_manifest_bytes: bytes,
    raw_analysis_records_bytes: bytes,
    source_artifact_bytes: Sequence[bytes],
) -> B4AnalysisResult:
    """Evaluate actual B-4 artifact bytes as a total, fail-closed function.

    Processing is deliberately ordered: strict registry load, strict manifest
    load, byte-hash binding, exact manifest regeneration, unfiltered violation
    derivation, observed-slot comparison, full block adaptation, and finally the
    pure contract evaluation.  Loader, parser, and adapter failures are returned
    as one of the contract's closed invalid reasons rather than raised.
    """

    registry = _load_registry(scheduled_registry_bytes)
    if isinstance(registry, B4AnalysisResult):
        return registry

    manifest = _load_manifest(analysis_manifest_bytes)
    if isinstance(manifest, B4AnalysisResult):
        return manifest

    if not _artifact_hashes_match(
        contract_binding=contract_binding,
        scheduled_registry_bytes=scheduled_registry_bytes,
        analysis_manifest_bytes=analysis_manifest_bytes,
    ):
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.BINDING_DOMAIN_ERROR
        )

    try:
        receipt = assert_analysis_manifest_complete(
            registry=registry,
            manifest=manifest,
            schedule_receipt=registry.schedule_receipt,
            seed_receipt=manifest.seed_receipt,
        )
    except B4LedgerError:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.BINDING_DOMAIN_ERROR
        )
    except Exception:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )

    try:
        verify_assignment_schedule(
            manifest=manifest,
            seed_receipt=manifest.seed_receipt,
        )
    except B4LedgerError:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.BINDING_DOMAIN_ERROR
        )
    except Exception:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )

    try:
        actual_binding = build_contract_binding(
            registry=registry,
            manifest=manifest,
            schedule_receipt=registry.schedule_receipt,
            seed_receipt=manifest.seed_receipt,
        )
    except B4LedgerError:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.BINDING_DOMAIN_ERROR
        )
    except Exception:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )

    if (
        not b4_binding_domain_is_valid(actual_binding)
        or contract_binding != actual_binding
    ):
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.BINDING_DOMAIN_ERROR
        )

    try:
        violation_count = derive_registry_violation_count(
            registry=registry,
            schedule_receipt=registry.schedule_receipt,
        )
    except B4LedgerError:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.VIOLATION_COUNT_DOMAIN_ERROR
        )
    except Exception:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )
    if violation_count != receipt.registry_violation_count:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.VIOLATION_COUNT_DOMAIN_ERROR
        )

    parsed = parse_raw_analysis_records(raw_analysis_records_bytes)
    if isinstance(parsed, B4AnalysisInvalid):
        return _analysis_invalid_result(parsed)
    if not _source_artifacts_match(
        records=parsed,
        source_artifact_bytes=source_artifact_bytes,
    ):
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )

    try:
        followed_by_block = {
            block.block_id: assignment_followed(
                manifest=manifest,
                observation=B4ExecutionAssignmentObservation(
                    schema_version=B4_EXECUTION_ASSIGNMENT_SCHEMA_VERSION,
                    block_id=block.block_id,
                    observed_schedule=block.assignment_observation,
                ),
            )
            for block in parsed.blocks
        }
    except B4LedgerError:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )
    except Exception:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )

    adapted = adapt_raw_blocks(parsed, contract_binding=actual_binding)
    if isinstance(adapted, B4AnalysisInvalid):
        return _analysis_invalid_result(adapted)
    if any(
        block.assignment_followed != followed_by_block.get(block.block_id)
        for block in adapted
    ):
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )

    exact_floor = as_b4_exact_fraction(floor)
    if exact_floor is None or exact_floor < 0 or exact_floor >= 1:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.FLOOR_DOMAIN_ERROR
        )

    try:
        return evaluate_analysis(
            floor=exact_floor,
            contract_binding=actual_binding,
            registry_violation_count=violation_count,
            blocks=adapted,
        )
    except Exception:
        return _analysis_invalid_result(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )


def _heading_level(line: bytes) -> int | None:
    stripped = line.rstrip(b"\r\n")
    level = 0
    for character in stripped:
        if character != 35:
            break
        level += 1
    if level == 0 or level > 6 or stripped[level : level + 1] != b" ":
        return None
    return level


def preregistration_section_5_1_1_bytes(document_bytes: bytes) -> bytes:
    """Extract the exact section 5.1.1 bytes, including its heading."""

    if type(document_bytes) is not bytes:
        raise B4AnalysisSourceClosureError("preregistration input is not bytes")
    try:
        document_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise B4AnalysisSourceClosureError(
            "preregistration input is not strict UTF-8"
        ) from error
    lines = document_bytes.splitlines(keepends=True)
    starts = [
        index
        for index, line in enumerate(lines)
        if line.rstrip(b"\r\n").startswith(_SECTION_HEADING_PREFIX)
    ]
    if len(starts) != 1:
        raise B4AnalysisSourceClosureError(
            "preregistration section 5.1.1 is absent or duplicated"
        )
    start = starts[0]
    end = len(lines)
    for index in range(start + 1, len(lines)):
        level = _heading_level(lines[index])
        if level is not None and level <= 4:
            end = index
            break
    section = b"".join(lines[start:end])
    if not section:
        raise B4AnalysisSourceClosureError(
            "preregistration section 5.1.1 is empty"
        )
    return section


def _canonical_closure_bytes(
    *,
    members: tuple[B4AnalysisSourceClosureMember, ...],
    preregistration_section_sha256: str,
    consumer_result: dict[str, object],
    consumer_result_sha256: str,
) -> bytes:
    payload = {
        "schema_version": B4_ANALYSIS_SOURCE_CLOSURE_SCHEMA_VERSION,
        "members": [
            {"path": member.path, "sha256": member.sha256}
            for member in members
        ],
        "preregistration_section_sha256": preregistration_section_sha256,
        "consumer_result": consumer_result,
        "consumer_result_sha256": consumer_result_sha256,
    }
    return (
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        + b"\n"
    )


def _load_canonical_consumer_result(data: object) -> dict[str, object]:
    if type(data) is not bytes or not data:
        raise B4AnalysisSourceClosureError(
            "verified consumer result must be non-empty canonical bytes"
        )
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise B4AnalysisSourceClosureError(
            "verified consumer result is not strict UTF-8 JSON"
        ) from error
    if (
        type(value) is not dict
        or set(value) != {"schema_version", "contract"}
        or value["schema_version"]
        != B4_PREREGISTRATION_CONSUMER_RESULT_SCHEMA_VERSION
        or type(value["contract"]) is not dict
    ):
        raise B4AnalysisSourceClosureError(
            "verified consumer result schema is invalid"
        )
    canonical = (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        + b"\n"
    )
    if canonical != data:
        raise B4AnalysisSourceClosureError(
            "verified consumer result bytes are not canonical"
        )
    return value


def _generate_analysis_source_closure_receipt(
    *,
    repository_root: Path,
    preregistration_document_bytes: bytes,
    consumer_result_canonical_bytes: bytes,
) -> B4AnalysisSourceClosureReceipt:
    """Assemble a receipt after the consumer has produced canonical success bytes.

    This is private assembly, not a public verification route.  The public
    producer lives in ``p3_b4_analysis_prereg_consumer`` and reaches this helper
    only after its document, AST, and behavior checks have succeeded.  Every
    source member remains mandatory.
    """

    if not isinstance(repository_root, Path):
        raise B4AnalysisSourceClosureError("repository_root must be a Path")
    consumer_result = _load_canonical_consumer_result(
        consumer_result_canonical_bytes
    )
    consumer_result_sha256 = hashlib.sha256(
        consumer_result_canonical_bytes
    ).hexdigest()
    members: list[B4AnalysisSourceClosureMember] = []
    for relative_path in _SOURCE_CLOSURE_PATHS:
        member_path = repository_root / relative_path
        try:
            member_bytes = member_path.read_bytes()
        except OSError as error:
            raise B4AnalysisSourceClosureError(
                f"required source closure member is unavailable: {relative_path}"
            ) from error
        members.append(
            B4AnalysisSourceClosureMember(
                path=relative_path,
                sha256=hashlib.sha256(member_bytes).hexdigest(),
            )
        )
    section = preregistration_section_5_1_1_bytes(
        preregistration_document_bytes
    )
    section_sha256 = hashlib.sha256(section).hexdigest()
    member_tuple = tuple(members)
    canonical = _canonical_closure_bytes(
        members=member_tuple,
        preregistration_section_sha256=section_sha256,
        consumer_result=consumer_result,
        consumer_result_sha256=consumer_result_sha256,
    )
    return B4AnalysisSourceClosureReceipt(
        schema_version=B4_ANALYSIS_SOURCE_CLOSURE_SCHEMA_VERSION,
        members=member_tuple,
        preregistration_section_sha256=section_sha256,
        consumer_result_canonical_bytes=consumer_result_canonical_bytes,
        consumer_result_sha256=consumer_result_sha256,
        canonical_bytes=canonical,
        sha256=hashlib.sha256(canonical).hexdigest(),
    )


__all__ = [
    "B4_ANALYSIS_SOURCE_CLOSURE_SCHEMA_VERSION",
    "B4_PREREGISTRATION_CONSUMER_RESULT_SCHEMA_VERSION",
    "B4AnalysisSourceClosureError",
    "B4AnalysisSourceClosureMember",
    "B4AnalysisSourceClosureReceipt",
    "evaluate_b4_artifacts",
    "preregistration_section_5_1_1_bytes",
]
