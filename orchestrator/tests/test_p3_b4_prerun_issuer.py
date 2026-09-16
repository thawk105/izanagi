from dataclasses import replace
import ast
import hashlib
import inspect
import json
import os
import stat
from pathlib import Path
from unittest import mock

import pytest

from orchestrator.campaign import p3_b4_analysis_ledgers as ledgers
from orchestrator.campaign import p3_b4_prerun_issuer as issuer
from orchestrator.campaign.p3_b4_analysis_contract import EXPECTED_BLOCK_COUNT


from p3_b4_proposal_binding_support import copy_preregistered_repository


def _publication_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = copy_preregistered_repository(tmp_path)
    monkeypatch.setattr(issuer, "_REPOSITORY_ROOT", tmp_path)
    return root


def _hash(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _attempt(
    index: int,
    *,
    reason: ledgers.B4ScheduledAttemptReason = ledgers.B4ScheduledAttemptReason.SCHEDULED,
    red_classes: tuple[ledgers.B4DigestRedClass, ...] = (
        ledgers.B4DigestRedClass.VERIFY_RED,
    ),
) -> ledgers.B4ScheduledAttemptInput:
    return ledgers.B4ScheduledAttemptInput(
        schema_version=ledgers.B4_SCHEDULED_ATTEMPT_SCHEMA_VERSION,
        attempt_id=f"attempt-{index:04d}",
        registry_ordinal=index,
        block_id=f"block-{index:04d}",
        driver="base-driver",
        reason=reason,
        whiteboard_result=ledgers.B4WhiteboardResult.REJECTED,
        digest_red_classes=red_classes,
        workload="calibrated-workload",
        calibrated_workload_member=True,
        initial_proposal_sha256=_hash(f"proposal-{index}"),
        bootstrap_member=True,
        reference_tps=(10_000 + index, 1),
        reference_snapshot_hash=_hash(f"snapshot-{index}"),
        reference_receipt_hash=_hash(f"receipt-{index}"),
        reference_is_unique=True,
        arm_digest_received=False,
    )


def _eligible_attempts(
    count: int = EXPECTED_BLOCK_COUNT,
) -> tuple[ledgers.B4ScheduledAttemptInput, ...]:
    return tuple(_attempt(index) for index in range(count))


def _planned(
    attempts: tuple[ledgers.B4ScheduledAttemptInput, ...],
    result_root: Path,
) -> tuple[issuer.B4PlannedResultArtifact, ...]:
    result_root.mkdir(parents=True, exist_ok=True)
    return tuple(
        issuer.B4PlannedResultArtifact(
            attempt_id=attempt.attempt_id,
            artifact_path=str(result_root / f"{attempt.attempt_id}.json"),
        )
        for attempt in attempts
    )


def _install_counted_seed(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    calls: list[int] = []

    def fake_token_bytes(count: int) -> bytes:
        calls.append(count)
        return bytes(range(count))

    monkeypatch.setattr(issuer.secrets, "token_bytes", fake_token_bytes)
    return calls


def _assert_reason(
    caught: pytest.ExceptionInfo[issuer.B4PrerunIssuerError],
    reason: issuer.B4PrerunRejectionReason,
) -> None:
    assert caught.value.reason is reason
    assert str(caught.value).startswith(f"{reason.value}:")


def _rewrite_planned_paths_and_all_bindings(
    publication: issuer.B4PrerunPublication,
    planned: tuple[issuer.B4PlannedResultArtifact, ...],
) -> None:
    receipt_path = Path(publication.receipt_path)
    receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    commitment = receipt_payload["issuer_commitment"]
    commitment["planned_result_artifacts"] = [
        {
            "attempt_id": item.attempt_id,
            "result_artifact_path": item.artifact_path,
        }
        for item in sorted(planned, key=lambda item: item.attempt_id)
    ]
    replacement_issuer_sha256 = hashlib.sha256(_canonical(commitment)).hexdigest()

    schedule_receipt = replace(
        publication.schedule_receipt,
        issuer_sha256=replacement_issuer_sha256,
    )
    registry = ledgers.seal_scheduled_attempt_registry(
        scheduled_inputs=publication.registry.scheduled_attempts,
        schedule_receipt=schedule_receipt,
    )
    seed_source = receipt_payload["seed_source"]
    seed_source["issuer_commitment_sha256"] = replacement_issuer_sha256
    seed_receipt = replace(
        publication.seed_receipt,
        registry_prefix_sha256=registry.sealed_prefix_sha256,
        issuer_sha256=replacement_issuer_sha256,
        source_receipt_sha256=hashlib.sha256(_canonical(seed_source)).hexdigest(),
    )
    manifest_result = ledgers.generate_analysis_manifest(
        registry=registry,
        schedule_receipt=schedule_receipt,
        seed_receipt=seed_receipt,
    )
    assert not isinstance(manifest_result, ledgers.B4DesignNotFeasible)
    manifest = manifest_result
    completeness = ledgers.assert_analysis_manifest_complete(
        registry=registry,
        manifest=manifest,
        schedule_receipt=schedule_receipt,
        seed_receipt=seed_receipt,
    )
    registry_bytes = registry.canonical_bytes
    manifest_bytes = manifest.canonical_bytes
    receipt_payload["issuer_commitment_sha256"] = replacement_issuer_sha256
    receipt_payload["registry_artifact"].update(
        sha256=hashlib.sha256(registry_bytes).hexdigest(),
        byte_count=len(registry_bytes),
        row_count=len(registry_bytes.splitlines()),
    )
    receipt_payload["manifest_artifact"].update(
        sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        byte_count=len(manifest_bytes),
        row_count=len(manifest.rows),
    )
    receipt_payload["completeness"] = {
        "schema_version": completeness.schema_version,
        "manifest_sha256": completeness.manifest_sha256,
        "registry_sha256": completeness.registry_sha256,
        "registry_prefix_sha256": completeness.registry_prefix_sha256,
        "schedule_issuer_sha256": completeness.schedule_issuer_sha256,
        "seed_issuer_sha256": completeness.seed_issuer_sha256,
        "row_count": completeness.row_count,
        "registry_violation_count": completeness.registry_violation_count,
    }
    Path(publication.registry_path).write_bytes(registry_bytes)
    Path(publication.manifest_path).write_bytes(manifest_bytes)
    receipt_path.write_bytes(_canonical(receipt_payload))


def test_issue_publishes_complete_bundle_and_existing_consumers_reverify(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    eligible = _eligible_attempts()
    exceptional = (
        _attempt(
            700,
            reason=ledgers.B4ScheduledAttemptReason.GENERATION_FAILED,
        ),
        _attempt(
            701,
            reason=ledgers.B4ScheduledAttemptReason.SCREENING_ONLY_RED,
            red_classes=(ledgers.B4DigestRedClass.SCREENING,),
        ),
    )
    attempts = eligible + exceptional
    planned = _planned(attempts, tmp_path / "results")
    publication_root = _publication_root(tmp_path, monkeypatch)
    calls = _install_counted_seed(monkeypatch)

    publication = issuer.issue_b4_prerun_publication(
        scheduled_inputs=attempts,
        planned_result_artifacts=planned,
        publication_root=str(publication_root),
    )

    expected_seed = bytes(range(32))
    expected_seed_sha256 = hashlib.sha256(expected_seed).hexdigest()
    assert calls == [32]
    assert publication.seed_receipt.seed_hex == expected_seed.hex()
    assert len(publication.registry.scheduled_attempts) == len(attempts)
    assert len(publication.manifest.rows) == EXPECTED_BLOCK_COUNT
    assert publication.completeness.row_count == EXPECTED_BLOCK_COUNT
    assert publication.schedule_receipt.issuer_sha256 == (
        publication.issuer_commitment_sha256
    )
    assert publication.seed_receipt.issuer_sha256 == (
        publication.issuer_commitment_sha256
    )
    assert publication.registry_path == str(
        publication_root / "scheduled-attempt-registry.jsonl"
    )
    assert publication.manifest_path == str(publication_root / "analysis-manifest.json")
    assert publication.receipt_path == str(
        publication_root / "prerun-issuer-receipt.json"
    )
    assert not (publication_root / ".prerun-issuer-receipt.tmp").exists()
    assert set(path.name for path in publication_root.iterdir()) == {
        "scheduled-attempt-registry.jsonl",
        "analysis-manifest.json",
        "prerun-issuer-receipt.json",
    }
    receipt_payload = json.loads(publication.receipt_canonical_bytes)
    assert receipt_payload["seed_source"]["seed_sha256"] == expected_seed_sha256
    assert (
        receipt_payload["issuer_commitment"]["seed_sha256"]
        == expected_seed_sha256
    )

    registry = ledgers.load_scheduled_attempt_registry(
        Path(publication.registry_path).read_bytes()
    )
    manifest = ledgers.load_analysis_manifest(Path(publication.manifest_path).read_bytes())
    completeness = ledgers.assert_analysis_manifest_complete(
        registry=registry,
        manifest=manifest,
        schedule_receipt=registry.schedule_receipt,
        seed_receipt=manifest.seed_receipt,
    )
    assert completeness == publication.completeness

    loaded = issuer.load_b4_prerun_publication(str(publication_root))
    assert loaded == publication
    assert loaded.planned_result_artifacts == tuple(
        sorted(planned, key=lambda item: item.attempt_id)
    )
    expected_non_guarantees = (
        "formal_launcher_not_wired_to_require_this_receipt",
        "unknown_or_missing_result_root_cannot_be_fully_preinspected",
        "publication_under_a_different_root_is_not_prevented",
        "csprng_uniformity_and_external_attestation_are_not_proven",
        "caller_schedule_is_not_bound_to_an_external_authoritative_population",
        "caller_result_paths_are_not_proven_formal_producer_paths",
        "issuer_commitment_hash_is_not_identity_signature_or_external_pin",
        "coordinated_rewrite_is_not_detected",
        "bind_mount_and_external_rename_races_are_not_excluded",
        "concurrent_result_writer_race_is_not_excluded",
        "file_drawer_risk_is_not_closed_end_to_end",
    )
    assert issuer.B4_PRERUN_NON_GUARANTEES == expected_non_guarantees
    assert receipt_payload["non_guarantees"] == list(expected_non_guarantees)
    assert loaded.non_guarantees == expected_non_guarantees
    assert loaded.non_guarantees == issuer.B4_PRERUN_NON_GUARANTEES
    assert "file_drawer_risk_is_not_closed_end_to_end" in loaded.non_guarantees


def test_real_repository_preregistered_publication_root() -> None:
    """The source checkout must include its real preregistration document."""
    repository = Path(__file__).resolve().parents[2]
    assert issuer._REPOSITORY_ROOT == repository
    document = (repository / "docs/phase3-b4-reflux-ablation-preregistration.md").read_bytes()
    declarations = [
        line for line in document.decode("utf-8").splitlines()
        if "B-4 prerun publication root" in line
    ]
    assert declarations == [
        "B-4 prerun publication root (repo 相対): `output/b4-prerun-publication`"
    ]
    assert issuer._preregistered_publication_root() == str(
        repository / "output/b4-prerun-publication"
    )


@pytest.mark.parametrize("sibling", ("different-publication", "b4-prerun-publication-extra"))
def test_non_preregistered_root_is_rejected_before_rng_or_root_inspection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sibling: str,
) -> None:
    expected = _publication_root(tmp_path, monkeypatch)
    root = expected.parent / sibling
    assert root.parent.is_dir()
    attempts = _eligible_attempts()
    planned = _planned(attempts, tmp_path / "results")
    with (
        mock.patch.object(issuer.secrets, "token_bytes", wraps=issuer.secrets.token_bytes) as rng,
        mock.patch.object(issuer, "_ensure_new_publication_root", wraps=issuer._ensure_new_publication_root) as inspect_root,
        pytest.raises(issuer.B4PrerunIssuerError) as caught,
    ):
        issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts, planned_result_artifacts=planned,
            publication_root=str(root),
        )
    _assert_reason(caught, issuer.B4PrerunRejectionReason.PUBLICATION_ROOT_NOT_PREREGISTERED)
    assert "does not match" in str(caught.value)
    assert rng.call_count == 0
    assert inspect_root.call_count == 0
    assert not root.exists()


@pytest.mark.parametrize("defect", ("missing", "duplicate", "ambiguous", "unreadable", "invalid-utf8"))
def test_preregistered_root_declaration_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str,
) -> None:
    root = _publication_root(tmp_path, monkeypatch)
    path = tmp_path / "docs/phase3-b4-reflux-ablation-preregistration.md"
    document = path.read_bytes()
    declaration = next(line for line in document.splitlines(keepends=True)
                       if b"B-4 prerun publication root" in line)
    if defect == "unreadable":
        path.unlink()
    elif defect == "invalid-utf8":
        path.write_bytes(document + b"\xff")
    else:
        replacement = {"missing": b"", "duplicate": declaration * 2,
                       "ambiguous": b" " + declaration}[defect]
        path.write_bytes(document.replace(declaration, replacement))
    attempts = _eligible_attempts()
    planned = _planned(attempts, tmp_path / "results")
    with (
        mock.patch.object(issuer.secrets, "token_bytes", wraps=issuer.secrets.token_bytes) as rng,
        mock.patch.object(issuer, "_ensure_new_publication_root", wraps=issuer._ensure_new_publication_root) as inspect_root,
        pytest.raises(issuer.B4PrerunIssuerError) as caught,
    ):
        issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts, planned_result_artifacts=planned,
            publication_root=str(root),
        )
    _assert_reason(caught, issuer.B4PrerunRejectionReason.PUBLICATION_ROOT_NOT_PREREGISTERED)
    detail = {"missing": "found 0", "duplicate": "found 2", "ambiguous": "malformed",
              "unreadable": "cannot read", "invalid-utf8": "not UTF-8"}[defect]
    assert detail in str(caught.value)
    assert rng.call_count == 0
    assert inspect_root.call_count == 0
    assert not root.exists()


