from __future__ import annotations

import contextlib
import copy
from dataclasses import dataclass, replace
import fcntl
import functools
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest import mock

import pytest

from orchestrator.campaign import (
    campaign_lock,
    contract_loader_binding,
    env_contract,
    ident,
)
from orchestrator.campaign import p3_b4_closed_critic as C
from orchestrator.campaign import p3_b4_prerun_issuer as issuer
from orchestrator.campaign import p3_b4_raw_record_producer as P
from orchestrator.campaign import p3_s4_loop as L
from orchestrator.campaign import wal
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.campaign.model import Genome, STAGE_ABORT, STAGE_BUILD_START
from orchestrator.campaign.build_admission import (
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.p3_b4_analysis_adapter import parse_raw_analysis_records
from orchestrator.campaign.p3_b4_analysis_contract import EXPECTED_BLOCK_COUNT
from orchestrator.campaign.p3_b4_analysis_path import evaluate_b4_artifacts
from orchestrator.campaign.p3_b4_analysis_ledgers import build_contract_binding
from orchestrator.campaign.pipeline import variant_id
from orchestrator.campaign.source_digest import EMPTY_TRACKED_DIFF_SHA256, SourceEvidence
from campaign_lock_test_support import build_v2_lock
import commit_receipt_support
from test_p3_b4_closed_critic import (
    _committed_admission_fixture,
    _fake_runner_factory,
    _make_admitted_fixture,
    _marked_driver_configs,
    _production_launch_context,
)
from test_p3_b4_prerun_issuer import _eligible_attempts, _planned


@dataclass(frozen=True)
class _Evidence:
    admission: object
    on_cfg: object
    off_cfg: object
    on_layout: CampaignLayout
    off_layout: CampaignLayout
    on_receipt: Path
    off_receipt: Path
    iteration: int


@dataclass(frozen=True)
class _SharedAdmission:
    repository: Path
    role_file: Path
    record_path: Path


@dataclass(frozen=True)
class _WriterAuthority:
    binding: object
    activation_state: object


_CLEAN_GENOME = Genome("silo", {
    "NO_WAIT_LOCKING_IN_VALIDATION": 1,
    "NO_WAIT_OF_TICTOC": 0,
    "WAL": 0,
    "BACK_OFF": 1,
    "BACKOFF_FIXED": 20,
})

_REAL_VERIFY_ADMISSION = C.verify_b4_admission_record


@functools.lru_cache(maxsize=None)
def _writer_authority() -> _WriterAuthority:
    binding = contract_loader_binding.capture_contract_loader_binding()
    contract_loader_binding.verify_live_contract_loader_binding(binding)
    return _WriterAuthority(
        binding=binding,
        activation_state=env_contract.verified_current_activation_state(),
    )


@functools.lru_cache(maxsize=None)
def _verified_admission(record_path: str, repository_root: str):
    return _REAL_VERIFY_ADMISSION(
        record_path,
        repository_root=repository_root,
    )


def _cached_verify_admission(admission_record_path, *, repository_root):
    return _verified_admission(
        os.fspath(admission_record_path),
        os.fspath(repository_root),
    )


def _publication(
    root: Path,
    *,
    reference_override: tuple[int, int] | None = None,
    driver_override: str | None = None,
) -> issuer.B4PrerunPublication:
    attempts = [
        replace(
            attempt,
            driver="base" if driver_override is None else driver_override,
            reference_tps=(100_001 + index * 10, 10),
        )
        for index, attempt in enumerate(_eligible_attempts())
    ]
    if reference_override is not None:
        attempts[0] = replace(attempts[0], reference_tps=reference_override)
    attempt_tuple = tuple(attempts)
    return issuer.issue_b4_prerun_publication(
        scheduled_inputs=attempt_tuple,
        planned_result_artifacts=_planned(attempt_tuple, root / "results"),
        publication_root=str(root / "publication"),
    )


def _copy_precursor_with_writers(
    source: CampaignLayout,
    target: CampaignLayout,
    target_cfg,
) -> None:
    target.ensure()
    for record in wal.read_records(source):
        wal.append(target, record)
    authority = _writer_authority()
    binding = authority.binding
    activation_state = authority.activation_state
    contract = target_cfg.bound_environment_contract
    assert contract is not None
    wal.write_lock(
        target,
        campaign_lock.encode_campaign_lock_v2(
            ident.canonical_preimage(target_cfg),
            campaign_lock.CampaignLockAuthority(
                environment_contract_sha256=contract.contract_sha256,
                activation_serial=activation_state.activation_serial,
                activation_state_sha256=activation_state.activation_state_sha256,
                contract_loader_commit=binding.contract_loader_commit,
                contract_loader_blob_sha256s=dict(
                    binding.contract_loader_blob_sha256s
                ),
            ),
        ),
    )
    source_state = L.load_loop_state(source)
    assert source_state is not None
    L.save_loop_state(target, source_state)


def _make_clean_admitted_fixture(
    root: Path,
    cfg,
    *,
    source_tag: str,
    iteration: int,
) -> CampaignLayout:
    """Write a policy-admitted BUILD_START with no red-class terminal entry."""

    layout = CampaignLayout(str(root)).ensure()
    src_token = hashlib.sha256(source_tag.encode("utf-8")).hexdigest()
    evidence = SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=os.path.realpath(layout.root),
        ccbench_commit=L.PIN,
        genome_sha256=hashlib.sha256(
            _CLEAN_GENOME.canonical().encode("utf-8")
        ).hexdigest(),
        src_token=src_token,
        source_bytes_sha256=hashlib.sha256(
            f"b4-clean-source:{source_tag}".encode("utf-8")
        ).hexdigest(),
        tracked_clean=False,
        tracked_diff_sha256=hashlib.sha256(
            f"b4-clean-diff:{source_tag}".encode("utf-8")
        ).hexdigest(),
        tracked_paths=("include/b4-clean-fixture.hh",),
    )
    assert evidence.tracked_diff_sha256 != EMPTY_TRACKED_DIFF_SHA256
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    capability = attest_generator_output(
        context,
        evidence,
        generator_input_sha256=hashlib.sha256(
            f"b4-clean-input:{source_tag}".encode("utf-8")
        ).hexdigest(),
    )
    admission = derive_build_admission(
        context,
        evidence,
        generator_receipt=capability,
    )
    receipt = admission.as_wal_receipt()
    candidate = variant_id(_CLEAN_GENOME, src_token)
    wal.log(
        layout,
        candidate,
        STAGE_BUILD_START,
        L.ENV_TAG,
        {
            "genome": _CLEAN_GENOME.canonical(),
            "src_token": src_token,
            "build_attempt_id": f"{source_tag}-attempt",
            "build_admission": receipt,
            "build_admission_receipt_sha256": receipt["receipt_sha256"],
        },
    )
    wal.write_lock(layout, build_v2_lock(ident.canonical_preimage(cfg)))
    state = L.LoopState(iteration=iteration, start_wall=1.0)
    state.whiteboard.append(L.WhiteboardEntry(
        iteration=iteration,
        direction="increase",
        magnitude="small",
        result="rejected",
        delta_pct=None,
    ))
    L.save_loop_state(layout, state)
    return layout


