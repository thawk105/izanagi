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
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Callable, Iterable, Mapping, NoReturn, Sequence


BASE_COMMIT = "4ec3eba04354f9ba86117a2dd488c72d007045e6"
SCRATCH_ROOT = Path("/work/1/SFC/tanab/t2103-scratch")
PRODUCER_PATH = "orchestrator/campaign/p3_b4_raw_record_producer.py"
EXPERIMENT_PATH = "orchestrator/campaign/p3_b4_producer_auth_experiment.py"
EXPERIMENT_OVERLAY_PATHS = (
    EXPERIMENT_PATH,
    "orchestrator/tests/p3_b4_rogue_producer_support.py",
    "orchestrator/tests/test_p3_b4_producer_auth_experiment.py",
)
PREREGISTRATION_SCHEMA_VERSION = "p3-b4-producer-auth-prereg/v2"
REPORT_SCHEMA_VERSION = "p3-b4-producer-auth-comparison/v2"
BASE_PRODUCER_SHA256 = (
    "55e264f05eef48e466a1ab20c97d9a7d30acba0afe3e76937e58411e17b1c790"
)


class Candidate(str, Enum):
    ISSUER = "issuer"
    RAW_ASSEMBLY = "raw_assembly"
    FROZEN_CONSUMER = "temporary_6_member_expanded_closure_prototype"


class CaseOutcome(str, Enum):
    KILLED = "KILLED"
    SURVIVED = "SURVIVED"
    BASELINE_REJECTED = "BASELINE_REJECTED"
    ABORTED = "ABORTED"


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


@dataclass(frozen=True, slots=True)
class CandidateCaseResult:
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
    leaders: tuple[Candidate, ...]
    complete_candidate_exists: bool
    incremental_kills: tuple[tuple[Candidate, int], ...]


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


def _mutation_specs() -> tuple[MutationSpec, ...]:
    rows: list[MutationSpec] = []
    order = 1
    for family in ("C0", "C1", "R", "D"):
        for judgment in ("P", "T", "C"):
            target_arm, old_bytes, new_bytes, position = _JUDGMENT_PATCHES[judgment]
            relative_path = PRODUCER_PATH
            if family in {"R", "D"}:
                field, old_value, new_value = {
                    "P": ("protocol_ok", b"true", b"false"),
                    "T": ("treatment_fired", b"true", b"false"),
                    "C": ("contaminated", b"false", b"true"),
                }[judgment]
                target_arm = "on"
                old_bytes = old_value
                new_bytes = new_value
                if family == "R":
                    relative_path = (
                        f"<planned-attempt-artifact>/first/on/raw/{field}"
                    )
                    position = "rogue attempt artifact first on-arm judgment"
                else:
                    relative_path = f"<raw-analysis-records>/first/on/{field}"
                    position = "post-assembly first on-arm judgment"
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
            and candidate is Candidate.RAW_ASSEMBLY
            else outcome
        )
        for candidate, outcome in row.items()
    }
    for mutation_id, row in EXPECTED_GUARD_MATRIX.items()
}