def test_unplanned_attempt_is_rejected_before_rng_or_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    planned = list(_planned(attempts, tmp_path / "results"))
    planned[0] = replace(
        planned[0],
        attempt_id="attempt-unplanned",
    )
    assert len(planned) == len(attempts)
    assert len({item.attempt_id for item in planned}) == len(planned)
    assert {item.attempt_id for item in planned} != {
        item.attempt_id for item in attempts
    }
    publication_root = _publication_root(tmp_path, monkeypatch)
    calls = _install_counted_seed(monkeypatch)

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts,
            planned_result_artifacts=planned,
            publication_root=str(publication_root),
        )

    _assert_reason(
        caught,
        issuer.B4PrerunRejectionReason.PLANNED_RESULT_MAPPING_MISMATCH,
    )
    assert calls == []
    assert not publication_root.exists()


def test_replaced_seed_is_rejected_at_seed_source_edge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    publication_root = _publication_root(tmp_path, monkeypatch)
    _install_counted_seed(monkeypatch)
    publication = issuer.issue_b4_prerun_publication(
        scheduled_inputs=attempts,
        planned_result_artifacts=_planned(attempts, tmp_path / "results"),
        publication_root=str(publication_root),
    )
    manifest_path = Path(publication.manifest_path)
    receipt_path = Path(publication.receipt_path)
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_payload["seed_receipt"]["seed_hex"] = "55" * 32
    replaced_manifest = _canonical(manifest_payload)
    manifest_path.write_bytes(replaced_manifest)

    receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt_payload["manifest_artifact"]["sha256"] = hashlib.sha256(
        replaced_manifest
    ).hexdigest()
    receipt_payload["manifest_artifact"]["byte_count"] = len(replaced_manifest)
    receipt_path.write_bytes(_canonical(receipt_payload))

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.load_b4_prerun_publication(str(publication_root))

    _assert_reason(caught, issuer.B4PrerunRejectionReason.SEED_SOURCE_MISMATCH)