def _commit_with_decimal_lexeme(
    layout: CampaignLayout,
    *,
    ts: float,
    operation_identity: str,
) -> None:
    real = wal._record_to_line

    def lexical_writer(record):
        line = real(record)
        if RECEIPT_MARKER in line:
            assert '"fitness_tps":0.1' in line
            return line.replace(
                '"fitness_tps":0.1',
                '"fitness_tps":0.10000000000000001',
                1,
            )
        return line

    with mock.patch.object(wal, "_record_to_line", side_effect=lexical_writer):
        commit_receipt_support.log_receipted_commit(
            layout,
            "b4-result-variant",
            L.ENV_TAG,
            {"fitness_tps": 0.1},
            operation_identity=operation_identity,
            ts=ts,
        )


RECEIPT_MARKER = '"commit_verification_receipt"'

MUTATION_NODE_IDS = {
    "M01": "test_m01_assembly_rederives_precursor_from_the_sealed_registry",
    "M02": "test_m02_planned_path_lookup_and_publish_use_the_issuer_leaf",
    "M03": "test_m03_assignment_comes_from_attempt_wal_first_record_timestamps",
    "M04": "test_m04_final_assembly_rejects_different_on_off_pair_ids",
    "M05": "test_m05_campaign_lock_classification_and_receipt_share_one_byte_buffer",
    "M06": "test_m06_lowercase_wal_commit_maps_only_to_uppercase_raw_commit",
    "M07": "test_m07_non_binary_exact_decimal_lexeme_is_preserved",
    "M08": "test_m08_publication_rejects_reuse_of_campaign_iteration_arm_tuple",
    "M09": "test_m09_stable_nonterminal_wal_is_not_classified_as_executed",
    "M10": "test_m10_empty_red_section_is_rejected_instead_of_marking_both_arms_true",
    "M11": "test_m11_unproved_crash_and_stopped_before_dispositions_are_never_emitted",
    "M12": "test_m12_nonterminating_reference_ratio_has_only_named_rejection",
    "M13": "test_m13_integer_reference_is_the_only_integer_acceptance_control",
    "M14": "test_m14_busy_campaign_with_no_terminal_record_is_deferred_without_publish",
    "M15": "test_m15_lock_free_campaign_with_no_terminal_record_is_published",
    "M16": "test_m16_judgment_fields_are_unknown_request_fields",
    "M17": "test_m17_terminal_receipt_validation_survives_original_replacement",
    "M18": "test_m18_symlinked_evidence_is_rejected_with_regular_control",
}


