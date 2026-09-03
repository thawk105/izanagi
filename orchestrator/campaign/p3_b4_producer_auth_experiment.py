"""Counterfactual producer-authentication experiment for B-4.

This module is deliberately not a production authentication layer.  It owns
the three guards used by disposable prototypes, the exact mutations and
prototype patches, scratch-tree isolation, result attribution, and canonical
comparison-report serialization.  Production modules call a guard only after
the corresponding prototype patch has been applied inside a disposable tree.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Callable, Iterable, Mapping, NoReturn, Sequence


SCRATCH_ROOT = Path("/work/1/SFC/tanab/t2103-scratch")
PRODUCER_PATH = "orchestrator/campaign/p3_b4_raw_record_producer.py"
EXPERIMENT_PATH = "orchestrator/campaign/p3_b4_producer_auth_experiment.py"
PREREGISTRATION_RELATIVE_PATH = (
    "output/insights/2026-09-03_t2103-producer-auth-layer/"
    "mutation-prereg.json"
)
COMPARISON_RELATIVE_PATH = (
    "output/insights/2026-09-03_t2103-producer-auth-layer/comparison.json"
)
EXPERIMENT_OVERLAY_PATHS = (
    EXPERIMENT_PATH,
    "orchestrator/tests/p3_b4_rogue_producer_support.py",
    "orchestrator/tests/test_p3_b4_producer_auth_experiment.py",
    PREREGISTRATION_RELATIVE_PATH,
)
PREREGISTRATION_SCHEMA_VERSION = "p3-b4-producer-auth-prereg/v7"
REPORT_SCHEMA_VERSION = "p3-b4-producer-auth-comparison/v7"
SHARD_SCHEMA_VERSION = "p3-b4-producer-auth-candidate-phase-shard/v4"
REAL_REGIME_BLOCK_COUNT = 201
MEASUREMENT_FLOOR = 0
TRUST_ANCHOR_SOURCE = "measurement_base_commit_git_blob"
_ENVIRONMENT_CONSTANT_PREFIX = "ENVIRONMENT_CONSTANT:"
_FLOOR_DOMAIN_ERROR = "floor_domain_error"


class Candidate(str, Enum):
    ISSUER = "issuer"
    RAW_ASSEMBLY = "raw_assembly"
    FROZEN_CONSUMER = "temporary_6_member_expanded_closure_prototype"


class MeasurementPhase(str, Enum):
    BASELINE = "baseline"
    PROTOTYPE = "prototype"


class CaseOutcome(str, Enum):
    KILLED = "KILLED"
    SURVIVED = "SURVIVED"
    BASELINE_REJECTED = "BASELINE_REJECTED"
    ENVIRONMENT_CONSTANT = "ENVIRONMENT_CONSTANT"
    ABORTED = "ABORTED"


def analysis_invalid_observation_reason(reasons: Iterable[object]) -> str:
    """Preserve every evaluator invalid reason and classify floor absence."""

    reason_values = tuple(
        reason.value if isinstance(reason, Enum) else reason
        for reason in reasons
    )
    if not reason_values or any(
        type(reason) is not str or not reason for reason in reason_values
    ):
        raise ValueError("analysis_invalid reasons are empty or invalid")
    detail = "evaluator:analysis_invalid:reasons=" + ",".join(reason_values)
    if _FLOOR_DOMAIN_ERROR in reason_values:
        return _ENVIRONMENT_CONSTANT_PREFIX + detail
    return detail


def is_environment_constant_reason(reason: object) -> bool:
    """Return whether a diagnostic is excluded from candidate attribution."""

    return type(reason) is str and reason.startswith(_ENVIRONMENT_CONSTANT_PREFIX)


def measurement_evaluator_contract_value() -> dict[str, object]:
    """Describe the ruled measurement-only evaluator boundary."""

    return {
        "floor": MEASUREMENT_FLOOR,
        "floor_domain_error_classification": CaseOutcome.ENVIRONMENT_CONSTANT.value,
        "floor_scope": "experiment_only",
        "production_floor": None,
        "production_floor_availability": "absent",
    }


class ProducerAuthRejection(RuntimeError):
    """A disposable candidate guard rejected the fixed producer member."""

    def __init__(self, candidate: Candidate, observed_sha256: str) -> None:
        self.candidate = candidate
        self.observed_sha256 = observed_sha256
        super().__init__(
            f"producer_auth_rejection:{candidate.value}:{observed_sha256}"
        )


class ScratchTreeError(RuntimeError):
    """A disposable tree could not be created or completely destroyed."""


class PreregistrationError(ValueError):
    """The approved preregistration does not match the executable registry."""


class ComparisonIntegrityError(ValueError):
    """A shard or recorded comparison cannot produce an authenticated decision."""


@dataclass(frozen=True, slots=True)
class TrustAnchor:
    candidate: Candidate
    producer_path: str
    sha256: str

    def __post_init__(self) -> None:
        if self.producer_path != PRODUCER_PATH:
            raise ValueError("trust anchor names an unexpected producer path")
        if not _is_sha256(self.sha256):
            raise ValueError("trust anchor sha256 is not canonical")


@dataclass(frozen=True, slots=True)
class ExactPatch:
    candidate: Candidate
    relative_path: str
    old_bytes: bytes
    new_bytes: bytes
    position: str
    order: int

    def __post_init__(self) -> None:
        if not self.relative_path or Path(self.relative_path).is_absolute():
            raise ValueError("patch path must be repository-relative")
        if not self.old_bytes or self.old_bytes == self.new_bytes:
            raise ValueError("patch must replace nonempty, differing bytes")
        if self.order < 1:
            raise ValueError("patch order must be positive")


@dataclass(frozen=True, slots=True)
class MutationSpec:
    mutation_id: str
    family: str
    judgment: str
    target_arm: str
    relative_path: str
    old_bytes: bytes
    new_bytes: bytes
    position: str
    order: int
    decision_input: bool

    def __post_init__(self) -> None:
        if self.family not in {"C0", "C1", "R", "D", "POS"}:
            raise ValueError("unknown mutation family")
        if self.judgment not in {"P", "T", "C", "none"}:
            raise ValueError("unknown judgment")
        if self.target_arm not in {"on", "both", "none"}:
            raise ValueError("unknown target arm")
        if self.family == "POS":
            if self.old_bytes or self.new_bytes or self.decision_input:
                raise ValueError("positive control must not carry a mutation")
        elif not self.old_bytes or self.old_bytes == self.new_bytes:
            raise ValueError("negative mutation must have exact differing bytes")


@dataclass(frozen=True, slots=True)
class LayerObservation:
    guard_rejected: bool
    rejecting_candidate: Candidate | None
    existing_gate_rejected: bool
    reason: str | None

    def __post_init__(self) -> None:
        if self.guard_rejected != (self.rejecting_candidate is not None):
            raise ValueError("guard rejection and rejecting candidate disagree")
        if self.reason is not None and type(self.reason) is not str:
            raise TypeError("reason must be a string or None")
        if is_environment_constant_reason(self.reason) and (
            self.guard_rejected or self.existing_gate_rejected
        ):
            raise ValueError(
                "environment constant must not be attributed to a rejection gate"
            )


@dataclass(frozen=True, slots=True)
class CandidateCaseResult:
    base_commit: str
    candidate: Candidate
    mutation_id: str
    expected: CaseOutcome
    observed: CaseOutcome
    baseline: LayerObservation
    prototype: LayerObservation

    @property
    def incremental_kill(self) -> bool:
        return (
            self.observed is CaseOutcome.KILLED
            and not self.baseline.existing_gate_rejected
            and self.prototype.guard_rejected
            and self.prototype.rejecting_candidate is self.candidate
        )


@dataclass(frozen=True, slots=True)
class CandidatePhaseResult:
    base_commit: str
    candidate: Candidate
    mutation_id: str
    phase: MeasurementPhase
    observation: LayerObservation
    wall_seconds: float

    def __post_init__(self) -> None:
        if (
            type(self.wall_seconds) is not float
            or not math.isfinite(self.wall_seconds)
            or self.wall_seconds < 0.0
        ):
            raise ValueError("phase wall time must be a finite nonnegative float")


@dataclass(frozen=True, slots=True)
class ChangeClosure:
    candidate: Candidate
    production_file_count: int
    pin_site_count: int
    test_impact_file_count: int

    @property
    def tie_break_key(self) -> tuple[int, int, int]:
        return (
            self.production_file_count,
            self.pin_site_count,
            self.test_impact_file_count,
        )


@dataclass(frozen=True, slots=True)
class ComparisonDecision:
    base_commit: str | None
    decision_available: bool
    leaders: tuple[Candidate, ...]
    complete_candidate_exists: bool
    incremental_kills: tuple[tuple[Candidate, int], ...]
    non_regression: tuple[tuple[Candidate, bool], ...]
    ineligible_candidates: tuple[Candidate, ...]
    blocking_reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WaveMutant:
    mutation_id: str
    relative_path: str
    old_bytes: bytes
    new_bytes: bytes
    target_node: str

    def __post_init__(self) -> None:
        if self.mutation_id not in {f"W{index:02d}" for index in range(1, 9)}:
            raise ValueError("wave mutant id must be W01 through W08")
        if not self.old_bytes or self.old_bytes == self.new_bytes:
            raise ValueError("wave mutant needs differing exact bytes")


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


_JUDGMENT_PATCHES = {
    "P": (
        "both",
        b"    protocol_ok = all(\n",
        b"    protocol_ok = False and all(\n",
        "_arm_observation protocol_ok derivation",
    ),
    "T": (
        "on",
        b"        treatment_fired = red_detail and not peer_red_detail and "
        b"digest.startswith(peer_digest + \"\\n\\n\")\n",
        b"        treatment_fired = False\n",
        "_arm_observation on-arm treatment_fired derivation",
    ),
    "C": (
        "on",
        b"        contaminated = False\n",
        b"        contaminated = True\n",
        "_arm_observation on-arm contaminated derivation",
    ),
}

_ARTIFACT_JUDGMENT_OLD = (
    b'{"contaminated":false,"protocol_ok":true,"treatment_fired":true}'
)
_ARTIFACT_JUDGMENT_NEW = {
    "P": b'{"contaminated":false,"protocol_ok":false,"treatment_fired":true}',
    "T": b'{"contaminated":false,"protocol_ok":true,"treatment_fired":false}',
    "C": b'{"contaminated":true,"protocol_ok":true,"treatment_fired":true}',
}


def _mutation_specs() -> tuple[MutationSpec, ...]:
    rows: list[MutationSpec] = []
    order = 1
    for family in ("C0", "C1", "R", "D"):
        for judgment in ("P", "T", "C"):
            target_arm, old_bytes, new_bytes, position = _JUDGMENT_PATCHES[judgment]
            relative_path = PRODUCER_PATH
            if family in {"R", "D"}:
                target_arm = "on"
                old_bytes = _ARTIFACT_JUDGMENT_OLD
                new_bytes = _ARTIFACT_JUDGMENT_NEW[judgment]
                if family == "R":
                    relative_path = (
                        "<planned-attempt-artifact>/first/on/"
                        "judgment-projection"
                    )
                    position = (
                        "separate-path rogue producer writes the planned attempt "
                        "artifact first on-arm judgment projection"
                    )
                else:
                    relative_path = (
                        "<raw-analysis-records>/first/on/judgment-projection"
                    )
                    position = (
                        "post-assembly rewrite of the first on-arm raw-analysis "
                        "judgment projection"
                    )
            rows.append(
                MutationSpec(
                    mutation_id=f"{family}-{judgment}",
                    family=family,
                    judgment=judgment,
                    target_arm=target_arm,
                    relative_path=relative_path,
                    old_bytes=old_bytes,
                    new_bytes=new_bytes,
                    position=position,
                    order=order,
                    decision_input=family in {"C1", "R"},
                )
            )
            order += 1
    rows.append(
        MutationSpec(
            mutation_id="POS-1",
            family="POS",
            judgment="none",
            target_arm="none",
            relative_path=PRODUCER_PATH,
            old_bytes=b"",
            new_bytes=b"",
            position="normal producer and production route",
            order=order,
            decision_input=False,
        )
    )
    return tuple(rows)


MUTATIONS = _mutation_specs()
MUTATION_BY_ID = {mutation.mutation_id: mutation for mutation in MUTATIONS}
DECISION_MUTATION_IDS = frozenset(
    mutation.mutation_id for mutation in MUTATIONS if mutation.decision_input
)
CONTROL_MUTATION_IDS = frozenset(MUTATION_BY_ID) - DECISION_MUTATION_IDS


EXPECTED_GUARD_MATRIX: Mapping[str, Mapping[Candidate, CaseOutcome]] = {
    mutation.mutation_id: {
        candidate: (
            CaseOutcome.KILLED
            if mutation.family == "C0"
            or (
                mutation.family == "C1"
                and candidate in {Candidate.RAW_ASSEMBLY, Candidate.FROZEN_CONSUMER}
            )
            else CaseOutcome.SURVIVED
        )
        for candidate in Candidate
    }
    for mutation in MUTATIONS
}
EXPECTED_MATRIX: Mapping[str, Mapping[Candidate, CaseOutcome]] = {
    mutation_id: {
        candidate: (
            CaseOutcome.BASELINE_REJECTED
            if mutation_id.startswith("R-")
            else outcome
        )
        for candidate, outcome in row.items()
    }
    for mutation_id, row in EXPECTED_GUARD_MATRIX.items()
}


CHANGE_CLOSURES = {
    Candidate.ISSUER: ChangeClosure(Candidate.ISSUER, 2, 1, 2),
    Candidate.RAW_ASSEMBLY: ChangeClosure(Candidate.RAW_ASSEMBLY, 2, 1, 2),
    Candidate.FROZEN_CONSUMER: ChangeClosure(
        Candidate.FROZEN_CONSUMER, 4, 3, 5
    ),
}


_PRODUCER_NON_REGRESSION_NODE = (
    "orchestrator/tests/test_p3_b4_raw_record_producer.py"
)
_ISSUER_V1_COMPATIBILITY_NODE = (
    "orchestrator/tests/test_p3_b4_prerun_issuer.py::"
    "test_issue_publishes_complete_bundle_and_existing_consumers_reverify"
)
_FROZEN_PRODUCTION_ROUTE_NODE = (
    "orchestrator/tests/test_p3_b4_material_report.py::"
    "test_normal_path_assembles_binds_evaluates_and_builds_document"
)


def non_regression_node_ids(candidate: Candidate) -> tuple[str, ...]:
    nodes = [_PRODUCER_NON_REGRESSION_NODE]
    if candidate is Candidate.ISSUER:
        nodes.append(_ISSUER_V1_COMPATIBILITY_NODE)
    if candidate is Candidate.FROZEN_CONSUMER:
        nodes.append(_FROZEN_PRODUCTION_ROUTE_NODE)
    return tuple(nodes)


_ISSUER_PATCHES = (
    ExactPatch(
        Candidate.ISSUER,
        "orchestrator/campaign/p3_b4_prerun_issuer.py",
        b"from .attempt_registry_core import canonical_json_bytes\n",
        b"from .attempt_registry_core import canonical_json_bytes\n"
        b"from .p3_b4_producer_auth_experiment import (\n"
        b"    ProducerAuthRejection,\n"
        b"    guard_issuer,\n"
        b")\n",
        "module imports",
        1,
    ),
    ExactPatch(
        Candidate.ISSUER,
        "orchestrator/campaign/p3_b4_prerun_issuer.py",
        b"    SCHEDULED_INPUTS_INVALID = \"scheduled_inputs_invalid\"\n",
        b"    PRODUCER_AUTH_MISMATCH = \"producer_auth_mismatch\"\n"
        b"    SCHEDULED_INPUTS_INVALID = \"scheduled_inputs_invalid\"\n",
        "B4PrerunRejectionReason",
        2,
    ),
    ExactPatch(
        Candidate.ISSUER,
        "orchestrator/campaign/p3_b4_prerun_issuer.py",
        b"    \"\"\"Issue exactly one B-4 pre-run publication under a new absolute root.\"\"\"\n\n"
        b"    root = _canonical_absolute_path(\n",
        b"    \"\"\"Issue exactly one B-4 pre-run publication under a new absolute root.\"\"\"\n\n"
        b"    try:\n"
        b"        guard_issuer()\n"
        b"    except ProducerAuthRejection as exc:\n"
        b"        _reject(\n"
        b"            B4PrerunRejectionReason.PRODUCER_AUTH_MISMATCH,\n"
        b"            str(exc),\n"
        b"            cause=exc,\n"
        b"        )\n"
        b"    root = _canonical_absolute_path(\n",
        "issue_b4_prerun_publication entry",
        3,
    ),
)


_RAW_PATCHES = (
    ExactPatch(
        Candidate.RAW_ASSEMBLY,
        PRODUCER_PATH,
        b"from .p3_b4_prerun_issuer import (\n",
        b"from .p3_b4_producer_auth_experiment import (\n"
        b"    ProducerAuthRejection,\n"
        b"    guard_raw_assembly,\n"
        b")\n"
        b"from .p3_b4_prerun_issuer import (\n",
        "module imports",
        1,
    ),
    ExactPatch(
        Candidate.RAW_ASSEMBLY,
        PRODUCER_PATH,
        b"    IO_ERROR = \"io_error\"\n",
        b"    PRODUCER_AUTH_MISMATCH = \"producer_auth_mismatch\"\n"
        b"    IO_ERROR = \"io_error\"\n",
        "B4RawRecordIssueCode",
        2,
    ),
    ExactPatch(
        Candidate.RAW_ASSEMBLY,
        PRODUCER_PATH,
        b"    rejection_history: B4RawRecordRejectionHistory | None = None\n"
        b"    try:\n"
        b"        checked = _validated_publication(publication)\n",
        b"    rejection_history: B4RawRecordRejectionHistory | None = None\n"
        b"    try:\n"
        b"        guard_raw_assembly()\n"
        b"        checked = _validated_publication(publication)\n",
        "assemble_b4_raw_analysis entry",
        3,
    ),
    ExactPatch(
        Candidate.RAW_ASSEMBLY,
        PRODUCER_PATH,
        b"            rejection_history=rejection_history,\n"
        b"        )\n"
        b"    except _Reject as exc:\n"
        b"        rejection = _rejection(None, exc.issue)\n",
        b"            rejection_history=rejection_history,\n"
        b"        )\n"
        b"    except ProducerAuthRejection as exc:\n"
        b"        return B4RawRecordRejection(\n"
        b"            schema_version=B4_RAW_RECORD_REJECTION_SCHEMA_VERSION,\n"
        b"            attempt_id=None,\n"
        b"            issues=(B4RawRecordIssue(\n"
        b"                artifact=\"producer\",\n"
        b"                field=\"producer_auth\",\n"
        b"                code=B4RawRecordIssueCode.PRODUCER_AUTH_MISMATCH,\n"
        b"                detail=str(exc),\n"
        b"            ),),\n"
        b"        )\n"
        b"    except _Reject as exc:\n"
        b"        rejection = _rejection(None, exc.issue)\n",
        "assemble_b4_raw_analysis producer-auth rejection",
        4,
    ),
)


_CLOSURE_MEMBER_OLD = (
    b'    "orchestrator/campaign/p3_b4_analysis_prereg_consumer.py",\n'
    b")\n"
)
_CLOSURE_MEMBER_NEW = (
    b'    "orchestrator/campaign/p3_b4_analysis_prereg_consumer.py",\n'
    b'    "orchestrator/campaign/p3_b4_raw_record_producer.py",\n'
    b")\n"
)


_FROZEN_PATCHES = (
    ExactPatch(
        Candidate.FROZEN_CONSUMER,
        "orchestrator/campaign/p3_b4_analysis_path.py",
        _CLOSURE_MEMBER_OLD,
        _CLOSURE_MEMBER_NEW,
        "_SOURCE_CLOSURE_PATHS",
        1,
    ),
    ExactPatch(
        Candidate.FROZEN_CONSUMER,
        "orchestrator/campaign/p3_b4_analysis_prereg_consumer.py",
        _CLOSURE_MEMBER_OLD,
        _CLOSURE_MEMBER_NEW,
        "_CLOSURE_PATHS",
        2,
    ),
    ExactPatch(
        Candidate.FROZEN_CONSUMER,
        "orchestrator/campaign/p3_b4_material_report.py",
        b"from .p3_b4_analysis_path import evaluate_b4_artifacts\n",
        b"from .p3_b4_analysis_path import evaluate_b4_artifacts\n"
        b"from .p3_b4_analysis_prereg_consumer import (\n"
        b"    generate_verified_analysis_source_closure_receipt,\n"
        b")\n"
        b"from .p3_b4_producer_auth_experiment import (\n"
        b"    generate_experiment_closure_receipt,\n"
        b"    guard_frozen_consumer,\n"
        b")\n",
        "material-report imports",
        3,
    ),
    ExactPatch(
        Candidate.FROZEN_CONSUMER,
        "orchestrator/campaign/p3_b4_material_report.py",
        b"    result = evaluate_b4_artifacts(\n",
        b"    closure_receipt = generate_experiment_closure_receipt(\n"
        b"        generator=generate_verified_analysis_source_closure_receipt,\n"
        b"        repository_root=Path(__file__).resolve().parents[2],\n"
        b"    )\n"
        b"    guard_frozen_consumer(\n"
        b"        producer_sha256=closure_receipt.members[-1].sha256,\n"
        b"    )\n"
        b"    result = evaluate_b4_artifacts(\n",
        "material-report input construction before evaluate_b4_artifacts",
        4,
    ),
)


PROTOTYPE_PATCHES: Mapping[Candidate, tuple[ExactPatch, ...]] = {
    Candidate.ISSUER: _ISSUER_PATCHES,
    Candidate.RAW_ASSEMBLY: _RAW_PATCHES,
    Candidate.FROZEN_CONSUMER: _FROZEN_PATCHES,
}


def repository_root_from_module() -> Path:
    return Path(__file__).resolve().parents[2]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resolve_source_head(source_repository: Path) -> str:
    """Resolve the exact source commit used for every tree in one run."""

    completed = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD^{commit}"],
        cwd=source_repository,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    commit = completed.stdout.strip()
    if len(commit) not in {40, 64} or any(
        character not in "0123456789abcdef" for character in commit
    ):
        raise ScratchTreeError("source HEAD did not resolve to a canonical object id")
    return commit


def producer_blob_at_commit(
    source_repository: Path,
    base_commit: str,
) -> bytes:
    """Read the canonical producer from the measurement base commit."""

    try:
        commit = _validate_base_commit(base_commit)
    except ComparisonIntegrityError as exc:
        raise ScratchTreeError("base commit is not canonical") from exc
    completed = subprocess.run(
        ["git", "cat-file", "blob", f"{commit}:{PRODUCER_PATH}"],
        cwd=source_repository,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise ScratchTreeError(
            "producer blob is unavailable at the measurement base commit"
        )
    return completed.stdout


def resolve_candidate_trust_anchor(
    source_repository: Path,
    base_commit: str,
    candidate: Candidate,
) -> TrustAnchor:
    """Derive the post-prototype anchor from the pinned base commit blob."""

    data = producer_blob_at_commit(source_repository, base_commit)
    for patch in sorted(PROTOTYPE_PATCHES[candidate], key=lambda item: item.order):
        if patch.relative_path == PRODUCER_PATH:
            data = apply_exact_once(data, patch)
    return TrustAnchor(candidate, PRODUCER_PATH, sha256_bytes(data))


def _runtime_trust_anchor(candidate: Candidate) -> TrustAnchor:
    repository = repository_root_from_module()
    return resolve_candidate_trust_anchor(
        repository,
        resolve_source_head(repository),
        candidate,
    )


def _reject(candidate: Candidate, observed_sha256: str) -> NoReturn:
    raise ProducerAuthRejection(candidate, observed_sha256)


def _guard_repository_member(candidate: Candidate) -> None:
    anchor = _runtime_trust_anchor(candidate)
    try:
        observed = sha256_bytes(
            (repository_root_from_module() / anchor.producer_path).read_bytes()
        )
    except OSError:
        _reject(candidate, "unreadable")
    if observed != anchor.sha256:
        _reject(candidate, observed)


def guard_issuer() -> None:
    """Check the fixed producer bytes at the issuer boundary."""

    _guard_repository_member(Candidate.ISSUER)


def guard_raw_assembly() -> None:
    """Check the post-prototype producer bytes at the assembly boundary."""

    _guard_repository_member(Candidate.RAW_ASSEMBLY)


def guard_frozen_consumer(*, producer_sha256: str) -> None:
    """Check only the fixed digest of the already-required sixth member."""

    anchor = _runtime_trust_anchor(Candidate.FROZEN_CONSUMER)
    if producer_sha256 != anchor.sha256:
        _reject(Candidate.FROZEN_CONSUMER, producer_sha256)


def evaluate_with_measurement_floor(
    *,
    evaluator: Callable[..., object],
    evaluator_kwargs: Mapping[str, object],
) -> object:
    """Call the frozen evaluator with the ruled measurement-only floor zero."""

    if "floor" not in evaluator_kwargs or evaluator_kwargs["floor"] is not None:
        raise ValueError("material-report evaluator must supply absent floor")
    forwarded = dict(evaluator_kwargs)
    forwarded["floor"] = MEASUREMENT_FLOOR
    return evaluator(**forwarded)


def measurement_block_count(
    mutation: MutationSpec,
    *,
    prototype_enabled: bool,
) -> int:
    """Return the fixed preregistered design scale for every phase."""

    if MUTATION_BY_ID.get(mutation.mutation_id) is not mutation:
        raise ValueError("measurement mutation is not preregistered")
    if type(prototype_enabled) is not bool:
        raise TypeError("prototype_enabled must be bool")
    return REAL_REGIME_BLOCK_COUNT


def measurement_plan_value() -> dict[str, object]:
    """Return the stable scale and sharding contract shared by all artifacts."""

    return {
        "comparison_pair_count": len(MUTATIONS) * len(Candidate),
        "phase_count_per_shard": len(MUTATIONS),
        "phase_wall_time_field": "results[].wall_seconds",
        "phase_wall_time_unit": "seconds",
        "phases": [phase.value for phase in MeasurementPhase],
        "publication_block_count": REAL_REGIME_BLOCK_COUNT,
        "non_regression_measurements": [
            {
                "candidate": candidate.value,
                "execution_phase": MeasurementPhase.PROTOTYPE.value,
                "node_ids": list(non_regression_node_ids(candidate)),
                "producer_node_count": 29,
            }
            for candidate in Candidate
        ],
        "required_candidate_phase_shards": [
            {"candidate": candidate.value, "phase": phase.value}
            for candidate in Candidate
            for phase in MeasurementPhase
        ],
        "shard_unit": "candidate_x_phase",
    }


def generate_experiment_closure_receipt(
    *,
    generator: Callable[..., object],
    repository_root: Path,
) -> object:
    """Verify the temporary six-member closure at production design scale."""

    return generator(repository_root=repository_root)


def apply_exact_once(data: bytes, patch: ExactPatch | MutationSpec) -> bytes:
    """Apply one preregistered replacement after proving unique occurrence."""

    if not patch.old_bytes or patch.old_bytes == patch.new_bytes:
        raise ValueError("replacement must have nonempty, differing bytes")
    count = data.count(patch.old_bytes)
    if count != 1:
        raise ValueError(
            f"{patch.relative_path}:{patch.position}: old byte count is {count}, not 1"
        )
    return data.replace(patch.old_bytes, patch.new_bytes, 1)


def validate_exact_replacements(
    repository_root: Path,
    patches: Iterable[ExactPatch | MutationSpec],
) -> None:
    """Validate every old-byte anchor against its pre-application file."""

    by_path: dict[str, bytes] = {}
    for patch in sorted(patches, key=lambda item: item.order):
        if not patch.old_bytes:
            continue
        data = by_path.setdefault(
            patch.relative_path,
            (repository_root / patch.relative_path).read_bytes(),
        )
        by_path[patch.relative_path] = apply_exact_once(data, patch)


def apply_patches(repository_root: Path, patches: Sequence[ExactPatch]) -> None:
    """Apply an already validated ordered prototype patch set in place."""

    validate_exact_replacements(repository_root, patches)
    for patch in sorted(patches, key=lambda item: item.order):
        path = repository_root / patch.relative_path
        path.write_bytes(apply_exact_once(path.read_bytes(), patch))


def freeze_candidate_anchor_before_mutations(
    repository_root: Path,
    candidate: Candidate,
) -> TrustAnchor:
    """Require the base-blob anchor after prototype and before rogue mutation."""

    anchor = resolve_candidate_trust_anchor(
        repository_root,
        resolve_source_head(repository_root),
        candidate,
    )
    observed = sha256_bytes((repository_root / anchor.producer_path).read_bytes())
    if observed != anchor.sha256:
        raise PreregistrationError(
            f"{candidate.value} post-prototype producer sha256 differs: {observed}"
        )
    return anchor


def classify_case(
    *,
    candidate: Candidate,
    baseline: LayerObservation,
    prototype: LayerObservation,
) -> CaseOutcome:
    """Attribute a kill only to the enabled candidate guard, incrementally."""

    if any(
        is_environment_constant_reason(observation.reason)
        for observation in (baseline, prototype)
    ):
        return CaseOutcome.ENVIRONMENT_CONSTANT
    if baseline.guard_rejected:
        return CaseOutcome.ABORTED
    if baseline.existing_gate_rejected:
        return CaseOutcome.BASELINE_REJECTED
    if (
        prototype.guard_rejected
        and prototype.rejecting_candidate is candidate
    ):
        return CaseOutcome.KILLED
    return CaseOutcome.SURVIVED


def result_matches_registered_route(result: CandidateCaseResult) -> bool:
    """Check the exact layer and reason reached by a non-aborted measurement."""

    return (
        result.observed is not CaseOutcome.ABORTED
        and result.baseline
        == expected_phase_observation(
            candidate=result.candidate,
            mutation_id=result.mutation_id,
            phase=MeasurementPhase.BASELINE,
        )
        and result.prototype
        == expected_phase_observation(
            candidate=result.candidate,
            mutation_id=result.mutation_id,
            phase=MeasurementPhase.PROTOTYPE,
        )
    )


def expected_phase_observation(
    *,
    candidate: Candidate,
    mutation_id: str,
    phase: MeasurementPhase,
) -> LayerObservation:
    """Return the frozen layer observation for one candidate-case phase."""

    clean = LayerObservation(False, None, False, None)
    if mutation_id.startswith("R-"):
        return LayerObservation(
            False,
            None,
            True,
            "evidence_binding:source_rederivation",
        )
    if (
        phase is MeasurementPhase.PROTOTYPE
        and EXPECTED_MATRIX[mutation_id][candidate] is CaseOutcome.KILLED
    ):
        return LayerObservation(
            True,
            candidate,
            False,
            "producer_auth_mismatch",
        )
    return clean


def phase_result_matches_registered_route(result: CandidatePhaseResult) -> bool:
    """Check that a measured phase reached its preregistered layer and reason."""

    return result.observation == expected_phase_observation(
        candidate=result.candidate,
        mutation_id=result.mutation_id,
        phase=result.phase,
    )


def is_decision_input(mutation_id: str) -> bool:
    return mutation_id in DECISION_MUTATION_IDS


def decide_candidate(
    results: Sequence[CandidateCaseResult],
    *,
    non_regression: Mapping[Candidate, bool],
    closures: Mapping[Candidate, ChangeClosure] = CHANGE_CLOSURES,
) -> ComparisonDecision:
    """Fail closed before applying the six-case rule and closure tie breaker."""

    counts = {
        candidate: sum(
            result.incremental_kill
            for result in results
            if result.candidate is candidate
            and is_decision_input(result.mutation_id)
        )
        for candidate in Candidate
    }
    expected_keys = {
        (candidate, mutation.mutation_id)
        for mutation in MUTATIONS
        for candidate in Candidate
    }
    observed_keys = [(result.candidate, result.mutation_id) for result in results]
    blocking: list[str] = []
    if len(observed_keys) != len(set(observed_keys)):
        blocking.append("duplicate_candidate_mutation_result")
    if set(observed_keys) != expected_keys:
        blocking.append("candidate_mutation_matrix_incomplete")
    if any(result.observed is CaseOutcome.ABORTED for result in results):
        blocking.append("aborted_case_present")
    if any(
        result.observed is CaseOutcome.ENVIRONMENT_CONSTANT for result in results
    ):
        blocking.append("environment_constant_present")
    if any(result.observed is not result.expected for result in results):
        blocking.append("expected_observed_mismatch")
    base_commits = {result.base_commit for result in results}
    if len(base_commits) != 1:
        blocking.append("base_commit_missing_or_inconsistent")
    if set(non_regression) != set(Candidate):
        blocking.append("candidate_non_regression_incomplete")
    elif any(type(non_regression[candidate]) is not bool for candidate in Candidate):
        blocking.append("candidate_non_regression_ill_typed")

    ineligible = tuple(
        candidate
        for candidate in Candidate
        if non_regression.get(candidate) is False
    )
    eligible = tuple(
        candidate
        for candidate in Candidate
        if non_regression.get(candidate) is True
    )
    leaders: tuple[Candidate, ...] = ()
    if not blocking and eligible:
        maximum = max(counts[candidate] for candidate in eligible)
        tied = tuple(
            candidate for candidate in eligible if counts[candidate] == maximum
        )
        smallest_key = min(closures[candidate].tie_break_key for candidate in tied)
        leaders = tuple(
            candidate
            for candidate in tied
            if closures[candidate].tie_break_key == smallest_key
        )
    elif not blocking:
        blocking.append("no_non_regressing_candidate")

    return ComparisonDecision(
        base_commit=next(iter(base_commits)) if len(base_commits) == 1 else None,
        decision_available=not blocking,
        leaders=leaders,
        complete_candidate_exists=(
            not blocking
            and any(counts[candidate] == 6 for candidate in eligible)
        ),
        incremental_kills=tuple((candidate, counts[candidate]) for candidate in Candidate),
        non_regression=tuple(
            (candidate, non_regression.get(candidate) is True)
            for candidate in Candidate
        ),
        ineligible_candidates=ineligible,
        blocking_reasons=tuple(blocking),
    )


def _wire_observation(observation: LayerObservation) -> dict[str, object]:
    return {
        "existing_gate_rejected": observation.existing_gate_rejected,
        "guard_rejected": observation.guard_rejected,
        "reason": observation.reason,
        "rejecting_candidate": (
            None
            if observation.rejecting_candidate is None
            else observation.rejecting_candidate.value
        ),
    }


def _wire_result(result: CandidateCaseResult) -> dict[str, object]:
    mutation = MUTATION_BY_ID[result.mutation_id]
    return {
        "baseline": _wire_observation(result.baseline),
        "baseline_block_count": measurement_block_count(
            mutation, prototype_enabled=False
        ),
        "candidate": result.candidate.value,
        "expected": result.expected.value,
        "incremental_kill": result.incremental_kill,
        "mutation_id": result.mutation_id,
        "observed": result.observed.value,
        "prototype": _wire_observation(result.prototype),
        "prototype_block_count": measurement_block_count(
            mutation, prototype_enabled=True
        ),
    }


def _wire_trust_anchor(anchor: TrustAnchor) -> dict[str, object]:
    return {
        "candidate": anchor.candidate.value,
        "producer_path": anchor.producer_path,
        "sha256": anchor.sha256,
        "source": TRUST_ANCHOR_SOURCE,
    }


def _resolved_trust_anchors(
    *,
    source_repository: Path,
    base_commit: str,
) -> tuple[TrustAnchor, ...]:
    return tuple(
        resolve_candidate_trust_anchor(
            source_repository,
            base_commit,
            candidate,
        )
        for candidate in Candidate
    )


def comparison_report_value(
    *,
    results: Sequence[CandidateCaseResult],
    decision: ComparisonDecision,
    source_repository: Path | None = None,
) -> dict[str, object]:
    """Build the canonical, nonvolatile report value."""

    if decision.base_commit is None:
        raise ComparisonIntegrityError("comparison decision has no base commit")
    repository = source_repository or repository_root_from_module()
    anchors = _resolved_trust_anchors(
        source_repository=repository,
        base_commit=decision.base_commit,
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "base_commit": decision.base_commit,
        "decision_input_mutation_ids": sorted(DECISION_MUTATION_IDS),
        "control_mutation_ids": sorted(CONTROL_MUTATION_IDS),
        "evaluator_contract": measurement_evaluator_contract_value(),
        "trust_anchors": [_wire_trust_anchor(anchor) for anchor in anchors],
        "change_closures": [
            {
                "candidate": candidate.value,
                "production_file_count": CHANGE_CLOSURES[candidate].production_file_count,
                "production_file_count_basis": (
                    "candidate production callsite files plus the shared runtime "
                    "experiment module"
                ),
                "pin_site_count": CHANGE_CLOSURES[candidate].pin_site_count,
                "test_impact_file_count": CHANGE_CLOSURES[candidate].test_impact_file_count,
            }
            for candidate in Candidate
        ],
        "measurement_plan": measurement_plan_value(),
        "results": [
            _wire_result(result)
            for result in sorted(
                results,
                key=lambda item: (item.mutation_id, item.candidate.value),
            )
        ],
        "decision": {
            "available": decision.decision_available,
            "blocking_reasons": list(decision.blocking_reasons),
            "complete_candidate_exists": decision.complete_candidate_exists,
            "ineligible_candidates": [
                candidate.value for candidate in decision.ineligible_candidates
            ],
            "incremental_kills": [
                {"candidate": candidate.value, "count": count}
                for candidate, count in decision.incremental_kills
            ],
            "leaders": [candidate.value for candidate in decision.leaders],
            "non_regression": [
                {"candidate": candidate.value, "passed": passed}
                for candidate, passed in decision.non_regression
            ],
        },
        "non_guarantees": [
            (
                "KILLED and SURVIVED apply only to the C0, C1, R, and D "
                "injection positions at the P, T, and C judgment values and to "
                "POS-1; they do not generalize to other judgment values, arbitrary "
                "code mutations, coordinated rewrites, or path races."
            ),
            (
                "A matching path and SHA-256 shows only the repository bytes seen "
                "when a layer checked them; it does not prove that those bytes "
                "causally produced the artifact."
            ),
            (
                "Frozen-consumer measurements are values of a temporary six-member "
                "closure with an additional gate; they are neither rejection "
                "capability of the current five-file consumer nor evidence for "
                "production adoption."
            ),
            (
                "R-family raw-assembly rejections come from the existing source "
                "rederivation gate and are not incremental kills by the added guard."
            ),
            (
                "D-family survival leaves post-assembly modification outside every "
                "candidate, so none provides end-to-end authenticity."
            ),
            "The issuer cannot observe replacement of the producer after issuance.",
            (
                "The current five-file receipt hashes current bytes; it does not "
                "compare them with fixed expected digests."
            ),
            (
                "This measurement supplies floor=0, which the production route "
                "does not currently supply. Production passes floor=None and "
                "returns floor_domain_error because no authoritative floor "
                "artifact has been issued. Frozen-candidate values therefore "
                "measure rejection capability only when a floor is supplied; "
                "they are not current production behavior."
            ),
        ],
    }


def canonical_report_bytes(
    *,
    results: Sequence[CandidateCaseResult],
    decision: ComparisonDecision,
    source_repository: Path | None = None,
) -> bytes:
    return (
        json.dumps(
            comparison_report_value(
                results=results,
                decision=decision,
                source_repository=source_repository,
            ),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _strict_comparison_json(data: bytes) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise ComparisonIntegrityError(
                    f"comparison artifact contains duplicate key: {key}"
                )
            result[key] = value
        return result

    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ComparisonIntegrityError(
            "comparison artifact is not strict UTF-8 JSON"
        ) from exc


def _parse_observation(value: object) -> LayerObservation:
    if type(value) is not dict or set(value) != {
        "existing_gate_rejected",
        "guard_rejected",
        "reason",
        "rejecting_candidate",
    }:
        raise ComparisonIntegrityError("comparison observation has wrong shape")
    guard_rejected = value["guard_rejected"]
    existing_gate_rejected = value["existing_gate_rejected"]
    reason = value["reason"]
    rejecting_value = value["rejecting_candidate"]
    if type(guard_rejected) is not bool or type(existing_gate_rejected) is not bool:
        raise ComparisonIntegrityError("comparison observation flags are not bool")
    if reason is not None and type(reason) is not str:
        raise ComparisonIntegrityError("comparison observation reason is invalid")
    try:
        rejecting_candidate = (
            None if rejecting_value is None else Candidate(rejecting_value)
        )
        return LayerObservation(
            guard_rejected=guard_rejected,
            rejecting_candidate=rejecting_candidate,
            existing_gate_rejected=existing_gate_rejected,
            reason=reason,
        )
    except (TypeError, ValueError) as exc:
        raise ComparisonIntegrityError(
            "comparison observation candidate is invalid"
        ) from exc


def _parse_result(value: object, *, base_commit: str) -> CandidateCaseResult:
    if type(value) is not dict or set(value) != {
        "baseline",
        "baseline_block_count",
        "candidate",
        "expected",
        "incremental_kill",
        "mutation_id",
        "observed",
        "prototype",
        "prototype_block_count",
    }:
        raise ComparisonIntegrityError("comparison result has wrong shape")
    mutation_id = value["mutation_id"]
    if type(mutation_id) is not str or mutation_id not in MUTATION_BY_ID:
        raise ComparisonIntegrityError("comparison result mutation is unknown")
    mutation = MUTATION_BY_ID[mutation_id]
    if value["baseline_block_count"] != measurement_block_count(
        mutation, prototype_enabled=False
    ) or value["prototype_block_count"] != measurement_block_count(
        mutation, prototype_enabled=True
    ):
        raise ComparisonIntegrityError("comparison result scale is not preregistered")
    try:
        candidate = Candidate(value["candidate"])
        expected = CaseOutcome(value["expected"])
        observed = CaseOutcome(value["observed"])
        result = CandidateCaseResult(
            base_commit=base_commit,
            candidate=candidate,
            mutation_id=mutation_id,
            expected=expected,
            observed=observed,
            baseline=_parse_observation(value["baseline"]),
            prototype=_parse_observation(value["prototype"]),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, ComparisonIntegrityError):
            raise
        raise ComparisonIntegrityError("comparison result value is invalid") from exc
    if expected is not EXPECTED_MATRIX[mutation_id][candidate]:
        raise ComparisonIntegrityError("comparison result contradicts expected matrix")
    classified = classify_case(
        candidate=candidate,
        baseline=result.baseline,
        prototype=result.prototype,
    )
    aborted_reason_present = any(
        observation.reason is not None
        and observation.reason.startswith("case_aborted:")
        for observation in (result.baseline, result.prototype)
    )
    if (
        observed is CaseOutcome.ABORTED
        and not aborted_reason_present
    ) or (
        observed is not CaseOutcome.ABORTED
        and observed is not classified
    ):
        raise ComparisonIntegrityError(
            "comparison outcome does not follow its layer observations"
        )
    if observed is not CaseOutcome.ABORTED and not result_matches_registered_route(
        result
    ):
        raise ComparisonIntegrityError(
            "comparison did not reach the preregistered layer and reason"
        )
    if type(value["incremental_kill"]) is not bool or (
        value["incremental_kill"] is not result.incremental_kill
    ):
        raise ComparisonIntegrityError("comparison incremental kill is inconsistent")
    return result


def _validate_base_commit(value: object) -> str:
    if (
        type(value) is not str
        or len(value) not in {40, 64}
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ComparisonIntegrityError("comparison base commit is not canonical")
    return value


def _parse_trust_anchor(
    value: object,
    *,
    candidate: Candidate,
) -> TrustAnchor:
    if type(value) is not dict or set(value) != {
        "candidate",
        "producer_path",
        "sha256",
        "source",
    }:
        raise ComparisonIntegrityError("recorded trust anchor has wrong shape")
    if value["source"] != TRUST_ANCHOR_SOURCE:
        raise ComparisonIntegrityError("recorded trust anchor source is unknown")
    try:
        anchor = TrustAnchor(
            candidate=Candidate(value["candidate"]),
            producer_path=value["producer_path"],
            sha256=value["sha256"],
        )
    except (TypeError, ValueError) as exc:
        raise ComparisonIntegrityError("recorded trust anchor is invalid") from exc
    if anchor.candidate is not candidate:
        raise ComparisonIntegrityError("recorded trust anchor candidate differs")
    return anchor


def _assert_recorded_trust_anchor_matches_base_blob(
    value: object,
    *,
    source_repository: Path,
    base_commit: str,
    candidate: Candidate,
) -> TrustAnchor:
    recorded = _parse_trust_anchor(value, candidate=candidate)
    try:
        expected = resolve_candidate_trust_anchor(
            source_repository,
            base_commit,
            candidate,
        )
    except ScratchTreeError as exc:
        raise ComparisonIntegrityError(
            "recorded base commit producer blob is unavailable"
        ) from exc
    if recorded != expected:
        raise ComparisonIntegrityError(
            "recorded trust anchor does not match the base commit producer blob"
        )
    return recorded


def _wire_phase_result(result: CandidatePhaseResult) -> dict[str, object]:
    mutation = MUTATION_BY_ID[result.mutation_id]
    return {
        "block_count": measurement_block_count(
            mutation,
            prototype_enabled=result.phase is MeasurementPhase.PROTOTYPE,
        ),
        "classification": (
            CaseOutcome.ENVIRONMENT_CONSTANT.value
            if is_environment_constant_reason(result.observation.reason)
            else None
        ),
        "mutation_id": result.mutation_id,
        "observation": _wire_observation(result.observation),
        "wall_seconds": result.wall_seconds,
    }


def _parse_phase_result(
    value: object,
    *,
    base_commit: str,
    candidate: Candidate,
    phase: MeasurementPhase,
) -> CandidatePhaseResult:
    if type(value) is not dict or set(value) != {
        "block_count",
        "classification",
        "mutation_id",
        "observation",
        "wall_seconds",
    }:
        raise ComparisonIntegrityError("candidate phase result has wrong shape")
    mutation_id = value["mutation_id"]
    if type(mutation_id) is not str or mutation_id not in MUTATION_BY_ID:
        raise ComparisonIntegrityError("candidate phase mutation is unknown")
    if value["block_count"] != measurement_block_count(
        MUTATION_BY_ID[mutation_id],
        prototype_enabled=phase is MeasurementPhase.PROTOTYPE,
    ):
        raise ComparisonIntegrityError("candidate phase scale is not preregistered")
    try:
        result = CandidatePhaseResult(
            base_commit=base_commit,
            candidate=candidate,
            mutation_id=mutation_id,
            phase=phase,
            observation=_parse_observation(value["observation"]),
            wall_seconds=value["wall_seconds"],
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, ComparisonIntegrityError):
            raise
        raise ComparisonIntegrityError("candidate phase result is invalid") from exc
    expected_classification = (
        CaseOutcome.ENVIRONMENT_CONSTANT.value
        if is_environment_constant_reason(result.observation.reason)
        else None
    )
    if value["classification"] != expected_classification:
        raise ComparisonIntegrityError(
            "candidate phase classification is inconsistent"
        )
    return result


def canonical_candidate_shard_bytes(
    *,
    candidate: Candidate,
    phase: MeasurementPhase,
    results: Sequence[CandidatePhaseResult],
    non_regression_passed: bool | None,
    non_regression_wall_seconds: float | None,
    source_repository: Path | None = None,
) -> bytes:
    """Serialize one complete candidate x phase measurement shard."""

    selected = tuple(results)
    if any(
        result.candidate is not candidate or result.phase is not phase
        for result in selected
    ):
        raise ComparisonIntegrityError("candidate phase shard mixes conditions")
    mutation_ids = [result.mutation_id for result in selected]
    if len(mutation_ids) != len(set(mutation_ids)) or set(mutation_ids) != set(
        MUTATION_BY_ID
    ):
        raise ComparisonIntegrityError(
            "candidate phase shard does not contain 13 phases"
        )
    base_commits = {result.base_commit for result in selected}
    if len(base_commits) != 1:
        raise ComparisonIntegrityError(
            "candidate phase shard base commit is inconsistent"
        )
    base_commit = _validate_base_commit(next(iter(base_commits)))
    repository = source_repository or repository_root_from_module()
    anchor = resolve_candidate_trust_anchor(
        repository,
        base_commit,
        candidate,
    )
    if phase is MeasurementPhase.BASELINE:
        if non_regression_passed is not None or non_regression_wall_seconds is not None:
            raise ComparisonIntegrityError(
                "baseline shard must not carry prototype non-regression"
            )
        non_regression: dict[str, object] | None = None
    else:
        if type(non_regression_passed) is not bool or (
            type(non_regression_wall_seconds) is not float
            or not math.isfinite(non_regression_wall_seconds)
            or non_regression_wall_seconds < 0.0
        ):
            raise ComparisonIntegrityError(
                "prototype non-regression result or wall time is invalid"
            )
        non_regression = {
            "node_ids": list(non_regression_node_ids(candidate)),
            "passed": non_regression_passed,
            "producer_node_count": 29,
            "wall_seconds": non_regression_wall_seconds,
        }
    value = {
        "base_commit": base_commit,
        "candidate": candidate.value,
        "evaluator_contract": measurement_evaluator_contract_value(),
        "measurement_plan": measurement_plan_value(),
        "non_regression": non_regression,
        "phase": phase.value,
        "results": [
            _wire_phase_result(result)
            for result in sorted(
                selected, key=lambda item: MUTATION_BY_ID[item.mutation_id].order
            )
        ],
        "schema_version": SHARD_SCHEMA_VERSION,
        "trust_anchor": _wire_trust_anchor(anchor),
    }
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def parse_candidate_shard_bytes(
    data: bytes,
    *,
    source_repository: Path | None = None,
) -> tuple[
    Candidate,
    MeasurementPhase,
    tuple[CandidatePhaseResult, ...],
    bool | None,
    float | None,
]:
    """Load one canonical candidate x phase shard and rederive its content."""

    value = _strict_comparison_json(data)
    if type(value) is not dict or set(value) != {
        "base_commit",
        "candidate",
        "evaluator_contract",
        "measurement_plan",
        "non_regression",
        "phase",
        "results",
        "schema_version",
        "trust_anchor",
    }:
        raise ComparisonIntegrityError("candidate phase shard has wrong shape")
    if value["schema_version"] != SHARD_SCHEMA_VERSION:
        raise ComparisonIntegrityError("candidate phase shard schema is unknown")
    if value["evaluator_contract"] != measurement_evaluator_contract_value():
        raise ComparisonIntegrityError(
            "candidate phase shard evaluator contract differs"
        )
    if value["measurement_plan"] != measurement_plan_value():
        raise ComparisonIntegrityError("candidate phase shard measurement plan differs")
    base_commit = _validate_base_commit(value["base_commit"])
    try:
        candidate = Candidate(value["candidate"])
        phase = MeasurementPhase(value["phase"])
    except (TypeError, ValueError) as exc:
        raise ComparisonIntegrityError(
            "candidate phase shard condition is unknown"
        ) from exc
    repository = source_repository or repository_root_from_module()
    _assert_recorded_trust_anchor_matches_base_blob(
        value["trust_anchor"],
        source_repository=repository,
        base_commit=base_commit,
        candidate=candidate,
    )
    rows = value["results"]
    if type(rows) is not list:
        raise ComparisonIntegrityError("candidate phase results are not a list")
    results = tuple(
        _parse_phase_result(
            row,
            base_commit=base_commit,
            candidate=candidate,
            phase=phase,
        )
        for row in rows
    )
    non_regression = value["non_regression"]
    if phase is MeasurementPhase.BASELINE:
        if non_regression is not None:
            raise ComparisonIntegrityError(
                "baseline shard carries prototype non-regression"
            )
        passed = None
        non_regression_wall_seconds = None
    else:
        if type(non_regression) is not dict or set(non_regression) != {
            "node_ids",
            "passed",
            "producer_node_count",
            "wall_seconds",
        }:
            raise ComparisonIntegrityError(
                "prototype candidate non-regression has wrong shape"
            )
        passed = non_regression["passed"]
        non_regression_wall_seconds = non_regression["wall_seconds"]
        if (
            type(passed) is not bool
            or non_regression["node_ids"] != list(non_regression_node_ids(candidate))
            or non_regression["producer_node_count"] != 29
            or type(non_regression_wall_seconds) is not float
            or not math.isfinite(non_regression_wall_seconds)
            or non_regression_wall_seconds < 0.0
        ):
            raise ComparisonIntegrityError(
                "prototype candidate non-regression differs from plan"
            )
    if data != canonical_candidate_shard_bytes(
        candidate=candidate,
        phase=phase,
        results=results,
        non_regression_passed=passed,
        non_regression_wall_seconds=non_regression_wall_seconds,
        source_repository=repository,
    ):
        raise ComparisonIntegrityError("candidate phase shard is not canonical")
    return candidate, phase, results, passed, non_regression_wall_seconds


def combine_candidate_shards(
    shard_bytes: Sequence[bytes],
    *,
    preregistration_data: bytes,
    source_repository: Path | None = None,
) -> bytes:
    """Require all six candidate x phase shards before making a decision."""

    assert_preregistration_matches_registry(preregistration_data)
    by_shard: dict[
        tuple[Candidate, MeasurementPhase],
        tuple[tuple[CandidatePhaseResult, ...], bool | None],
    ] = {}
    repository = source_repository or repository_root_from_module()
    for data in shard_bytes:
        candidate, phase, phase_results, passed, _wall_seconds = (
            parse_candidate_shard_bytes(
                data,
                source_repository=repository,
            )
        )
        key = (candidate, phase)
        if key in by_shard:
            raise ComparisonIntegrityError("duplicate candidate phase shard")
        by_shard[key] = (phase_results, passed)
    required_shards = {
        (candidate, phase)
        for candidate in Candidate
        for phase in MeasurementPhase
    }
    if set(by_shard) != required_shards:
        raise ComparisonIntegrityError(
            "all six candidate phase shards are required"
        )
    phase_by_key = {
        (result.candidate, result.mutation_id, result.phase): result
        for phase_results, _passed in by_shard.values()
        for result in phase_results
    }
    base_commits = {result.base_commit for result in phase_by_key.values()}
    if len(base_commits) != 1:
        raise ComparisonIntegrityError(
            "candidate phase shard base commits are inconsistent"
        )
    results_list: list[CandidateCaseResult] = []
    for candidate in Candidate:
        positive_baseline = phase_by_key[
            (candidate, "POS-1", MeasurementPhase.BASELINE)
        ].observation
        if positive_baseline != LayerObservation(False, None, False, None):
            reason = positive_baseline.reason or "non-accepted observation"
            raise ComparisonIntegrityError(
                "POS-1 baseline did not reach accepted for "
                f"{candidate.value}: {reason}"
            )
        for mutation in MUTATIONS:
            baseline = phase_by_key[
                (candidate, mutation.mutation_id, MeasurementPhase.BASELINE)
            ].observation
            prototype = phase_by_key[
                (candidate, mutation.mutation_id, MeasurementPhase.PROTOTYPE)
            ].observation
            phase_aborted = any(
                observation.reason is not None
                and observation.reason.startswith("case_aborted:")
                for observation in (baseline, prototype)
            )
            observed = (
                CaseOutcome.ABORTED
                if phase_aborted
                else classify_case(
                    candidate=candidate,
                    baseline=baseline,
                    prototype=prototype,
                )
            )
            results_list.append(
                CandidateCaseResult(
                    base_commit=phase_by_key[
                        (candidate, mutation.mutation_id, MeasurementPhase.BASELINE)
                    ].base_commit,
                    candidate=candidate,
                    mutation_id=mutation.mutation_id,
                    expected=EXPECTED_MATRIX[mutation.mutation_id][candidate],
                    observed=observed,
                    baseline=baseline,
                    prototype=prototype,
                )
            )
    results = tuple(results_list)
    mismatches = [
        result for result in results if not result_matches_registered_route(result)
    ]
    if mismatches:
        first = mismatches[0]
        raise ComparisonIntegrityError(
            "candidate phases did not reach the preregistered layer and reason: "
            f"{first.candidate.value}/{first.mutation_id} "
            f"baseline={first.baseline.reason!r} prototype={first.prototype.reason!r}"
        )
    decision = decide_candidate(
        results,
        non_regression={
            candidate: bool(
                by_shard[(candidate, MeasurementPhase.PROTOTYPE)][1]
            )
            for candidate in Candidate
        },
    )
    if not decision.decision_available:
        raise ComparisonIntegrityError(
            "complete shards did not satisfy decision preconditions: "
            + ",".join(decision.blocking_reasons)
        )
    return canonical_report_bytes(
        results=results,
        decision=decision,
        source_repository=repository,
    )


def assert_recorded_comparison_matches_preregistration(
    data: bytes,
    *,
    preregistration_data: bytes,
    expected_base_commit: str | None = None,
    source_repository: Path | None = None,
) -> ComparisonDecision:
    """Recompute the complete decision from a recorded canonical report."""

    assert_preregistration_matches_registry(preregistration_data)
    value = _strict_comparison_json(data)
    if type(value) is not dict or type(value.get("results")) is not list:
        raise ComparisonIntegrityError("recorded comparison has wrong shape")
    base_commit = _validate_base_commit(value.get("base_commit"))
    if expected_base_commit is not None and base_commit != expected_base_commit:
        raise ComparisonIntegrityError("recorded comparison is from another commit")
    repository = source_repository or repository_root_from_module()
    trust_anchor_values = value.get("trust_anchors")
    if type(trust_anchor_values) is not list or len(trust_anchor_values) != len(
        Candidate
    ):
        raise ComparisonIntegrityError("recorded trust anchors have wrong shape")
    recorded_anchors = tuple(
        _assert_recorded_trust_anchor_matches_base_blob(
            anchor_value,
            source_repository=repository,
            base_commit=base_commit,
            candidate=candidate,
        )
        for candidate, anchor_value in zip(Candidate, trust_anchor_values)
    )
    if tuple(anchor.candidate for anchor in recorded_anchors) != tuple(Candidate):
        raise ComparisonIntegrityError("recorded trust anchors are out of order")
    results = tuple(
        _parse_result(row, base_commit=base_commit) for row in value["results"]
    )
    decision_value = value.get("decision")
    if type(decision_value) is not dict:
        raise ComparisonIntegrityError("recorded decision has wrong shape")
    non_regression_value = decision_value.get("non_regression")
    if type(non_regression_value) is not list:
        raise ComparisonIntegrityError("recorded non-regression is absent")
    non_regression: dict[Candidate, bool] = {}
    try:
        for row in non_regression_value:
            if type(row) is not dict or set(row) != {"candidate", "passed"}:
                raise ComparisonIntegrityError(
                    "recorded non-regression row has wrong shape"
                )
            candidate = Candidate(row["candidate"])
            if candidate in non_regression or type(row["passed"]) is not bool:
                raise ComparisonIntegrityError(
                    "recorded non-regression row is duplicate or invalid"
                )
            non_regression[candidate] = row["passed"]
    except (TypeError, ValueError) as exc:
        if isinstance(exc, ComparisonIntegrityError):
            raise
        raise ComparisonIntegrityError(
            "recorded non-regression candidate is unknown"
        ) from exc
    decision = decide_candidate(results, non_regression=non_regression)
    if not decision.decision_available:
        raise ComparisonIntegrityError(
            "recorded comparison does not satisfy decision preconditions"
        )
    if data != canonical_report_bytes(
        results=results,
        decision=decision,
        source_repository=repository,
    ):
        raise ComparisonIntegrityError(
            "recorded comparison is noncanonical or internally inconsistent"
        )
    return decision


def repository_status_bytes(repository_root: Path) -> bytes:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=repository_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def assert_repository_unchanged(repository_root: Path, before: bytes) -> None:
    after = repository_status_bytes(repository_root)
    if after != before:
        raise ScratchTreeError("main worktree status changed during experiment")


class ScratchTree:
    """One runtime-resolved, commit-pinned tree outside every worktree."""

    def __init__(
        self,
        *,
        source_repository: Path,
        scratch_root: Path = SCRATCH_ROOT,
        base_commit: str | None = None,
    ) -> None:
        self.source_repository = source_repository
        self.scratch_root = scratch_root
        self.base_commit = base_commit
        self.path: Path | None = None

    def __enter__(self) -> Path:
        try:
            self.scratch_root.mkdir(parents=True, exist_ok=True)
            path = Path(tempfile.mkdtemp(prefix="case-", dir=self.scratch_root))
            self.path = path
            base_commit = self.base_commit or resolve_source_head(
                self.source_repository
            )
            self.base_commit = base_commit
            archive = subprocess.Popen(
                ["git", "archive", "--format=tar", base_commit],
                cwd=self.source_repository,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert archive.stdout is not None
            extract = subprocess.run(
                ["tar", "-xf", "-", "-C", str(path)],
                stdin=archive.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            archive.stdout.close()
            archive_stderr = archive.stderr.read() if archive.stderr is not None else b""
            archive_rc = archive.wait()
            if archive_rc or extract.returncode:
                raise ScratchTreeError(
                    "base archive extraction failed: "
                    + (archive_stderr + extract.stderr).decode("utf-8", "replace")
                )
            common_dir = subprocess.run(
                [
                    "git",
                    "rev-parse",
                    "--path-format=absolute",
                    "--git-common-dir",
                ],
                cwd=self.source_repository,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            ).stdout.strip()
            subprocess.run(
                ["git", "init", "-q", str(path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            objects_info = path / ".git" / "objects" / "info"
            objects_info.mkdir(parents=True, exist_ok=True)
            (objects_info / "alternates").write_text(
                str(Path(common_dir) / "objects") + "\n",
                encoding="utf-8",
            )
            (path / ".git" / "HEAD").write_text(
                base_commit + "\n", encoding="ascii"
            )
            subprocess.run(
                ["git", "read-tree", base_commit],
                cwd=path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            for relative_path in EXPERIMENT_OVERLAY_PATHS:
                source = self.source_repository / relative_path
                target = path / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
            return path
        except Exception as exc:
            if self.path is not None:
                shutil.rmtree(self.path, ignore_errors=True)
                self.path = None
            if isinstance(exc, ScratchTreeError):
                raise
            raise ScratchTreeError(f"scratch tree creation failed: {exc}") from exc

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if self.path is None:
            return False
        path = self.path
        self.path = None
        try:
            shutil.rmtree(path)
        except OSError as cleanup_error:
            raise ScratchTreeError(
                f"scratch tree destruction failed: {cleanup_error}"
            ) from cleanup_error
        if path.exists():
            raise ScratchTreeError("scratch tree still exists after destruction")
        return False


def prepare_candidate_tree(repository_root: Path, candidate: Candidate) -> TrustAnchor:
    """Apply a prototype, then freeze its anchor before any rogue mutation."""

    patches = PROTOTYPE_PATCHES[candidate]
    apply_patches(repository_root, patches)
    return freeze_candidate_anchor_before_mutations(repository_root, candidate)


def _aborted_observation(phase: str, exc: Exception) -> LayerObservation:
    """Return a case-local failure with the complete exception message."""

    message = str(exc)
    return LayerObservation(
        guard_rejected=False,
        rejecting_candidate=None,
        existing_gate_rejected=False,
        reason=(
            f"case_aborted:{phase}:{type(exc).__name__}:message={message}"
        ),
    )


def run_isolated_cases(
    *,
    source_repository: Path,
    case_runner: Callable[[Path, Candidate, MutationSpec, bool], LayerObservation],
    candidate: Candidate,
    phase: MeasurementPhase,
    scratch_root: Path = SCRATCH_ROOT,
    mutations: Sequence[MutationSpec] = MUTATIONS,
) -> tuple[CandidatePhaseResult, ...]:
    """Run exactly one candidate x phase shard in disposable trees."""

    selected_mutations = tuple(mutations)
    if candidate not in set(Candidate):
        raise ValueError("candidate shard selection is unknown")
    if phase not in set(MeasurementPhase):
        raise ValueError("measurement phase is unknown")
    if (
        not selected_mutations
        or len(selected_mutations) != len(set(selected_mutations))
        or any(
            MUTATION_BY_ID.get(mutation.mutation_id) is not mutation
            for mutation in selected_mutations
        )
    ):
        raise ValueError("mutation shard selection is empty, duplicate, or unknown")

    preregistration_path = approved_preregistration_path(source_repository)
    try:
        preregistration_bytes = preregistration_path.read_bytes()
    except OSError as exc:
        raise PreregistrationError(
            "approved preregistration file is unavailable"
        ) from exc
    assert_preregistration_matches_registry(preregistration_bytes)
    base_commit = resolve_source_head(source_repository)
    main_before = repository_status_bytes(source_repository)
    results: list[CandidatePhaseResult] = []
    prototype_enabled = phase is MeasurementPhase.PROTOTYPE
    try:
        # Freeze the post-prototype anchor before this shard can apply a rogue
        # mutation. Baseline runs never install a candidate prototype.
        if prototype_enabled:
            with ScratchTree(
                source_repository=source_repository,
                scratch_root=scratch_root,
                base_commit=base_commit,
            ) as anchor_tree:
                prepare_candidate_tree(anchor_tree, candidate)
        for mutation in selected_mutations:
            started = time.monotonic()
            try:
                with ScratchTree(
                    source_repository=source_repository,
                    scratch_root=scratch_root,
                    base_commit=base_commit,
                ) as tree:
                    if prototype_enabled:
                        prepare_candidate_tree(tree, candidate)
                    observation = case_runner(
                        tree, candidate, mutation, prototype_enabled
                    )
            except Exception as exc:
                observation = _aborted_observation(phase.value, exc)
            wall_seconds = round(time.monotonic() - started, 6)
            results.append(
                CandidatePhaseResult(
                    base_commit=base_commit,
                    candidate=candidate,
                    mutation_id=mutation.mutation_id,
                    phase=phase,
                    observation=observation,
                    wall_seconds=wall_seconds,
                )
            )
    finally:
        assert_repository_unchanged(source_repository, main_before)
    return tuple(results)


def canonical_preregistration_bytes() -> bytes:
    """Render the executable registry for comparison with the approved file."""

    value = {
        "schema_version": PREREGISTRATION_SCHEMA_VERSION,
        "evaluator_contract": measurement_evaluator_contract_value(),
        "process_model": {
            "C1": (
                "issuance process exits before producer mutation; attempt "
                "production and assembly run in a new process"
            )
        },
        "trust_anchor_contract": {
            "digest": "sha256",
            "expected_bytes_source": TRUST_ANCHOR_SOURCE,
            "freeze_point": "after_candidate_prototype_before_rogue_mutation",
            "producer_path": PRODUCER_PATH,
        },
        "mutations": [
            {
                "decision_input": mutation.decision_input,
                "family": mutation.family,
                "judgment": mutation.judgment,
                "mutation_id": mutation.mutation_id,
                "new_hex": mutation.new_bytes.hex(),
                "old_hex": mutation.old_bytes.hex(),
                "order": mutation.order,
                "position": mutation.position,
                "relative_path": mutation.relative_path,
                "target_arm": mutation.target_arm,
            }
            for mutation in MUTATIONS
        ],
        "expectation_matrix": [
            {
                "mutation_id": mutation.mutation_id,
                "outcomes": {
                    candidate.value: EXPECTED_MATRIX[mutation.mutation_id][
                        candidate
                    ].value
                    for candidate in Candidate
                },
            }
            for mutation in MUTATIONS
        ],
        "measurement_plan": measurement_plan_value(),
        "decision_rule": {
            "controls": sorted(CONTROL_MUTATION_IDS),
            "inputs": sorted(DECISION_MUTATION_IDS),
            "preconditions": [
                "all_six_candidate_x_phase_shards_present",
                "exactly_one_result_for_each_of_13_mutations_x_3_candidates",
                "no_ABORTED_result",
                "every_observed_result_matches_its_approved_expectation",
                "non_regression_result_present_for_every_candidate",
                "POS-1_baseline_accepted_for_every_candidate",
            ],
            "selection": (
                "maximize incremental KILLED among non-regressing candidates; "
                "tie-break by production file count, pin site count, then test "
                "impact file count; retain all candidates if all keys tie"
            ),
        },
    }
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def approved_preregistration_path(repository_root: Path) -> Path:
    return repository_root / PREREGISTRATION_RELATIVE_PATH


def _strict_preregistration_json(data: bytes) -> object:
    """Parse approved bytes with duplicate-key rejection."""

    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise PreregistrationError(
                    f"preregistration contains duplicate key: {key}"
                )
            result[key] = value
        return result

    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PreregistrationError("preregistration is not strict UTF-8 JSON") from exc


def assert_preregistration_matches_registry(data: bytes) -> None:
    """Require the independent approved content to equal the full registry."""

    approved = _strict_preregistration_json(data)
    executable = _strict_preregistration_json(canonical_preregistration_bytes())
    if approved != executable:
        raise PreregistrationError(
            "approved preregistration content differs from executable registry"
        )


WAVE_MUTANTS = (
    WaveMutant(
        "W01",
        EXPERIMENT_PATH,
        b"    if observed != anchor.sha256:\n        _reject(candidate, observed)\n",
        b"    if observed == anchor.sha256:\n        _reject(candidate, observed)\n",
        "test_w01_fixed_anchor_accepts_regular_and_rejects_rogue",
    ),
    WaveMutant(
        "W02",
        EXPERIMENT_PATH,
        b"            baseline = phase_by_key[\n"
        b"                (candidate, mutation.mutation_id, MeasurementPhase.BASELINE)\n"
        b"            ].observation\n",
        b"            baseline = LayerObservation(False, None, False, None)\n",
        "test_w02_baseline_rejection_is_not_an_incremental_kill",
    ),
    WaveMutant(
        "W03",
        EXPERIMENT_PATH,
        b"        prototype.guard_rejected\n"
        b"        and prototype.rejecting_candidate is candidate\n",
        b"        prototype.guard_rejected\n"
        b"        and prototype.rejecting_candidate is not None\n",
        "test_w03_only_the_candidate_guard_can_own_a_kill",
    ),
    WaveMutant(
        "W04",
        EXPERIMENT_PATH,
        b"    finally:\n        assert_repository_unchanged(source_repository, main_before)\n",
        b"    finally:\n        pass\n",
        "test_w04_main_worktree_status_invariant_detects_change",
    ),
    WaveMutant(
        "W05",
        EXPERIMENT_PATH,
        b"    if producer_sha256 != anchor.sha256:\n",
        b"    if not producer_sha256:\n",
        "test_w05_frozen_predicate_is_digest_equality_only",
    ),
    WaveMutant(
        "W06",
        EXPERIMENT_PATH,
        b"def is_decision_input(mutation_id: str) -> bool:\n"
        b"    return mutation_id in DECISION_MUTATION_IDS\n",
        b"def is_decision_input(mutation_id: str) -> bool:\n"
        b"    return mutation_id in DECISION_MUTATION_IDS or mutation_id.startswith(\"D-\")\n",
        "test_w06_only_c1_and_r_are_decision_inputs",
    ),
    WaveMutant(
        "W07",
        EXPERIMENT_PATH,
        b"    if count != 1:\n",
        b"    if count < 1:\n",
        "test_w07_every_exact_replacement_requires_one_occurrence",
    ),
    WaveMutant(
        "W08",
        EXPERIMENT_PATH,
        b"    approved = _strict_preregistration_json(data)\n"
        b"    executable = _strict_preregistration_json(canonical_preregistration_bytes())\n",
        b"    approved = _strict_preregistration_json(canonical_preregistration_bytes())\n"
        b"    executable = _strict_preregistration_json(canonical_preregistration_bytes())\n",
        "test_w08_preregistration_is_rederived_from_content",
    ),
)


__all__ = [
    "CHANGE_CLOSURES",
    "COMPARISON_RELATIVE_PATH",
    "CONTROL_MUTATION_IDS",
    "Candidate",
    "CandidateCaseResult",
    "CandidatePhaseResult",
    "CaseOutcome",
    "ChangeClosure",
    "ComparisonDecision",
    "ComparisonIntegrityError",
    "DECISION_MUTATION_IDS",
    "EXPERIMENT_PATH",
    "EXPERIMENT_OVERLAY_PATHS",
    "EXPECTED_GUARD_MATRIX",
    "EXPECTED_MATRIX",
    "ExactPatch",
    "LayerObservation",
    "MEASUREMENT_FLOOR",
    "MeasurementPhase",
    "MUTATIONS",
    "MUTATION_BY_ID",
    "MutationSpec",
    "PRODUCER_PATH",
    "PROTOTYPE_PATCHES",
    "PreregistrationError",
    "PREREGISTRATION_RELATIVE_PATH",
    "ProducerAuthRejection",
    "REPORT_SCHEMA_VERSION",
    "REAL_REGIME_BLOCK_COUNT",
    "SCRATCH_ROOT",
    "SHARD_SCHEMA_VERSION",
    "ScratchTree",
    "ScratchTreeError",
    "TRUST_ANCHOR_SOURCE",
    "TrustAnchor",
    "WAVE_MUTANTS",
    "WaveMutant",
    "approved_preregistration_path",
    "apply_exact_once",
    "apply_patches",
    "analysis_invalid_observation_reason",
    "assert_preregistration_matches_registry",
    "assert_recorded_comparison_matches_preregistration",
    "assert_repository_unchanged",
    "canonical_preregistration_bytes",
    "canonical_candidate_shard_bytes",
    "canonical_report_bytes",
    "classify_case",
    "comparison_report_value",
    "decide_candidate",
    "evaluate_with_measurement_floor",
    "freeze_candidate_anchor_before_mutations",
    "generate_experiment_closure_receipt",
    "guard_frozen_consumer",
    "guard_issuer",
    "guard_raw_assembly",
    "is_decision_input",
    "is_environment_constant_reason",
    "measurement_block_count",
    "measurement_evaluator_contract_value",
    "measurement_plan_value",
    "non_regression_node_ids",
    "parse_candidate_shard_bytes",
    "phase_result_matches_registered_route",
    "prepare_candidate_tree",
    "producer_blob_at_commit",
    "repository_root_from_module",
    "repository_status_bytes",
    "result_matches_registered_route",
    "resolve_source_head",
    "resolve_candidate_trust_anchor",
    "run_isolated_cases",
    "sha256_bytes",
    "combine_candidate_shards",
    "validate_exact_replacements",
]