def test_source_receipt_reference_only_tamper_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    publication_root = _publication_root(tmp_path, monkeypatch)
    _install_counted_seed(monkeypatch)
    publication = issuer.issue_b4_prerun_publication(
        scheduled_inputs=attempts,
        planned_result_artifacts=_planned(attempts, tmp_path / "results"),
        publication_root=str(publication_root),
    )
    manifest_path = Path(publication.manifest_path)
    receipt_path = Path(publication.receipt_path)
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    old_source_sha256 = manifest_payload["seed_receipt"][
        "source_receipt_sha256"
    ]
    replacement_source_sha256 = "00" * 32
    assert replacement_source_sha256 != old_source_sha256
    manifest_payload["seed_receipt"][
        "source_receipt_sha256"
    ] = replacement_source_sha256
    replaced_manifest = _canonical(manifest_payload)
    manifest_path.write_bytes(replaced_manifest)

    receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    replacement_manifest_sha256 = hashlib.sha256(replaced_manifest).hexdigest()
    receipt_payload["manifest_artifact"]["sha256"] = (
        replacement_manifest_sha256
    )
    receipt_payload["manifest_artifact"]["byte_count"] = len(replaced_manifest)
    receipt_payload["completeness"]["manifest_sha256"] = (
        replacement_manifest_sha256
    )
    receipt_path.write_bytes(_canonical(receipt_payload))

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.load_b4_prerun_publication(str(publication_root))

    _assert_reason(caught, issuer.B4PrerunRejectionReason.SEED_SOURCE_MISMATCH)