@contextlib.contextmanager
def _evidence_scope(
    root: Path,
    *,
    iteration: int,
    assignment: tuple[str, str] = ("on", "off"),
    terminal: str = "commit",
    admission=None,
    red_detail: bool = True,
):
    admission = admission or _committed_admission_fixture()
    on_cfg, off_cfg = _marked_driver_configs()
    on_id = str(ident.campaign_id(on_cfg))
    off_id = str(ident.campaign_id(off_cfg))
    output_root = root / "output"
    on_layout = CampaignLayout(
        str(output_root / "exploration" / "campaigns" / on_id)
    )
    off_layout = CampaignLayout(
        str(output_root / "exploration" / "campaigns" / off_id)
    )
    if red_detail:
        _make_admitted_fixture(
            Path(on_layout.root),
            on_cfg,
            source_tag=f"producer-precursor-{iteration}",
            iteration=iteration,
        )
    else:
        _make_clean_admitted_fixture(
            Path(on_layout.root),
            on_cfg,
            source_tag=f"producer-clean-precursor-{iteration}",
            iteration=iteration,
        )
    _copy_precursor_with_writers(on_layout, off_layout, off_cfg)
    layouts = {on_id: on_layout, off_id: off_layout}

    def layout_for(campaign_id):
        return layouts[campaign_id]

    runner, _calls = _fake_runner_factory()
    home = root / "home"
    home.mkdir(parents=True)
    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(C, "REPOSITORY_ROOT", admission.repository))
        stack.enter_context(mock.patch.object(C, "ROLE_FILE", admission.role_file))
        stack.enter_context(mock.patch.object(C, "verify_b4_admission_record", _cached_verify_admission))
        stack.enter_context(mock.patch.object(P.launcher, "verify_b4_admission_record", _cached_verify_admission))
        stack.enter_context(mock.patch.object(C.shutil, "which", return_value=sys.executable))
        stack.enter_context(mock.patch.object(C, "exploration_campaign_layout", side_effect=layout_for))
        stack.enter_context(mock.patch.object(L, "exploration_campaign_layout", side_effect=layout_for))
        on_context = _production_launch_context(
            on_cfg,
            admission=admission,
            arm="on",
            layout=on_layout,
        )
        _production_launch_context(
            off_cfg,
            admission=admission,
            arm="off",
            layout=off_layout,
        )
        with C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=root / "critic-pair",
            admission_record_path=admission.record_path,
            expected_driver_kind="base",
            _b4_launch_context=on_context,
            repository_root=admission.repository,
            environ={"HOME": str(home)},
        ) as pair:
            pair.on._B4ClosedCriticController__provider._runner = runner
            pair.off._B4ClosedCriticController__provider._runner = runner
            on_invocation = pair.on.invoke(invocation_id=f"producer-on-{iteration}")
            off_invocation = pair.off.invoke(invocation_id=f"producer-off-{iteration}")
            for cfg, layout, receipt_path in (
                (on_cfg, on_layout, on_invocation.terminal_receipt_path),
                (off_cfg, off_layout, off_invocation.terminal_receipt_path),
            ):
                state = L.load_loop_state(layout)
                assert state is not None
                authorization = L.require_b4_iteration_authorization(
                    cfg,
                    layout,
                    state,
                    do_build=True,
                    terminal_receipt_path=receipt_path,
                )
                assert authorization is not None
                L.consume_b4_iteration_authorization(authorization)

            timestamps = {assignment[0]: float(iteration * 10 + 1), assignment[1]: float(iteration * 10 + 2)}
            if terminal == "commit":
                for arm, cfg, layout in (
                    ("on", on_cfg, on_layout),
                    ("off", off_cfg, off_layout),
                ):
                    _production_launch_context(
                        cfg,
                        admission=admission,
                        arm=arm,
                        layout=layout,
                        action=lambda _context, live_layout, arm=arm: _commit_with_decimal_lexeme(
                            live_layout,
                            ts=timestamps[arm],
                            operation_identity=f"producer-{iteration}-{arm}",
                        ),
                    )
                    state = L.load_loop_state(layout)
                    assert state is not None
                    state.iteration += 1
                    state.whiteboard.append(
                        L.WhiteboardEntry(
                            iteration=state.iteration,
                            direction="increase",
                            magnitude="small",
                            result="success",
                            delta_pct=None,
                        )
                    )
                    L.save_loop_state(layout, state)
            elif terminal == "abort":
                for arm, layout in (("on", on_layout), ("off", off_layout)):
                    wal.log(
                        layout,
                        f"rejected-{iteration}-{arm}",
                        STAGE_ABORT,
                        L.ENV_TAG,
                        {"reason": "diff-quarantine"},
                        ts=timestamps[arm],
                    )
                    state = L.load_loop_state(layout)
                    assert state is not None
                    state.iteration += 1
                    state.whiteboard.append(
                        L.WhiteboardEntry(
                            iteration=state.iteration,
                            direction="increase",
                            magnitude="small",
                            result="rejected",
                            delta_pct=None,
                        )
                    )
                    L.save_loop_state(layout, state)
            elif terminal == "absent":
                for arm, layout in (("on", on_layout), ("off", off_layout)):
                    wal.log(
                        layout,
                        f"unfinished-{iteration}-{arm}",
                        STAGE_BUILD_START,
                        L.ENV_TAG,
                        {"attempt": f"unfinished-{iteration}-{arm}"},
                        ts=timestamps[arm],
                    )
            else:
                raise AssertionError(terminal)
            yield _Evidence(
                admission=admission,
                on_cfg=on_cfg,
                off_cfg=off_cfg,
                on_layout=on_layout,
                off_layout=off_layout,
                on_receipt=on_invocation.terminal_receipt_path,
                off_receipt=off_invocation.terminal_receipt_path,
                iteration=iteration,
            )


def _request(evidence: _Evidence, attempt_id: str) -> dict[str, object]:
    return {
        "attempt_id": attempt_id,
        "on_campaign_root": evidence.on_layout.root,
        "off_campaign_root": evidence.off_layout.root,
        "on_terminal_receipt_path": str(evidence.on_receipt),
        "off_terminal_receipt_path": str(evidence.off_receipt),
    }


def _publish(
    publication: issuer.B4PrerunPublication,
    evidence: _Evidence,
    *,
    attempt_id: str | None = None,
):
    result = P.publish_b4_attempt_result(
        publication=publication,
        request=_request(
            evidence,
            attempt_id or publication.manifest.rows[0].attempt_id,
        ),
    )
    return result


def _assert_write(result) -> P.B4AttemptResultWrite:
    assert isinstance(result, P.B4AttemptResultWrite), result
    assert Path(result.artifact_path).read_bytes() == result.canonical_bytes
    return result


def _assert_rejection(result, code: P.B4RawRecordIssueCode) -> None:
    assert isinstance(result, P.B4RawRecordRejection), result
    assert tuple(issue.code for issue in result.issues) == (code,)


def test_mutation_node_mapping_is_complete_and_one_to_one() -> None:
    assert set(MUTATION_NODE_IDS) == {f"M{index:02d}" for index in range(1, 19)}
    assert len(set(MUTATION_NODE_IDS.values())) == 18
    assert all(callable(globals().get(name)) for name in MUTATION_NODE_IDS.values())