CHANGE_CLOSURES = {
    Candidate.ISSUER: ChangeClosure(Candidate.ISSUER, 1, 1, 2),
    Candidate.RAW_ASSEMBLY: ChangeClosure(Candidate.RAW_ASSEMBLY, 1, 1, 2),
    Candidate.FROZEN_CONSUMER: ChangeClosure(
        Candidate.FROZEN_CONSUMER, 3, 3, 5
    ),
}


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
        b"    \"\"\"Assemble all 201 planned attempt artifacts without writing "
        b"another path.\"\"\"\n\n"
        b"    try:\n"
        b"        checked = _validated_publication(publication)\n",
        b"    \"\"\"Assemble all 201 planned attempt artifacts without writing "
        b"another path.\"\"\"\n\n"
        b"    try:\n"
        b"        guard_raw_assembly()\n"
        b"        checked = _validated_publication(publication)\n",
        "assemble_b4_raw_analysis entry",
        3,
    ),
    ExactPatch(
        Candidate.RAW_ASSEMBLY,
        PRODUCER_PATH,
        b"    except _Reject as exc:\n"
        b"        return _rejection(None, exc.issue)\n",
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
        b"        return _rejection(None, exc.issue)\n",
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
        b"from .p3_b4_producer_auth_experiment import guard_frozen_consumer\n",
        "material-report imports",
        3,
    ),
    ExactPatch(
        Candidate.FROZEN_CONSUMER,
        "orchestrator/campaign/p3_b4_material_report.py",
        b"    result = evaluate_b4_artifacts(\n",
        b"    closure_receipt = generate_verified_analysis_source_closure_receipt(\n"
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


# Filled from the exact producer bytes after applying _RAW_PATCHES in order.
RAW_PROTOTYPE_PRODUCER_SHA256 = (
    "72c1c84e4a402dda2a8c43b98637221a2795fe5acb9977c8fc0f01b2eae6f34a"
)

TRUST_ANCHORS: Mapping[Candidate, TrustAnchor] = {
    Candidate.ISSUER: TrustAnchor(
        Candidate.ISSUER, PRODUCER_PATH, BASE_PRODUCER_SHA256
    ),
    Candidate.RAW_ASSEMBLY: TrustAnchor(
        Candidate.RAW_ASSEMBLY, PRODUCER_PATH, RAW_PROTOTYPE_PRODUCER_SHA256
    ),
    Candidate.FROZEN_CONSUMER: TrustAnchor(
        Candidate.FROZEN_CONSUMER, PRODUCER_PATH, BASE_PRODUCER_SHA256
    ),
}


def repository_root_from_module() -> Path:
    return Path(__file__).resolve().parents[2]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _reject(candidate: Candidate, observed_sha256: str) -> NoReturn:
    raise ProducerAuthRejection(candidate, observed_sha256)


def _guard_repository_member(candidate: Candidate) -> None:
    anchor = TRUST_ANCHORS[candidate]
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

    if producer_sha256 != TRUST_ANCHORS[Candidate.FROZEN_CONSUMER].sha256:
        _reject(Candidate.FROZEN_CONSUMER, producer_sha256)


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
    """Measure after prototype application and require the preregistered anchor."""

    anchor = TRUST_ANCHORS[candidate]
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


def decide_candidate(
    results: Sequence[CandidateCaseResult],
    closures: Mapping[Candidate, ChangeClosure] = CHANGE_CLOSURES,
) -> ComparisonDecision:
    """Apply the fixed six-case decision rule and fixed closure tie breaker."""

    counts = {
        candidate: sum(
            result.incremental_kill
            for result in results
            if result.candidate is candidate
            and result.mutation_id in DECISION_MUTATION_IDS
        )
        for candidate in Candidate
    }
    maximum = max(counts.values(), default=0)
    tied = tuple(candidate for candidate in Candidate if counts[candidate] == maximum)
    smallest_key = min(closures[candidate].tie_break_key for candidate in tied)
    leaders = tuple(
        candidate
        for candidate in tied
        if closures[candidate].tie_break_key == smallest_key
    )
    return ComparisonDecision(
        leaders=leaders,
        complete_candidate_exists=any(count == 6 for count in counts.values()),
        incremental_kills=tuple((candidate, counts[candidate]) for candidate in Candidate),
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


def comparison_report_value(
    *,
    results: Sequence[CandidateCaseResult],
    decision: ComparisonDecision,
) -> dict[str, object]:
    """Build the canonical, nonvolatile report value."""

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "base_commit": BASE_COMMIT,
        "decision_input_mutation_ids": sorted(DECISION_MUTATION_IDS),
        "control_mutation_ids": sorted(CONTROL_MUTATION_IDS),
        "trust_anchors": [
            {
                "candidate": candidate.value,
                "producer_path": TRUST_ANCHORS[candidate].producer_path,
                "sha256": TRUST_ANCHORS[candidate].sha256,
            }
            for candidate in Candidate
        ],
        "change_closures": [
            {
                "candidate": candidate.value,
                "production_file_count": CHANGE_CLOSURES[candidate].production_file_count,
                "pin_site_count": CHANGE_CLOSURES[candidate].pin_site_count,
                "test_impact_file_count": CHANGE_CLOSURES[candidate].test_impact_file_count,
            }
            for candidate in Candidate
        ],
        "results": [
            {
                "baseline": _wire_observation(result.baseline),
                "candidate": result.candidate.value,
                "expected": result.expected.value,
                "incremental_kill": result.incremental_kill,
                "mutation_id": result.mutation_id,
                "observed": result.observed.value,
                "prototype": _wire_observation(result.prototype),
            }
            for result in sorted(
                results,
                key=lambda item: (item.mutation_id, item.candidate.value),
            )
        ],
        "decision": {
            "complete_candidate_exists": decision.complete_candidate_exists,
            "incremental_kills": [
                {"candidate": candidate.value, "count": count}
                for candidate, count in decision.incremental_kills
            ],
            "leaders": [candidate.value for candidate in decision.leaders],
        },
        "non_guarantees": [
            "results_cover_only_C0_C1_R_D_at_P_T_C_and_POS_1",
            "path_and_sha256_do_not_prove_causal_artifact_provenance",
            "frozen_results_describe_only_the_temporary_6_member_prototype",
            "raw_R_rejections_by_source_rederivation_are_not_incremental_guard_kills",
            "D_survival_leaves_post_assembly_authenticity_unproved",
            "issuer_does_not_observe_post_issuance_producer_replacement",
            "the_current_5_file_receipt_hashes_current_bytes_without_fixed_expected_digests",
        ],
    }


def canonical_report_bytes(
    *,
    results: Sequence[CandidateCaseResult],
    decision: ComparisonDecision,
) -> bytes:
    return (
        json.dumps(
            comparison_report_value(results=results, decision=decision),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


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
    """One base-commit tree outside every registered worktree."""

    def __init__(
        self,
        *,
        source_repository: Path,
        scratch_root: Path = SCRATCH_ROOT,
    ) -> None:
        self.source_repository = source_repository
        self.scratch_root = scratch_root
        self.path: Path | None = None

    def __enter__(self) -> Path:
        try:
            self.scratch_root.mkdir(parents=True, exist_ok=True)
            path = Path(tempfile.mkdtemp(prefix="case-", dir=self.scratch_root))
            self.path = path
            archive = subprocess.Popen(
                ["git", "archive", "--format=tar", BASE_COMMIT],
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
            git_dir = subprocess.run(
                ["git", "rev-parse", "--absolute-git-dir"],
                cwd=self.source_repository,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            ).stdout.strip()
            (path / ".git").write_text(
                f"gitdir: {git_dir}\n",
                encoding="utf-8",
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


def run_isolated_cases(
    *,
    source_repository: Path,
    preregistration_path: Path,
    case_runner: Callable[[Path, Candidate, MutationSpec, bool], LayerObservation],
    scratch_root: Path = SCRATCH_ROOT,
) -> tuple[CandidateCaseResult, ...]:
    """Run baseline and prototype in distinct disposable trees for every case."""

    assert_preregistration_matches_registry(preregistration_path.read_bytes())
    main_before = repository_status_bytes(source_repository)
    results: list[CandidateCaseResult] = []
    try:
        # Freeze every post-prototype anchor before the first baseline or rogue
        # mutation is allowed to run anywhere in the experiment.
        for candidate in Candidate:
            with ScratchTree(
                source_repository=source_repository,
                scratch_root=scratch_root,
            ) as anchor_tree:
                prepare_candidate_tree(anchor_tree, candidate)
        for mutation in MUTATIONS:
            for candidate in Candidate:
                try:
                    with ScratchTree(
                        source_repository=source_repository,
                        scratch_root=scratch_root,
                    ) as baseline_tree:
                        baseline = case_runner(
                            baseline_tree, candidate, mutation, False
                        )
                    with ScratchTree(
                        source_repository=source_repository,
                        scratch_root=scratch_root,
                    ) as prototype_tree:
                        prepare_candidate_tree(prototype_tree, candidate)
                        prototype = case_runner(
                            prototype_tree, candidate, mutation, True
                        )
                except ScratchTreeError as exc:
                    aborted = LayerObservation(
                        guard_rejected=False,
                        rejecting_candidate=None,
                        existing_gate_rejected=False,
                        reason=f"scratch_aborted:{exc}",
                    )
                    results.append(
                        CandidateCaseResult(
                            candidate=candidate,
                            mutation_id=mutation.mutation_id,
                            expected=EXPECTED_MATRIX[mutation.mutation_id][candidate],
                            observed=CaseOutcome.ABORTED,
                            baseline=aborted,
                            prototype=aborted,
                        )
                    )
                    continue
                observed = classify_case(
                    candidate=candidate,
                    baseline=baseline,
                    prototype=prototype,
                )
                results.append(
                    CandidateCaseResult(
                        candidate=candidate,
                        mutation_id=mutation.mutation_id,
                        expected=EXPECTED_MATRIX[mutation.mutation_id][candidate],
                        observed=observed,
                        baseline=baseline,
                        prototype=prototype,
                    )
                )
    finally:
        assert_repository_unchanged(source_repository, main_before)
    return tuple(results)


def canonical_preregistration_bytes() -> bytes:
    """Render the reviewable preregistration; this is not its verifier."""

    lines = [
        f"schema: {PREREGISTRATION_SCHEMA_VERSION}",
        "process: C1 issuance and assembly use separate processes",
        "columns: id|family|judgment|arm|path|position|order|decision|old_hex|new_hex",
    ]
    for mutation in MUTATIONS:
        lines.append(
            "|".join(
                (
                    mutation.mutation_id,
                    mutation.family,
                    mutation.judgment,
                    mutation.target_arm,
                    mutation.relative_path,
                    mutation.position,
                    str(mutation.order),
                    "yes" if mutation.decision_input else "no",
                    mutation.old_bytes.hex(),
                    mutation.new_bytes.hex(),
                )
            )
        )
    lines.append("matrix: id|issuer|raw_assembly|frozen_consumer")
    for mutation in MUTATIONS:
        expected = EXPECTED_MATRIX[mutation.mutation_id]
        lines.append(
            "|".join(
                (
                    mutation.mutation_id,
                    expected[Candidate.ISSUER].value,
                    expected[Candidate.RAW_ASSEMBLY].value,
                    expected[Candidate.FROZEN_CONSUMER].value,
                )
            )
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _parse_preregistration(data: bytes) -> tuple[
    tuple[MutationSpec, ...],
    dict[str, dict[Candidate, CaseOutcome]],
]:
    """Rederive all registered content from approved bytes, never from a hash."""

    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise PreregistrationError("preregistration is not UTF-8") from exc
    if lines[:3] != [
        f"schema: {PREREGISTRATION_SCHEMA_VERSION}",
        "process: C1 issuance and assembly use separate processes",
        "columns: id|family|judgment|arm|path|position|order|decision|old_hex|new_hex",
    ]:
        raise PreregistrationError("preregistration header differs")
    try:
        matrix_index = lines.index(
            "matrix: id|issuer|raw_assembly|frozen_consumer", 3
        )
    except ValueError as exc:
        raise PreregistrationError("preregistration matrix header is absent") from exc
    mutations: list[MutationSpec] = []
    for line in lines[3:matrix_index]:
        columns = line.split("|")
        if len(columns) != 10:
            raise PreregistrationError("mutation row column count differs")
        (
            mutation_id,
            family,
            judgment,
            arm,
            path,
            position,
            order,
            decision,
            old_hex,
            new_hex,
        ) = columns
        try:
            old_bytes = bytes.fromhex(old_hex)
            new_bytes = bytes.fromhex(new_hex)
            parsed_order = int(order)
        except ValueError as exc:
            raise PreregistrationError("mutation row encoding differs") from exc
        mutations.append(
            MutationSpec(
                mutation_id=mutation_id,
                family=family,
                judgment=judgment,
                target_arm=arm,
                relative_path=path,
                old_bytes=old_bytes,
                new_bytes=new_bytes,
                position=position,
                order=parsed_order,
                decision_input={"yes": True, "no": False}.get(decision, False),
            )
        )
        if decision not in {"yes", "no"}:
            raise PreregistrationError("decision flag differs")
    matrix: dict[str, dict[Candidate, CaseOutcome]] = {}
    for line in lines[matrix_index + 1 :]:
        columns = line.split("|")
        if len(columns) != 4:
            raise PreregistrationError("matrix row column count differs")
        mutation_id, issuer, raw, frozen = columns
        try:
            matrix[mutation_id] = {
                Candidate.ISSUER: CaseOutcome(issuer),
                Candidate.RAW_ASSEMBLY: CaseOutcome(raw),
                Candidate.FROZEN_CONSUMER: CaseOutcome(frozen),
            }
        except ValueError as exc:
            raise PreregistrationError("matrix outcome differs") from exc
    return tuple(mutations), matrix


def assert_preregistration_matches_registry(data: bytes) -> None:
    """Compare fully rederived content with the independently executable registry."""

    mutations, matrix = _parse_preregistration(data)
    if mutations != MUTATIONS:
        raise PreregistrationError("rederived mutation content differs")
    expected_matrix = {
        mutation_id: dict(values)
        for mutation_id, values in EXPECTED_MATRIX.items()
    }
    if matrix != expected_matrix:
        raise PreregistrationError("rederived expectation matrix differs")


__all__ = [
    "BASE_COMMIT",
    "BASE_PRODUCER_SHA256",
    "CHANGE_CLOSURES",
    "CONTROL_MUTATION_IDS",
    "Candidate",
    "CandidateCaseResult",
    "CaseOutcome",
    "ChangeClosure",
    "ComparisonDecision",
    "DECISION_MUTATION_IDS",
    "EXPERIMENT_PATH",
    "EXPERIMENT_OVERLAY_PATHS",
    "EXPECTED_GUARD_MATRIX",
    "EXPECTED_MATRIX",
    "ExactPatch",
    "LayerObservation",
    "MUTATIONS",
    "MUTATION_BY_ID",
    "MutationSpec",
    "PRODUCER_PATH",
    "PROTOTYPE_PATCHES",
    "PreregistrationError",
    "ProducerAuthRejection",
    "REPORT_SCHEMA_VERSION",
    "RAW_PROTOTYPE_PRODUCER_SHA256",
    "SCRATCH_ROOT",
    "ScratchTree",
    "ScratchTreeError",
    "TRUST_ANCHORS",
    "TrustAnchor",
    "apply_exact_once",
    "apply_patches",
    "assert_preregistration_matches_registry",
    "assert_repository_unchanged",
    "canonical_preregistration_bytes",
    "canonical_report_bytes",
    "classify_case",
    "comparison_report_value",
    "decide_candidate",
    "freeze_candidate_anchor_before_mutations",
    "guard_frozen_consumer",
    "guard_issuer",
    "guard_raw_assembly",
    "prepare_candidate_tree",
    "repository_root_from_module",
    "repository_status_bytes",
    "run_isolated_cases",
    "sha256_bytes",
    "validate_exact_replacements",
]