@pytest.mark.parametrize("existing_kind", ("regular", "broken-symlink"))
def test_postresult_issuance_is_rejected_before_rng_or_publication(
    existing_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    planned = _planned(attempts, tmp_path / "results")
    exact_result_path = Path(planned[0].artifact_path)
    if existing_kind == "regular":
        exact_result_path.write_bytes(b"observed")
    else:
        os.symlink("missing-result-target", exact_result_path)
    publication_root = _publication_root(tmp_path, monkeypatch)
    calls = _install_counted_seed(monkeypatch)

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts,
            planned_result_artifacts=planned,
            publication_root=str(publication_root),
        )

    _assert_reason(
        caught,
        issuer.B4PrerunRejectionReason.RESULT_ARTIFACT_ALREADY_EXISTS,
    )
    assert calls == []
    assert not publication_root.exists()


def test_fewer_than_201_eligible_is_typed_before_root_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts(EXPECTED_BLOCK_COUNT - 1)
    publication_root = _publication_root(tmp_path, monkeypatch)
    calls = _install_counted_seed(monkeypatch)

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts,
            planned_result_artifacts=_planned(attempts, tmp_path / "results"),
            publication_root=str(publication_root),
        )

    _assert_reason(caught, issuer.B4PrerunRejectionReason.DESIGN_NOT_FEASIBLE)
    assert calls == [32]
    assert not publication_root.exists()


def test_duplicate_result_path_is_rejected_before_rng_or_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    planned = list(_planned(attempts, tmp_path / "results"))
    planned[1] = replace(planned[1], artifact_path=planned[0].artifact_path)
    publication_root = _publication_root(tmp_path, monkeypatch)
    calls = _install_counted_seed(monkeypatch)

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts,
            planned_result_artifacts=planned,
            publication_root=str(publication_root),
        )

    _assert_reason(
        caught,
        issuer.B4PrerunRejectionReason.PLANNED_RESULT_PATH_DUPLICATE,
    )
    assert calls == []
    assert not publication_root.exists()