@pytest.fixture
def certified_evidence(tmp_path_factory):
    """Build one real pair per pytest run and serialize cross-worker consumers."""

    base = Path(tmp_path_factory.getbasetemp())
    shared_parent = base.parent if base.name.startswith("popen-") else base
    shared = shared_parent / "b4-producer-certified-shared"
    shared.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(shared / "fixture.lock", os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        metadata_path = shared / "evidence.json"
        if not metadata_path.exists():
            with _evidence_scope(
                shared / "evidence",
                iteration=1,
                assignment=("off", "on"),
                terminal="commit",
            ) as created:
                metadata = {
                    "admission_repository": str(created.admission.repository),
                    "admission_role_file": str(created.admission.role_file),
                    "admission_record_path": str(created.admission.record_path),
                    "on_root": created.on_layout.root,
                    "off_root": created.off_layout.root,
                    "on_receipt": str(created.on_receipt),
                    "off_receipt": str(created.off_receipt),
                    "iteration": created.iteration,
                }
            metadata_path.write_bytes(
                json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode("utf-8")
            )
        metadata = json.loads(metadata_path.read_bytes())
        on_cfg, off_cfg = _marked_driver_configs()
        evidence = _Evidence(
            admission=_SharedAdmission(
                repository=Path(metadata["admission_repository"]),
                role_file=Path(metadata["admission_role_file"]),
                record_path=Path(metadata["admission_record_path"]),
            ),
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            on_layout=CampaignLayout(metadata["on_root"]),
            off_layout=CampaignLayout(metadata["off_root"]),
            on_receipt=Path(metadata["on_receipt"]),
            off_receipt=Path(metadata["off_receipt"]),
            iteration=metadata["iteration"],
        )
        layouts = {
            str(ident.campaign_id(on_cfg)): evidence.on_layout,
            str(ident.campaign_id(off_cfg)): evidence.off_layout,
        }

        def layout_for(campaign_id):
            return layouts[campaign_id]

        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(C, "REPOSITORY_ROOT", evidence.admission.repository))
            stack.enter_context(mock.patch.object(C, "ROLE_FILE", evidence.admission.role_file))
            stack.enter_context(mock.patch.object(C, "verify_b4_admission_record", _cached_verify_admission))
            stack.enter_context(mock.patch.object(P.launcher, "verify_b4_admission_record", _cached_verify_admission))
            stack.enter_context(mock.patch.object(C.shutil, "which", return_value=sys.executable))
            stack.enter_context(mock.patch.object(C, "exploration_campaign_layout", side_effect=layout_for))
            stack.enter_context(mock.patch.object(L, "exploration_campaign_layout", side_effect=layout_for))
            yield evidence
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def test_m01_assembly_rederives_precursor_from_the_sealed_registry(
    tmp_path: Path,
    certified_evidence: _Evidence,
) -> None:
    """Acceptance would permit a caller-chosen precursor. Rejection leaves only the sealed registry lookup."""
    publication = _publication(tmp_path)
    write = _assert_write(_publish(publication, certified_evidence))
    value = P._strict_json(write.canonical_bytes, decimal_tokens=True)
    expected = publication.registry.scheduled_attempts[0].initial_proposal_sha256
    assert {source["binding"]["precursor_hash"] for source in value["arm_sources"]} == {expected}
    forged = hashlib.sha256(b"caller-selected-precursor").hexdigest()
    for source in value["arm_sources"]:
        source["binding"]["precursor_hash"] = forged
    Path(write.artifact_path).write_bytes(P._encode_json(value))
    result = P.assemble_b4_raw_analysis(publication=publication)
    assert isinstance(result, P.B4RawRecordRejection), result
    assert result.issues[0].field == "source_rederivation"


def test_m02_planned_path_lookup_and_publish_use_the_issuer_leaf(
    tmp_path: Path,
    certified_evidence: _Evidence,
) -> None:
    """Both the selector and the exclusive publisher name the sealed issuer leaf."""
    publication = _publication(tmp_path)
    row = publication.manifest.rows[0]
    planned = publication.planned_result_artifacts[0].artifact_path
    assert P._planned_path(publication, row.attempt_id) == planned
    write = _assert_write(_publish(publication, certified_evidence))
    assert write.artifact_path == planned


def test_m03_assignment_comes_from_attempt_wal_first_record_timestamps(
    tmp_path: Path,
    certified_evidence: _Evidence,
) -> None:
    """Acceptance would let publish order stand in for execution order. Rejection preserves the two production-WAL timestamp observations."""
    publication = _publication(tmp_path)
    write = _assert_write(_publish(publication, certified_evidence))
    value = json.loads(write.canonical_bytes)
    observations = {
        source["identity"]["arm"]: (
            source["evidence"]["wal"]["first_record_ts"],
            source["evidence"]["wal"]["first_record_position"],
        )
        for source in value["arm_sources"]
    }
    assert observations == {"on": (12.0, 3), "off": (11.0, 3)}
    assert value["assignment_observation"] == ["off", "on"]


