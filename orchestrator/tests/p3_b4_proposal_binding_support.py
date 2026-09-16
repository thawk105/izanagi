"""Real prerun-publication fixtures for B-4 bootstrap proposal binding tests."""
from __future__ import annotations

from contextlib import contextmanager
from unittest import mock
from dataclasses import dataclass
import hashlib
from pathlib import Path

from orchestrator.campaign import attempt_registry_core
from orchestrator.campaign import p3_b4_analysis_ledgers as ledgers
from orchestrator.campaign import p3_b4_prerun_issuer as issuer
from orchestrator.campaign.p3_b4_analysis_contract import EXPECTED_BLOCK_COUNT


_PREREGISTRATION_PATH = "docs/phase3-b4-reflux-ablation-preregistration.md"
_EXPECTED_PUBLICATION_ROOT = "output/b4-prerun-publication"


def copy_preregistered_repository(repository: Path) -> Path:
    """Copy the real document unchanged; the expected root is independently fixed."""
    source = Path(__file__).resolve().parents[2] / _PREREGISTRATION_PATH
    destination = repository / _PREREGISTRATION_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
    (repository / "output").mkdir(parents=True, exist_ok=True)
    return repository / _EXPECTED_PUBLICATION_ROOT


@contextmanager
def preregistered_publication_root(repository: Path):
    root = copy_preregistered_repository(repository)
    with mock.patch.object(issuer, "_REPOSITORY_ROOT", repository):
        yield root


@dataclass(frozen=True)
class ProposalBindingFixture:
    publication: issuer.B4PrerunPublication
    attempt_id: str
    document: dict[str, object]


def proposal_document(driver_kind: str, *, variant: int = 20) -> dict[str, object]:
    planner = {
        "axis": {
            "base": "silo-backoff-magnitude",
            "sort": "silo-writeset-sort",
            "trigger": "silo-backoff-trigger-gating",
        }[driver_kind],
        "direction": "increase",
        "magnitude": "small",
        "justification": "境界の正例",
    }
    if driver_kind == "base":
        coder = {
            "axis": planner["axis"],
            "value": variant,
            "implementation": f"double now_backoff = {variant};",
        }
        return {"planner": planner, "coder": coder}
    auditor = {"verdict": "pass", "diff_digest": "a" * 64}
    if driver_kind == "sort":
        coder = {
            "axis": planner["axis"],
            "implementation": f"int harmless_{variant} = {variant};",
        }
    else:
        coder = {
            "axis": planner["axis"],
            "wire": "00000" if variant == 20 else "00001",
        }
    return {"planner": planner, "coder": coder, "auditor": auditor}


def canonical_proposal_sha256(document: dict[str, object]) -> str:
    canonical_document = dict(document)
    canonical_document.pop("b4_closed_critic_receipt_sha256", None)
    return hashlib.sha256(
        attempt_registry_core.canonical_json_bytes(canonical_document)
    ).hexdigest()


def issue_proposal_binding_fixture(
    parent: Path,
    *,
    driver_kind: str,
    document: dict[str, object] | None = None,
    label: str = "binding",
    attempt_count: int = EXPECTED_BLOCK_COUNT,
    bound_attempt_index: int = 0,
) -> ProposalBindingFixture:
    if type(attempt_count) is not int or attempt_count <= 0:
        raise ValueError("attempt_count must be a positive integer")
    if (
        type(bound_attempt_index) is not int
        or not 0 <= bound_attempt_index < attempt_count
    ):
        raise ValueError("bound_attempt_index must identify an issued attempt")
    parent.mkdir(parents=True, exist_ok=True)
    bound_document = proposal_document(driver_kind) if document is None else document
    expected_hash = canonical_proposal_sha256(bound_document)
    attempts = tuple(
        ledgers.B4ScheduledAttemptInput(
            schema_version=ledgers.B4_SCHEDULED_ATTEMPT_SCHEMA_VERSION,
            attempt_id=f"{label}-attempt-{index:04d}",
            registry_ordinal=index,
            block_id=f"{label}-block-{index:04d}",
            driver=driver_kind,
            reason=ledgers.B4ScheduledAttemptReason.SCHEDULED,
            whiteboard_result=ledgers.B4WhiteboardResult.REJECTED,
            digest_red_classes=(ledgers.B4DigestRedClass.VERIFY_RED,),
            workload="calibrated-workload",
            calibrated_workload_member=True,
            initial_proposal_sha256=(
                expected_hash
                if index == bound_attempt_index
                else hashlib.sha256(
                    f"{label}-proposal-{index}".encode("ascii")
                ).hexdigest()
            ),
            bootstrap_member=True,
            reference_tps=(10_000 + index, 1),
            reference_snapshot_hash=hashlib.sha256(
                f"{label}-snapshot-{index}".encode("ascii")
            ).hexdigest(),
            reference_receipt_hash=hashlib.sha256(
                f"{label}-receipt-{index}".encode("ascii")
            ).hexdigest(),
            reference_is_unique=True,
            arm_digest_received=False,
        )
        for index in range(attempt_count)
    )
    result_root = parent / f"{label}-results"
    result_root.mkdir()
    planned = tuple(
        issuer.B4PlannedResultArtifact(
            attempt_id=attempt.attempt_id,
            artifact_path=str(result_root / f"{attempt.attempt_id}.json"),
        )
        for attempt in attempts
    )
    with preregistered_publication_root(parent / f"{label}-repository") as root:
        publication = issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts,
            planned_result_artifacts=planned,
            publication_root=str(root),
        )
    return ProposalBindingFixture(
        publication=publication,
        attempt_id=attempts[bound_attempt_index].attempt_id,
        document=bound_document,
    )


if __name__ == "__main__":
    import tempfile

    original_repository = issuer._REPOSITORY_ROOT
    with tempfile.TemporaryDirectory() as directory:
        parent = Path(directory)
        fixture = issue_proposal_binding_fixture(parent, driver_kind="base")
        assert fixture.publication.publication_root == str(
            parent / "binding-repository/output/b4-prerun-publication"
        )
        assert issuer.load_b4_prerun_publication(
            fixture.publication.publication_root
        ) == fixture.publication
        assert issuer._REPOSITORY_ROOT == original_repository
    print("p3_b4_proposal_binding_support.py::__main__: real fixture and loader passed")