def test_ancestor_result_paths_are_rejected_before_rng_or_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    planned = list(_planned(attempts, tmp_path / "results"))
    ancestor = tmp_path / "results" / "nested-result"
    planned[0] = replace(planned[0], artifact_path=str(ancestor))
    planned[1] = replace(
        planned[1],
        artifact_path=str(ancestor / "child.json"),
    )
    publication_root = _publication_root(tmp_path, monkeypatch)
    calls = _install_counted_seed(monkeypatch)

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts,
            planned_result_artifacts=planned,
            publication_root=str(publication_root),
        )

    _assert_reason(
        caught,
        issuer.B4PrerunRejectionReason.PLANNED_RESULT_PATH_INVALID,
    )
    assert calls == []
    assert not publication_root.exists()


def test_result_path_string_prefix_without_component_boundary_is_allowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    planned = list(_planned(attempts, tmp_path / "results"))
    prefix = tmp_path / "results" / "shared-prefix"
    planned[0] = replace(planned[0], artifact_path=str(prefix))
    planned[1] = replace(
        planned[1],
        artifact_path=str(tmp_path / "results" / "shared-prefix-child.json"),
    )
    publication_root = _publication_root(tmp_path, monkeypatch)

    publication = issuer.issue_b4_prerun_publication(
        scheduled_inputs=attempts,
        planned_result_artifacts=planned,
        publication_root=str(publication_root),
    )

    assert issuer.load_b4_prerun_publication(str(publication_root)) == publication


def test_result_path_symlink_component_is_rejected_before_rng(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    real_results = tmp_path / "real-results"
    real_results.mkdir()
    linked_results = tmp_path / "linked-results"
    linked_results.symlink_to(real_results, target_is_directory=True)
    planned = list(_planned(attempts, real_results))
    planned[0] = replace(
        planned[0],
        artifact_path=str(linked_results / "attempt-0000.json"),
    )
    calls = _install_counted_seed(monkeypatch)

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts,
            planned_result_artifacts=planned,
            publication_root=str(_publication_root(tmp_path, monkeypatch)),
        )

    _assert_reason(
        caught,
        issuer.B4PrerunRejectionReason.RESULT_PATH_SYMLINK_COMPONENT,
    )
    assert calls == []


@pytest.mark.parametrize(
    "fixed_artifact_name",
    (
        "scheduled-attempt-registry.jsonl",
        "analysis-manifest.json",
        "prerun-issuer-receipt.json",
        ".prerun-issuer-receipt.tmp",
        issuer.B4_RAW_RECORD_REJECTIONS_NAME,
    ),
)
def test_fixed_artifact_descendant_is_rejected_before_rng_or_publication(
    fixed_artifact_name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    publication_root = _publication_root(tmp_path, monkeypatch)
    planned = list(_planned(attempts, tmp_path / "results"))
    planned[0] = replace(
        planned[0],
        artifact_path=str(
            publication_root / fixed_artifact_name / "future-result.json"
        ),
    )
    calls = _install_counted_seed(monkeypatch)

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts,
            planned_result_artifacts=planned,
            publication_root=str(publication_root),
        )

    _assert_reason(
        caught,
        issuer.B4PrerunRejectionReason.PLANNED_RESULT_PATH_INVALID,
    )
    assert calls == []
    assert not publication_root.exists()


@pytest.mark.parametrize("conflict_kind", ("exact", "publication-root"))
def test_rejection_ledger_exact_path_and_publication_root_are_reserved(
    conflict_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    publication_root = _publication_root(tmp_path, monkeypatch)
    planned = list(_planned(attempts, tmp_path / "results"))
    conflict = (
        publication_root / issuer.B4_RAW_RECORD_REJECTIONS_NAME
        if conflict_kind == "exact"
        else publication_root
    )
    planned[0] = replace(planned[0], artifact_path=str(conflict))
    calls = _install_counted_seed(monkeypatch)

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts,
            planned_result_artifacts=planned,
            publication_root=str(publication_root),
        )

    _assert_reason(
        caught,
        issuer.B4PrerunRejectionReason.PLANNED_RESULT_PATH_INVALID,
    )
    assert calls == []
    assert not publication_root.exists()


def test_other_future_result_path_below_publication_root_is_allowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    publication_root = _publication_root(tmp_path, monkeypatch)
    planned = list(_planned(attempts, tmp_path / "results"))
    future_result = publication_root / "future-results" / "attempt-0000.json"
    planned[0] = replace(planned[0], artifact_path=str(future_result))
    calls = _install_counted_seed(monkeypatch)

    publication = issuer.issue_b4_prerun_publication(
        scheduled_inputs=attempts,
        planned_result_artifacts=planned,
        publication_root=str(publication_root),
    )

    assert calls == [32]
    assert not future_result.exists()
    assert issuer.load_b4_prerun_publication(str(publication_root)) == publication