def test_m04_final_assembly_rejects_different_on_off_pair_ids(
    tmp_path: Path,
    certified_evidence: _Evidence,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acceptance would combine arms that declare different receipt pairs. Rejection is performed again at final assembly after a valid control publish."""
    publication = _publication(tmp_path)
    write = _assert_write(_publish(publication, certified_evidence))
    value = P._strict_json(write.canonical_bytes, decimal_tokens=True)
    value["arm_sources"][1]["identity"]["pair_id"] += "-different"
    tampered = P._encode_json(value)
    Path(write.artifact_path).write_bytes(tampered)
    monkeypatch.setattr(
        P,
        "_derive_b4_attempt_data",
        lambda *_args, **_kwargs: (write.artifact_path, tampered),
    )
    _assert_rejection(
        P.assemble_b4_raw_analysis(publication=publication),
        P.B4RawRecordIssueCode.EVIDENCE_BINDING,
    )


def test_m05_campaign_lock_classification_and_receipt_share_one_byte_buffer(
    tmp_path: Path,
    certified_evidence: _Evidence,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Classification and COMMIT validation consume the identical snapshot object."""
    publication = _publication(tmp_path)
    real_decode = P._decode_campaign_identity
    real_receipt_hash = P.campaign_lock_bytes_sha256
    classified_buffers: list[bytes] = []
    receipt_buffers: list[bytes] = []

    def observed_decode(snapshot, **kwargs):
        classified_buffers.append(snapshot.data)
        return real_decode(snapshot, **kwargs)

    def observed_receipt_hash(data):
        receipt_buffers.append(data)
        return real_receipt_hash(data)

    monkeypatch.setattr(P, "_decode_campaign_identity", observed_decode)
    monkeypatch.setattr(P, "campaign_lock_bytes_sha256", observed_receipt_hash)
    _assert_write(_publish(publication, certified_evidence))
    assert len(classified_buffers) == len(receipt_buffers) == 2
    assert all(
        classified is receipted
        for classified, receipted in zip(classified_buffers, receipt_buffers)
    )
    assert classified_buffers[0] is not classified_buffers[1]


def test_m06_lowercase_wal_commit_maps_only_to_uppercase_raw_commit(
    tmp_path: Path,
    certified_evidence: _Evidence,
) -> None:
    """Acceptance would leak the WAL vocabulary into the closed raw enum. Rejection retains the exact commit-to-COMMIT mapping."""
    publication = _publication(tmp_path)
    value = json.loads(_assert_write(_publish(publication, certified_evidence)).canonical_bytes)
    assert {source["raw"]["terminal_stage"] for source in value["arm_sources"]} == {"COMMIT"}


def test_m07_non_binary_exact_decimal_lexeme_is_preserved(
    tmp_path: Path,
    certified_evidence: _Evidence,
) -> None:
    """Acceptance would silently reformat 0.10000000000000001 through float. Rejection preserves the exact production-WAL token."""
    publication = _publication(tmp_path)
    write = _assert_write(_publish(publication, certified_evidence))
    assert write.canonical_bytes.count(b'"throughput":0.10000000000000001') == 2


def test_m08_publication_rejects_reuse_of_campaign_iteration_arm_tuple(
    tmp_path: Path,
    certified_evidence: _Evidence,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Acceptance would copy one real arm trial into a second block. Rejection leaves the first planned artifact unchanged and refuses the duplicate tuple."""
    publication = _publication(tmp_path)
    first, second = publication.manifest.rows[:2]
    _assert_write(_publish(publication, certified_evidence, attempt_id=first.attempt_id))
    monkeypatch.setattr(P, "_existing_identity_triples", lambda *_args, **_kwargs: set())
    _assert_write(_publish(publication, certified_evidence, attempt_id=second.attempt_id))
    _assert_rejection(
        P.assemble_b4_raw_analysis(publication=publication),
        P.B4RawRecordIssueCode.PUBLICATION_CONFLICT,
    )


def test_m09_stable_nonterminal_wal_is_not_classified_as_executed(tmp_path: Path) -> None:
    """Acceptance would treat a stable read as terminal execution. Rejection maps lock-free absence to terminal-record-absent."""
    with _evidence_scope(tmp_path / "evidence", iteration=9, terminal="absent") as evidence:
        publication = _publication(tmp_path / "publication-case")
        value = json.loads(_assert_write(_publish(publication, evidence)).canonical_bytes)
    assert {source["raw"]["execution_disposition"] for source in value["arm_sources"]} == {"terminal-record-absent"}


def test_m10_certified_off_digest_absence_sets_treatment_fired_true(
    tmp_path: Path,
    certified_evidence: _Evidence,
) -> None:
    """Acceptance would make every off arm a treatment shortage. Rejection recognizes the certified absence of the red section as firing."""
    publication = _publication(tmp_path)
    value = json.loads(_assert_write(_publish(publication, certified_evidence)).canonical_bytes)
    assert [source["raw"]["treatment_fired"] for source in value["arm_sources"]] == [True, True]
    assert [source["raw"]["contaminated"] for source in value["arm_sources"]] == [False, False]


def test_m10_empty_red_section_is_rejected_instead_of_marking_both_arms_true(
    tmp_path: Path,
) -> None:
    """A constant-true treatment mutant would accept this empty red block; the eligibility gate rejects it."""
    with _evidence_scope(
        tmp_path / "evidence",
        iteration=10,
        terminal="commit",
        red_detail=False,
    ) as evidence:
        publication = _publication(tmp_path / "publication-case")
        result = _publish(publication, evidence)
    _assert_rejection(result, P.B4RawRecordIssueCode.EVIDENCE_BINDING)
    assert result.issues[0].field == "projected_digest.red_details"
    assert not Path(publication.planned_result_artifacts[0].artifact_path).exists()


def test_m11_unproved_crash_and_stopped_before_dispositions_are_never_emitted(
    tmp_path: Path,
) -> None:
    """Acceptance would invent a crash or entry-stop distinction. Rejection emits only the lock-supported terminal-record-absent value."""
    with _evidence_scope(tmp_path / "evidence", iteration=11, terminal="absent") as evidence:
        publication = _publication(tmp_path / "publication-case")
        raw = json.loads(_assert_write(_publish(publication, evidence)).canonical_bytes)
    dispositions = {source["raw"]["execution_disposition"] for source in raw["arm_sources"]}
    assert dispositions == {"terminal-record-absent"}
    assert dispositions.isdisjoint({"crash", "stopped-before"})


def test_abort_reason_is_projected_as_terminal_reason(tmp_path: Path) -> None:
    with _evidence_scope(tmp_path / "evidence", iteration=12, terminal="abort") as evidence:
        publication = _publication(tmp_path / "publication-case")
        raw = json.loads(_assert_write(_publish(publication, evidence)).canonical_bytes)
    assert {source["raw"]["terminal_stage"] for source in raw["arm_sources"]} == {"ABORT"}
    assert {source["raw"]["terminal_reason"] for source in raw["arm_sources"]} == {"diff-quarantine"}


def test_m12_nonterminating_reference_ratio_has_only_named_rejection(
    tmp_path: Path,
    certified_evidence: _Evidence,
) -> None:
    """Acceptance would round the one-third reference into raw JSON. Rejection names only the unavailable finite decimal representation."""
    control = _publication(tmp_path / "control")
    _assert_write(_publish(control, certified_evidence))
    publication = _publication(tmp_path, reference_override=(1, 3))
    _assert_rejection(
        _publish(publication, certified_evidence),
        P.B4RawRecordIssueCode.DECIMAL_NOT_TERMINATING,
    )


def test_m13_integer_reference_is_the_only_integer_acceptance_control(
    tmp_path: Path,
    certified_evidence: _Evidence,
) -> None:
    publication = _publication(tmp_path, reference_override=(10_000, 1))
    write = _assert_write(_publish(publication, certified_evidence))
    assert b'"reference_tps":10000' in write.canonical_bytes


def test_m14_busy_campaign_with_no_terminal_record_is_deferred_without_publish(
    tmp_path: Path,
) -> None:
    """Acceptance would seal a live attempt as missing. Rejection returns a deferred result and leaves the issuer-planned target absent."""
    from orchestrator.campaign.lock import campaign_lock

    with _evidence_scope(tmp_path / "evidence", iteration=14, terminal="absent") as evidence:
        control = _publication(tmp_path / "control")
        _assert_write(_publish(control, evidence))
        publication = _publication(tmp_path / "publication-case")
        lock_path = P._execution_lock_for_root(evidence.on_layout.root)
        with campaign_lock(lock_path, blocking=False):
            result = _publish(publication, evidence)
        assert isinstance(result, P.B4RawRecordDeferred), result
        target = publication.planned_result_artifacts[0].artifact_path
        assert not Path(target).exists()


def test_m15_lock_free_campaign_with_no_terminal_record_is_published(
    tmp_path: Path,
) -> None:
    """Acceptance would omit a finished attempt that left no terminal record. Rejection publishes terminal-record-absent after acquiring both campaign locks."""
    with _evidence_scope(tmp_path / "evidence", iteration=15, terminal="absent") as evidence:
        publication = _publication(tmp_path / "publication-case")
        write = _assert_write(_publish(publication, evidence))
        first = json.loads(write.canonical_bytes)
        second = _assert_write(_publish(publication, evidence))
    assert second.idempotent
    assert all(
        source["evidence"]["execution_lock"]["acquired"] is True
        and source["raw"]["execution_disposition"] == "terminal-record-absent"
        for source in first["arm_sources"]
    )


def test_m16_judgment_fields_are_unknown_request_fields(
    tmp_path: Path,
    certified_evidence: _Evidence,
) -> None:
    """Acceptance would turn the producer into a serializer of caller judgments. Rejection keeps every listed analysis field outside the input schema."""
    control = _publication(tmp_path / "control")
    _assert_write(_publish(control, certified_evidence))
    for field in sorted(P._JUDGMENT_FIELDS):
        publication = _publication(tmp_path / field)
        request = _request(certified_evidence, publication.manifest.rows[0].attempt_id)
        request[field] = False
        _assert_rejection(
            P.publish_b4_attempt_result(publication=publication, request=request),
            P.B4RawRecordIssueCode.UNKNOWN_FIELD,
        )


def test_m17_terminal_receipt_validation_survives_original_replacement(
    tmp_path: Path,
    certified_evidence: _Evidence,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every later validator consumes the first terminal-receipt snapshot bytes."""
    publication = _publication(tmp_path)
    real = P._snapshot_regular
    receipt_path = str(certified_evidence.on_receipt)
    original = certified_evidence.on_receipt.read_bytes()
    replaced = False

    def replace_after_snapshot(path, **kwargs):
        nonlocal replaced
        snapshot = real(path, **kwargs)
        if os.fspath(path) == receipt_path and not replaced:
            certified_evidence.on_receipt.write_bytes(b"not-the-snapshotted-receipt")
            replaced = True
        return snapshot

    monkeypatch.setattr(P, "_snapshot_regular", replace_after_snapshot)
    try:
        _assert_write(_publish(publication, certified_evidence))
    finally:
        certified_evidence.on_receipt.write_bytes(original)
    assert replaced


def test_m18_symlinked_evidence_is_rejected_with_regular_control(
    tmp_path: Path,
    certified_evidence: _Evidence,
) -> None:
    """Acceptance would follow a replaceable receipt leaf. Rejection preserves the regular-file control and rejects the symlinked locator."""
    control = _publication(tmp_path / "control")
    _assert_write(_publish(control, certified_evidence))
    link = tmp_path / "terminal-link.json"
    link.symlink_to(certified_evidence.on_receipt)
    publication = _publication(tmp_path / "attack")
    request = _request(certified_evidence, publication.manifest.rows[0].attempt_id)
    request["on_terminal_receipt_path"] = str(link)
    _assert_rejection(
        P.publish_b4_attempt_result(publication=publication, request=request),
        P.B4RawRecordIssueCode.EVIDENCE_SYMLINK,
    )

    role_file = Path(certified_evidence.admission.role_file)
    held_role = role_file.with_name("critic-held.md")
    role_file.rename(held_role)
    role_file.symlink_to(held_role)
    try:
        role_publication = _publication(tmp_path / "role-attack")
        _assert_rejection(
            _publish(role_publication, certified_evidence),
            P.B4RawRecordIssueCode.EVIDENCE_SYMLINK,
        )
    finally:
        role_file.unlink()
        held_role.rename(role_file)


def test_assembly_rederives_judgments_and_requires_non_guarantees(
    tmp_path: Path,
    certified_evidence: _Evidence,
) -> None:
    publication = _publication(tmp_path / "raw-forgery")
    write = _assert_write(_publish(publication, certified_evidence))
    value = P._strict_json(write.canonical_bytes, decimal_tokens=True)
    value["arm_sources"][0]["raw"]["protocol_ok"] = False
    Path(write.artifact_path).write_bytes(P._encode_json(value))
    forged = P.assemble_b4_raw_analysis(publication=publication)
    assert isinstance(forged, P.B4RawRecordRejection), forged
    assert forged.issues[0].field == "source_rederivation"

    publication = _publication(tmp_path / "pointer-free-forgery")
    write = _assert_write(_publish(publication, certified_evidence))
    value = P._strict_json(write.canonical_bytes, decimal_tokens=True)
    for source in value["arm_sources"]:
        del source["evidence"]
        source["raw"]["treatment_fired"] = True
        source["raw"]["protocol_ok"] = True
    Path(write.artifact_path).write_bytes(P._encode_json(value))
    pointer_free = P.assemble_b4_raw_analysis(publication=publication)
    assert isinstance(pointer_free, P.B4RawRecordRejection), pointer_free
    assert pointer_free.issues[0].field.endswith(".evidence")

    publication = _publication(tmp_path / "non-guarantee-forgery")
    write = _assert_write(_publish(publication, certified_evidence))
    value = P._strict_json(write.canonical_bytes, decimal_tokens=True)
    del value["arm_sources"][0]["non_guarantees"]
    Path(write.artifact_path).write_bytes(P._encode_json(value))
    missing_tuple = P.assemble_b4_raw_analysis(publication=publication)
    assert isinstance(missing_tuple, P.B4RawRecordRejection), missing_tuple
    assert missing_tuple.issues[0].field == "source_rederivation"


def test_terminal_checkpoint_window_is_deferred_until_state_catches_up(
    tmp_path: Path,
) -> None:
    with _evidence_scope(tmp_path / "evidence", iteration=31, terminal="commit") as evidence:
        publication = _publication(tmp_path / "publication-case")
        saved_states = {}
        for layout in (evidence.on_layout, evidence.off_layout):
            state = L.load_loop_state(layout)
            assert state is not None
            saved_states[layout.root] = copy.deepcopy(state)
            state.iteration -= 1
            state.whiteboard.pop()
            L.save_loop_state(layout, state)
        deferred = _publish(publication, evidence)
        assert isinstance(deferred, P.B4RawRecordDeferred), deferred
        assert set(deferred.checkpoint_campaign_roots) == {
            evidence.on_layout.root,
            evidence.off_layout.root,
        }
        assert not Path(publication.planned_result_artifacts[0].artifact_path).exists()
        for layout in (evidence.on_layout, evidence.off_layout):
            L.save_loop_state(layout, saved_states[layout.root])
        _assert_write(_publish(publication, evidence))


def test_terminal_absence_rereads_wal_after_lock_and_defers_on_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with _evidence_scope(tmp_path / "evidence", iteration=32, terminal="absent") as evidence:
        publication = _publication(tmp_path / "publication-case")
        real_lock = P.campaign_lock
        changed = False

        @contextlib.contextmanager
        def changing_lock(path, *, blocking):
            nonlocal changed
            with real_lock(path, blocking=blocking):
                if not changed:
                    changed = True
                    wal.log(
                        evidence.on_layout,
                        "post-lock-record",
                        STAGE_BUILD_START,
                        L.ENV_TAG,
                        {"attempt": "post-lock-record"},
                        ts=9999.0,
                    )
                yield

        monkeypatch.setattr(P, "campaign_lock", changing_lock)
        deferred = _publish(publication, evidence)
    assert isinstance(deferred, P.B4RawRecordDeferred), deferred
    assert deferred.wal_changed_campaign_roots == (evidence.on_layout.root,)
    assert not Path(publication.planned_result_artifacts[0].artifact_path).exists()


def test_terminal_trial_with_missing_auxiliary_evidence_is_still_reported(
    tmp_path: Path,
) -> None:
    with _evidence_scope(tmp_path / "evidence", iteration=33, terminal="commit") as evidence:
        launch_path = Path(evidence.on_layout.root) / P.launcher.B4_LAUNCH_SIDECAR
        held = launch_path.with_suffix(".held")
        launch_path.rename(held)
        publication = _publication(tmp_path / "publication-case")
        write = _assert_write(_publish(publication, evidence))
        value = json.loads(write.canonical_bytes)
        on_source = next(
            source for source in value["arm_sources"]
            if source["identity"]["arm"] == "on"
        )
        assert on_source["raw"]["protocol_ok"] is False
        assert [issue["field"] for issue in on_source["evidence_issues"]] == [
            P.launcher.B4_LAUNCH_SIDECAR
        ]
        assembled = P.assemble_b4_raw_analysis(publication=publication)
    assert isinstance(assembled, P.B4RawRecordRejection), assembled
    assert assembled.issues[0].code is P.B4RawRecordIssueCode.INCOMPLETE_SET
    assert assembled.issues[0].field == publication.manifest.rows[1].attempt_id


def test_manifest_driver_must_match_campaign_and_receipt_driver_kind(
    tmp_path: Path,
    certified_evidence: _Evidence,
) -> None:
    publication = _publication(tmp_path, driver_override="sort")
    result = _publish(publication, certified_evidence)
    _assert_rejection(result, P.B4RawRecordIssueCode.EVIDENCE_BINDING)
    assert result.issues[0].field == "driver"


def test_non_guarantees_name_the_residual_lock_and_closure_limits(
    tmp_path: Path,
    certified_evidence: _Evidence,
) -> None:
    publication = _publication(tmp_path)
    value = json.loads(_assert_write(_publish(publication, certified_evidence)).canonical_bytes)
    expected = set(P.B4_RAW_RECORD_NON_GUARANTEES)
    assert all(set(source["non_guarantees"]) == expected for source in value["arm_sources"])
    assert any("実行の内側区間しか覆わず" in item for item in expected)
    assert any("source hash が producer 意味論を識別しない" in item for item in expected)


def _publish_full_publication(
    root: Path,
    *,
    terminal: str,
) -> tuple[issuer.B4PrerunPublication, P.B4RawAnalysisAssembly]:
    publication = _publication(root / "pre")
    admission = _committed_admission_fixture()
    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(C, "REPOSITORY_ROOT", admission.repository))
        stack.enter_context(mock.patch.object(C, "ROLE_FILE", admission.role_file))
        requests = []
        for ordinal, row in enumerate(publication.manifest.rows, start=1):
            schedule = tuple(arm.value for arm in row.assignment_schedule)
            with _evidence_scope(
                root / f"block-{ordinal:03d}",
                iteration=ordinal,
                assignment=schedule,
                terminal=terminal,
                admission=admission,
            ) as evidence:
                requests.append(_request(evidence, row.attempt_id))
        writes = P.publish_b4_attempt_results(
            publication=publication,
            requests=requests,
        )
        assert len(writes) == EXPECTED_BLOCK_COUNT
        assert all(isinstance(write, P.B4AttemptResultWrite) for write in writes), writes
        for write in writes:
            _assert_write(write)
        assembled = P.assemble_b4_raw_analysis(publication=publication)
    assert isinstance(assembled, P.B4RawAnalysisAssembly), assembled
    return publication, assembled


def test_positive_201_block_all_terminal_records_absent(tmp_path: Path) -> None:
    publication, assembled = _publish_full_publication(tmp_path, terminal="absent")
    assert len(assembled.source_artifact_bytes) == 2 * EXPECTED_BLOCK_COUNT
    assert len({hashlib.sha256(item).hexdigest() for item in assembled.source_artifact_bytes}) == 2 * EXPECTED_BLOCK_COUNT
    parsed = parse_raw_analysis_records(assembled.canonical_bytes)
    assert not hasattr(parsed, "reasons")
    assert len(parsed.blocks) == EXPECTED_BLOCK_COUNT
    assert all(
        arm.execution_disposition.value == "terminal-record-absent"
        for block in parsed.blocks
        for arm in block.arms
    )
    binding = build_contract_binding(
        registry=publication.registry,
        manifest=publication.manifest,
        schedule_receipt=publication.schedule_receipt,
        seed_receipt=publication.seed_receipt,
    )
    result = evaluate_b4_artifacts(
        floor=0,
        contract_binding=binding,
        scheduled_registry_bytes=publication.registry.canonical_bytes,
        analysis_manifest_bytes=publication.manifest.canonical_bytes,
        raw_analysis_records_bytes=assembled.canonical_bytes,
        source_artifact_bytes=assembled.source_artifact_bytes,
    )
    assert result.analysis_invalid is None


def test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings(
    tmp_path: Path,
) -> None:
    publication, assembled = _publish_full_publication(tmp_path, terminal="commit")
    assert len(assembled.source_artifact_bytes) == 2 * EXPECTED_BLOCK_COUNT
    assert len({hashlib.sha256(item).hexdigest() for item in assembled.source_artifact_bytes}) == 2 * EXPECTED_BLOCK_COUNT
    assert assembled.canonical_bytes.count(b'"throughput":0.10000000000000001') == 2 * EXPECTED_BLOCK_COUNT
    parsed = parse_raw_analysis_records(assembled.canonical_bytes)
    assert not hasattr(parsed, "reasons")
    assert all(
        arm.execution_disposition.value == "executed"
        and arm.treatment_fired
        and not arm.contaminated
        and arm.protocol_ok
        for block in parsed.blocks
        for arm in block.arms
    )
    assert all(
        block.assignment_observation == row.assignment_schedule
        for block, row in zip(parsed.blocks, publication.manifest.rows)
    )
    binding = build_contract_binding(
        registry=publication.registry,
        manifest=publication.manifest,
        schedule_receipt=publication.schedule_receipt,
        seed_receipt=publication.seed_receipt,
    )
    result = evaluate_b4_artifacts(
        floor=0,
        contract_binding=binding,
        scheduled_registry_bytes=publication.registry.canonical_bytes,
        analysis_manifest_bytes=publication.manifest.canonical_bytes,
        raw_analysis_records_bytes=assembled.canonical_bytes,
        source_artifact_bytes=assembled.source_artifact_bytes,
    )
    assert result.analysis_invalid is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