@pytest.mark.parametrize("conflict_kind", ("exact", "descendant"))
def test_loader_rejects_fully_rebound_fixed_artifact_conflict(
    conflict_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    publication_root = _publication_root(tmp_path, monkeypatch)
    _install_counted_seed(monkeypatch)
    publication = issuer.issue_b4_prerun_publication(
        scheduled_inputs=attempts,
        planned_result_artifacts=_planned(attempts, tmp_path / "results"),
        publication_root=str(publication_root),
    )
    planned = list(publication.planned_result_artifacts)
    conflicting_path = Path(publication.receipt_path)
    if conflict_kind == "descendant":
        conflicting_path /= "future-result.json"
    planned[0] = replace(planned[0], artifact_path=str(conflicting_path))
    _rewrite_planned_paths_and_all_bindings(publication, tuple(planned))

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.load_b4_prerun_publication(str(publication_root))

    _assert_reason(
        caught,
        issuer.B4PrerunRejectionReason.PLANNED_RESULT_PATH_INVALID,
    )


@pytest.mark.parametrize("conflict_kind", ("exact", "descendant"))
def test_loader_rejects_fully_rebound_rejection_ledger_conflict(
    conflict_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    publication_root = _publication_root(tmp_path, monkeypatch)
    _install_counted_seed(monkeypatch)
    publication = issuer.issue_b4_prerun_publication(
        scheduled_inputs=attempts,
        planned_result_artifacts=_planned(attempts, tmp_path / "results"),
        publication_root=str(publication_root),
    )
    planned = list(publication.planned_result_artifacts)
    conflicting_path = (
        publication_root / issuer.B4_RAW_RECORD_REJECTIONS_NAME
    )
    if conflict_kind == "descendant":
        conflicting_path /= "future-result.json"
    planned[0] = replace(planned[0], artifact_path=str(conflicting_path))
    _rewrite_planned_paths_and_all_bindings(publication, tuple(planned))

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.load_b4_prerun_publication(str(publication_root))

    _assert_reason(
        caught,
        issuer.B4PrerunRejectionReason.PLANNED_RESULT_PATH_INVALID,
    )


def test_loader_rejects_fully_rebound_ancestor_result_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    publication_root = _publication_root(tmp_path, monkeypatch)
    _install_counted_seed(monkeypatch)
    publication = issuer.issue_b4_prerun_publication(
        scheduled_inputs=attempts,
        planned_result_artifacts=_planned(attempts, tmp_path / "results"),
        publication_root=str(publication_root),
    )
    planned = list(publication.planned_result_artifacts)
    ancestor = tmp_path / "tampered-results" / "nested-result"
    planned[0] = replace(planned[0], artifact_path=str(ancestor))
    planned[1] = replace(
        planned[1],
        artifact_path=str(ancestor / "child.json"),
    )
    _rewrite_planned_paths_and_all_bindings(publication, tuple(planned))

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.load_b4_prerun_publication(str(publication_root))

    _assert_reason(
        caught,
        issuer.B4PrerunRejectionReason.PLANNED_RESULT_PATH_INVALID,
    )


def test_same_publication_root_cannot_be_reissued(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    planned = _planned(attempts, tmp_path / "results")
    publication_root = _publication_root(tmp_path, monkeypatch)
    calls = _install_counted_seed(monkeypatch)
    issuer.issue_b4_prerun_publication(
        scheduled_inputs=attempts,
        planned_result_artifacts=planned,
        publication_root=str(publication_root),
    )

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts,
            planned_result_artifacts=planned,
            publication_root=str(publication_root),
        )

    _assert_reason(caught, issuer.B4PrerunRejectionReason.PUBLICATION_ROOT_EXISTS)
    assert calls == [32]


def test_competing_final_receipt_is_not_replaced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    publication_root = _publication_root(tmp_path, monkeypatch)
    sentinel_path = publication_root / "prerun-issuer-receipt.json"
    sentinel_bytes = b"competing-final-receipt-sentinel"
    original_read_relative = issuer._read_relative
    injected = False

    def read_and_inject_sentinel(root_fd: int, name: str) -> bytes:
        nonlocal injected
        data = original_read_relative(root_fd, name)
        if name == ".prerun-issuer-receipt.tmp" and not injected:
            sentinel_path.write_bytes(sentinel_bytes)
            injected = True
        return data

    monkeypatch.setattr(issuer, "_read_relative", read_and_inject_sentinel)

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts,
            planned_result_artifacts=_planned(attempts, tmp_path / "results"),
            publication_root=str(publication_root),
        )

    _assert_reason(caught, issuer.B4PrerunRejectionReason.PUBLICATION_IO_ERROR)
    assert injected
    assert sentinel_path.read_bytes() == sentinel_bytes


@pytest.mark.parametrize("failure_point", ("unlink", "directory-fsync", "close"))
def test_postlink_io_failure_is_commit_uncertain_and_loadable(
    failure_point: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    publication_root = _publication_root(tmp_path, monkeypatch)
    final_receipt = publication_root / "prerun-issuer-receipt.json"
    original_unlink = issuer.os.unlink
    original_fsync = issuer.os.fsync
    original_fstat = issuer.os.fstat
    original_close = issuer.os.close
    fault_injected = False

    def faulting_unlink(*args: object, **kwargs: object) -> None:
        nonlocal fault_injected
        if final_receipt.exists() and not fault_injected:
            fault_injected = True
            raise OSError("injected post-link unlink failure")
        original_unlink(*args, **kwargs)

    def faulting_fsync(fd: int) -> None:
        nonlocal fault_injected
        is_directory = stat.S_ISDIR(original_fstat(fd).st_mode)
        if final_receipt.exists() and is_directory and not fault_injected:
            fault_injected = True
            raise OSError("injected post-link directory fsync failure")
        original_fsync(fd)

    def faulting_close(fd: int) -> None:
        nonlocal fault_injected
        is_directory = stat.S_ISDIR(original_fstat(fd).st_mode)
        original_close(fd)
        if final_receipt.exists() and is_directory and not fault_injected:
            fault_injected = True
            raise OSError("injected post-link close failure")

    with monkeypatch.context() as patch:
        if failure_point == "unlink":
            patch.setattr(issuer.os, "unlink", faulting_unlink)
        elif failure_point == "directory-fsync":
            patch.setattr(issuer.os, "fsync", faulting_fsync)
        else:
            patch.setattr(issuer.os, "close", faulting_close)

        with pytest.raises(issuer.B4PrerunIssuerError) as caught:
            issuer.issue_b4_prerun_publication(
                scheduled_inputs=attempts,
                planned_result_artifacts=_planned(
                    attempts,
                    tmp_path / "results",
                ),
                publication_root=str(publication_root),
            )

    _assert_reason(
        caught,
        issuer.B4PrerunRejectionReason.PUBLICATION_COMMIT_UNCERTAIN,
    )
    assert fault_injected
    assert final_receipt.is_file()
    loaded = issuer.load_b4_prerun_publication(str(publication_root))
    assert loaded.receipt_canonical_bytes == final_receipt.read_bytes()


def test_publication_uses_parent_dirfd_and_closes_every_fd_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    publication_root = _publication_root(tmp_path, monkeypatch)
    planned = _planned(attempts, tmp_path / "results")
    original_open = issuer.os.open
    original_close = issuer.os.close
    original_mkdir = issuer.os.mkdir
    original_fsync = issuer.os.fsync
    original_fstat = issuer.os.fstat
    opened: list[tuple[int, int, object, int | None]] = []
    active: dict[int, int] = {}
    closed: list[int] = []
    mkdir_calls: list[tuple[object, int | None]] = []
    directory_fsyncs: list[int] = []

    def tracked_open(
        path: object,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        fd = original_open(path, flags, mode, dir_fd=dir_fd)
        assert fd not in active
        token = len(opened)
        active[fd] = token
        opened.append((token, fd, path, dir_fd))
        return fd

    def tracked_close(fd: int) -> None:
        assert fd in active
        closed.append(active.pop(fd))
        original_close(fd)

    def tracked_mkdir(
        path: object,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> None:
        mkdir_calls.append((path, dir_fd))
        original_mkdir(path, mode, dir_fd=dir_fd)

    def tracked_fsync(fd: int) -> None:
        if stat.S_ISDIR(original_fstat(fd).st_mode):
            directory_fsyncs.append(active[fd])
        original_fsync(fd)

    with monkeypatch.context() as patch:
        patch.setattr(issuer.os, "open", tracked_open)
        patch.setattr(issuer.os, "close", tracked_close)
        patch.setattr(issuer.os, "mkdir", tracked_mkdir)
        patch.setattr(issuer.os, "fsync", tracked_fsync)
        issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts,
            planned_result_artifacts=planned,
            publication_root=str(publication_root),
        )

    parent_open = next(
        event
        for event in opened
        if event[2] == str(publication_root.parent) and event[3] is None
    )
    root_open = next(
        event
        for event in opened
        if event[2] == publication_root.name and event[3] == parent_open[1]
    )
    assert mkdir_calls == [(publication_root.name, parent_open[1])]
    assert directory_fsyncs == [root_open[0], parent_open[0]]
    assert active == {}
    assert sorted(closed) == list(range(len(opened)))
    assert len(closed) == len(set(closed))


def test_float_commitment_count_is_not_equal_to_json_integer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    publication_root = _publication_root(tmp_path, monkeypatch)
    _install_counted_seed(monkeypatch)
    publication = issuer.issue_b4_prerun_publication(
        scheduled_inputs=attempts,
        planned_result_artifacts=_planned(attempts, tmp_path / "results"),
        publication_root=str(publication_root),
    )
    receipt_path = Path(publication.receipt_path)
    receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    commitment = receipt_payload["issuer_commitment"]
    commitment["scheduled_attempt_count"] = float(
        commitment["scheduled_attempt_count"]
    )
    replacement_issuer_sha256 = hashlib.sha256(
        _canonical(commitment)
    ).hexdigest()

    schedule_receipt = replace(
        publication.schedule_receipt,
        issuer_sha256=replacement_issuer_sha256,
    )
    registry = ledgers.seal_scheduled_attempt_registry(
        scheduled_inputs=publication.registry.scheduled_attempts,
        schedule_receipt=schedule_receipt,
    )
    seed_source = receipt_payload["seed_source"]
    seed_source["issuer_commitment_sha256"] = replacement_issuer_sha256
    seed_receipt = replace(
        publication.seed_receipt,
        registry_prefix_sha256=registry.sealed_prefix_sha256,
        issuer_sha256=replacement_issuer_sha256,
        source_receipt_sha256=hashlib.sha256(_canonical(seed_source)).hexdigest(),
    )
    manifest_result = ledgers.generate_analysis_manifest(
        registry=registry,
        schedule_receipt=schedule_receipt,
        seed_receipt=seed_receipt,
    )
    assert not isinstance(manifest_result, ledgers.B4DesignNotFeasible)
    manifest = manifest_result
    completeness = ledgers.assert_analysis_manifest_complete(
        registry=registry,
        manifest=manifest,
        schedule_receipt=schedule_receipt,
        seed_receipt=seed_receipt,
    )
    registry_bytes = registry.canonical_bytes
    manifest_bytes = manifest.canonical_bytes
    receipt_payload["issuer_commitment_sha256"] = replacement_issuer_sha256
    receipt_payload["registry_artifact"].update(
        sha256=hashlib.sha256(registry_bytes).hexdigest(),
        byte_count=len(registry_bytes),
        row_count=len(registry_bytes.splitlines()),
    )
    receipt_payload["manifest_artifact"].update(
        sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        byte_count=len(manifest_bytes),
        row_count=len(manifest.rows),
    )
    receipt_payload["completeness"] = {
        "schema_version": completeness.schema_version,
        "manifest_sha256": completeness.manifest_sha256,
        "registry_sha256": completeness.registry_sha256,
        "registry_prefix_sha256": completeness.registry_prefix_sha256,
        "schedule_issuer_sha256": completeness.schedule_issuer_sha256,
        "seed_issuer_sha256": completeness.seed_issuer_sha256,
        "row_count": completeness.row_count,
        "registry_violation_count": completeness.registry_violation_count,
    }
    Path(publication.registry_path).write_bytes(registry_bytes)
    Path(publication.manifest_path).write_bytes(manifest_bytes)
    receipt_path.write_bytes(_canonical(receipt_payload))

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.load_b4_prerun_publication(str(publication_root))

    _assert_reason(
        caught,
        issuer.B4PrerunRejectionReason.ISSUER_COMMITMENT_MISMATCH,
    )


def test_receipt_unknown_key_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    publication_root = _publication_root(tmp_path, monkeypatch)
    _install_counted_seed(monkeypatch)
    publication = issuer.issue_b4_prerun_publication(
        scheduled_inputs=attempts,
        planned_result_artifacts=_planned(attempts, tmp_path / "results"),
        publication_root=str(publication_root),
    )
    receipt_path = Path(publication.receipt_path)
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    payload["future_key"] = "not-accepted"
    receipt_path.write_bytes(_canonical(payload))

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.load_b4_prerun_publication(str(publication_root))

    _assert_reason(caught, issuer.B4PrerunRejectionReason.RECEIPT_SCHEMA_MISMATCH)


def test_partial_publication_root_is_poisoned_and_not_repaired(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = _eligible_attempts()
    planned = _planned(attempts, tmp_path / "results")
    publication_root = _publication_root(tmp_path, monkeypatch)
    publication_root.mkdir()
    calls = _install_counted_seed(monkeypatch)

    with pytest.raises(issuer.B4PrerunIssuerError) as caught:
        issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempts,
            planned_result_artifacts=planned,
            publication_root=str(publication_root),
        )

    _assert_reason(caught, issuer.B4PrerunRejectionReason.PUBLICATION_ROOT_EXISTS)
    assert calls == []
    assert list(publication_root.iterdir()) == []

    with pytest.raises(issuer.B4PrerunIssuerError) as load_caught:
        issuer.load_b4_prerun_publication(str(publication_root))
    _assert_reason(load_caught, issuer.B4PrerunRejectionReason.ARTIFACT_MISMATCH)


def test_public_api_has_no_external_seed_result_bool_or_caller_issuer_hash() -> None:
    parameters = inspect.signature(issuer.issue_b4_prerun_publication).parameters
    assert set(parameters) == {
        "scheduled_inputs",
        "planned_result_artifacts",
        "publication_root",
    }
    assert set(parameters).isdisjoint(
        {"seed", "seed_hex", "results_observed", "issuer_sha256"}
    )

    tree = ast.parse(inspect.getsource(issuer))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "secrets"
        and node.func.attr == "token_bytes"
    ]
    assert len(calls) == 1
    assert len(calls[0].args) == 1
    assert isinstance(calls[0].args[0], ast.Constant)
    assert calls[0].args[0].value == 32


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
