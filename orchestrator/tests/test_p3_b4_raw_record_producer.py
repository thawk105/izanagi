from __future__ import annotations

import ast
import contextlib
import copy
from dataclasses import dataclass, replace
import errno
import fcntl
import functools
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
from types import SimpleNamespace
from unittest import mock

import pytest

from orchestrator.campaign import (
    campaign_lock,
    contract_loader_binding,
    env_contract,
    ident,
)
from orchestrator.campaign import p3_b4_closed_critic as C
from orchestrator.campaign import p3_b4_material_report as material_report
from orchestrator.campaign import p3_b4_prerun_issuer as issuer
from orchestrator.campaign import p3_b4_raw_record_producer as P
from orchestrator.campaign import p3_s4_loop as L
from orchestrator.campaign import site_policy
from orchestrator.campaign import wal
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.campaign.model import (
    Genome,
    STAGE_ABORT,
    STAGE_BUILD_START,
    STAGE_COMMIT,
)
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
from p3_b4_proposal_binding_support import preregistered_publication_root
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
    on_commit_receipt: object | None = None
    off_commit_receipt: object | None = None


@dataclass(frozen=True)
class _SharedAdmission:
    repository: Path
    role_file: Path
    record_path: Path


@dataclass(frozen=True)
class _WriterAuthority:
    binding: object
    activation_state: object


@dataclass(frozen=True)
class _PublicationEvidence:
    publication: issuer.B4PrerunPublication
    evidence: tuple[_Evidence, ...]


_CLEAN_GENOME = Genome("silo", {
    "NO_WAIT_LOCKING_IN_VALIDATION": 1,
    "NO_WAIT_OF_TICTOC": 0,
    "WAL": 0,
    "BACK_OFF": 1,
    "BACKOFF_FIXED": 20,
})

@functools.lru_cache(maxsize=None)
def _writer_authority() -> _WriterAuthority:
    binding = contract_loader_binding.capture_contract_loader_binding()
    contract_loader_binding.verify_live_contract_loader_binding(binding)
    return _WriterAuthority(
        binding=binding,
        activation_state=env_contract.verified_current_activation_state(),
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
    with preregistered_publication_root(root) as publication_root:
        return issuer.issue_b4_prerun_publication(
            scheduled_inputs=attempt_tuple,
            planned_result_artifacts=_planned(attempt_tuple, root / "results"),
            publication_root=str(publication_root),
        )


def _copy_precursor_with_writers(
    source: CampaignLayout,
    target: CampaignLayout,
    target_cfg,
) -> None:
    target.ensure()
    for record in wal.read_records(source):
        wal.append(target, record)
    _write_campaign_lock_with_writer(target, target_cfg)
    source_state = L.load_loop_state(source)
    assert source_state is not None
    L.save_loop_state(target, source_state)


def _write_campaign_lock_with_writer(target: CampaignLayout, target_cfg) -> None:
    authority = _writer_authority()
    binding = authority.binding
    activation_state = authority.activation_state
    if target_cfg.bound_environment_contract is None:
        target_cfg = ident.bind_environment_contract(
            target_cfg, env_contract.lookup(L.ENV_TAG),
        )
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
    wal.write_lock(layout, build_v2_lock(ident.canonical_preimage(cfg)))
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
    commit_receipt=None,
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
        if commit_receipt is None:
            commit_receipt_support.log_receipted_commit(
                layout,
                "b4-result-variant",
                L.ENV_TAG,
                {"fitness_tps": 0.1},
                operation_identity=operation_identity,
                ts=ts,
            )
        else:
            wal.log(
                layout,
                "b4-result-variant",
                STAGE_COMMIT,
                L.ENV_TAG,
                {"fitness_tps": 0.1},
                commit_receipt=commit_receipt,
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
    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(
            site_policy,
            "socket",
            SimpleNamespace(gethostname=lambda: "test-host"),
        ))
        stack.enter_context(mock.patch.object(
            site_policy,
            "_has_nqsv",
            return_value=False,
        ))
        with _evidence_scope_at_declared_site(
            root,
            iteration=iteration,
            assignment=assignment,
            terminal=terminal,
            admission=admission,
            red_detail=red_detail,
        ) as evidence:
            yield evidence


@contextlib.contextmanager
def _evidence_scope_at_declared_site(
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
            commit_receipts: dict[str, object] = {}
            if terminal == "commit":
                for arm, cfg, layout in (
                    ("on", on_cfg, on_layout),
                    ("off", off_cfg, off_layout),
                ):
                    operation_identity = f"producer-{iteration}-{arm}"
                    commit_receipt = commit_receipt_support.campaign_receipt(
                        layout,
                        "b4-result-variant",
                        {"fitness_tps": 0.1},
                        operation_identity=operation_identity,
                    )
                    commit_receipts[arm] = commit_receipt
                    _production_launch_context(
                        cfg,
                        admission=admission,
                        arm=arm,
                        layout=layout,
                        action=(
                            lambda _context, live_layout, arm=arm,
                            operation_identity=operation_identity,
                            commit_receipt=commit_receipt:
                            _commit_with_decimal_lexeme(
                                live_layout,
                                ts=timestamps[arm],
                                operation_identity=operation_identity,
                                commit_receipt=commit_receipt,
                            )
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
                on_commit_receipt=commit_receipts.get("on"),
                off_commit_receipt=commit_receipts.get("off"),
            )


def _rewrite_receipt_state_with_writer(
    source_bytes: bytes,
    target: CampaignLayout,
    *,
    iteration: int,
) -> tuple[L.LoopState, bytes]:
    state = L.state_from_dict(json.loads(source_bytes))
    offset = iteration - state.iteration
    state.iteration = iteration
    state.whiteboard = [
        replace(entry, iteration=entry.iteration + offset)
        for entry in state.whiteboard
    ]
    L.save_loop_state(target, state)
    written = Path(L.loop_state_path(target)).read_bytes()
    return state, written


def _replay_admitted_wal_with_writer(
    admitted_bytes: bytes,
    target: CampaignLayout,
) -> None:
    assert admitted_bytes.endswith(b"\n")
    for frame in admitted_bytes.splitlines():
        wal.append(target, wal.parse_line(frame.decode("utf-8")))
    assert Path(target.wal_file).read_bytes() == admitted_bytes


def _source_attempt_record_for_replay(
    *,
    source_layout: CampaignLayout,
    source_receipt_path: Path,
):
    invocation_id = json.loads(source_receipt_path.read_bytes())["invocation_id"]
    admitted_path = source_receipt_path.parent / (
        f"admitted_view_{invocation_id}.wal"
    )
    admitted_bytes = admitted_path.read_bytes()
    source_wal = Path(source_layout.wal_file).read_bytes()
    assert source_wal.startswith(admitted_bytes)
    suffix = source_wal[len(admitted_bytes):]
    assert suffix.endswith(b"\n")
    frames = suffix.splitlines()
    assert len(frames) == 1
    return wal.parse_line(frames[0].decode("utf-8"))


def _append_replayed_attempt_with_writer(
    *,
    source_layout: CampaignLayout,
    source_receipt_path: Path,
    target_layout: CampaignLayout,
    ts: float,
    live_commit_receipt,
) -> None:
    source_record = _source_attempt_record_for_replay(
        source_layout=source_layout,
        source_receipt_path=source_receipt_path,
    )
    if source_record.stage == STAGE_COMMIT:
        assert live_commit_receipt is not None
        stored_receipt = source_record.payload["commit_verification_receipt"]
        _commit_with_decimal_lexeme(
            target_layout,
            ts=ts,
            operation_identity=stored_receipt["operation_identity"],
            commit_receipt=live_commit_receipt,
        )
    else:
        assert live_commit_receipt is None
        wal.append(target_layout, replace(source_record, ts=ts))
    target_record = wal.read_records(target_layout)[-1]
    assert target_record.ts == ts
    assert target_record.stage == source_record.stage
    assert target_record.variant == source_record.variant
    assert target_record.env_tag == source_record.env_tag
    assert target_record.payload == source_record.payload


def _write_replicated_receipt_bundle(
    *,
    source_terminal_path: Path,
    target_pair_root: Path,
    admitted_bytes: bytes,
    receipt_state_bytes: bytes,
    pair_id: str,
    iteration: int,
) -> tuple[Path, C.B4ClosedCriticReceipt, str]:
    source_terminal = json.loads(source_terminal_path.read_bytes())
    arm = source_terminal["arm"]
    invocation_id = source_terminal["invocation_id"]
    source_root = source_terminal_path.parent
    target_root = target_pair_root / arm
    target_root.mkdir(parents=True, exist_ok=False)

    source_start_path = source_root / f"receipt_{invocation_id}_start.json"
    start = json.loads(source_start_path.read_bytes())
    start["pair_id"] = pair_id
    start_path = target_root / source_start_path.name
    start_sha256 = C._write_exclusive_json(start_path, start)

    for stem, suffix in (
        ("payload", ".json"),
        ("argv", ".json"),
        ("effective_prompt", ".txt"),
        ("neutral_root_identity", ".json"),
        ("envelope", ".json"),
    ):
        name = f"{stem}_{invocation_id}{suffix}"
        C._write_exclusive_bytes(
            target_root / name,
            (source_root / name).read_bytes(),
        )
    C._write_exclusive_bytes(
        target_root / f"admitted_view_{invocation_id}.wal",
        admitted_bytes,
    )
    C._write_exclusive_bytes(
        target_root / f"loop_state_{invocation_id}.json",
        receipt_state_bytes,
    )

    terminal = dict(source_terminal)
    terminal["pair_id"] = pair_id
    terminal["iteration"] = iteration
    terminal["loop_state_sha256"] = hashlib.sha256(
        receipt_state_bytes
    ).hexdigest()
    terminal["start_receipt_sha256"] = start_sha256
    target_terminal = target_root / source_terminal_path.name
    terminal_sha256 = C._write_exclusive_json(target_terminal, terminal)

    converted = dict(terminal)
    converted.pop("finished_at_ns")
    for field_name in C._RECEIPT_TUPLE_FIELDS:
        converted[field_name] = tuple(converted[field_name])
    receipt = C.B4ClosedCriticReceipt(**converted)
    return target_terminal, receipt, terminal_sha256


def _clone_arm_evidence_with_writers(
    *,
    source: _Evidence,
    arm: str,
    cfg,
    source_layout: CampaignLayout,
    source_receipt_path: Path,
    target_layout: CampaignLayout,
    target_pair_root: Path,
    pair_id: str,
    iteration: int,
    ts: float,
    terminal: str,
    live_commit_receipt,
    replay_non_commit_sidecar: bool,
) -> Path:
    source_terminal = json.loads(source_receipt_path.read_bytes())
    invocation_id = source_terminal["invocation_id"]
    admitted_bytes = (
        source_receipt_path.parent / f"admitted_view_{invocation_id}.wal"
    ).read_bytes()
    source_state_bytes = (
        source_receipt_path.parent / f"loop_state_{invocation_id}.json"
    ).read_bytes()

    target_layout.ensure()
    _replay_admitted_wal_with_writer(admitted_bytes, target_layout)
    _write_campaign_lock_with_writer(target_layout, cfg)
    receipt_state, receipt_state_bytes = _rewrite_receipt_state_with_writer(
        source_state_bytes,
        target_layout,
        iteration=iteration,
    )
    if replay_non_commit_sidecar:
        source_record = _source_attempt_record_for_replay(
            source_layout=source_layout,
            source_receipt_path=source_receipt_path,
        )
        if live_commit_receipt is not None:
            raise AssertionError(
                "sidecar replay requires live_commit_receipt is None"
            )
        if source_record.stage == STAGE_COMMIT:
            raise AssertionError("sidecar replay requires a non-COMMIT source")
        C._write_exclusive_bytes(
            Path(target_layout.root) / P.launcher.B4_LAUNCH_SIDECAR,
            (
                Path(source_layout.root) / P.launcher.B4_LAUNCH_SIDECAR
            ).read_bytes(),
        )
        _append_replayed_attempt_with_writer(
            source_layout=source_layout,
            source_receipt_path=source_receipt_path,
            target_layout=target_layout,
            ts=ts,
            live_commit_receipt=live_commit_receipt,
        )
    else:
        _production_launch_context(
            cfg,
            admission=source.admission,
            arm=arm,
            layout=target_layout,
            action=lambda _context, live_layout: _append_replayed_attempt_with_writer(
                source_layout=source_layout,
                source_receipt_path=source_receipt_path,
                target_layout=live_layout,
                ts=ts,
                live_commit_receipt=live_commit_receipt,
            ),
        )
    if terminal == "commit":
        current_state = copy.deepcopy(receipt_state)
        current_state.iteration += 1
        current_state.whiteboard.append(L.WhiteboardEntry(
            iteration=current_state.iteration,
            direction="increase",
            magnitude="small",
            result="success",
            delta_pct=None,
        ))
        L.save_loop_state(target_layout, current_state)
    else:
        assert terminal == "absent"
        L.save_loop_state(target_layout, receipt_state)

    target_terminal, receipt, terminal_sha256 = (
        _write_replicated_receipt_bundle(
            source_terminal_path=source_receipt_path,
            target_pair_root=target_pair_root,
            admitted_bytes=admitted_bytes,
            receipt_state_bytes=receipt_state_bytes,
            pair_id=pair_id,
            iteration=iteration,
        )
    )
    with mock.patch.object(
        L,
        "exploration_campaign_layout",
        return_value=target_layout,
    ):
        L.consume_b4_iteration_authorization(L.B4IterationAuthorization(
            receipt=receipt,
            terminal_receipt_sha256=terminal_sha256,
        ))
    return target_terminal


def _clone_evidence_with_writers(
    source: _Evidence,
    target_root: Path,
    *,
    iteration: int,
    assignment: tuple[str, str],
    terminal: str,
    replay_non_commit_sidecar: bool = False,
) -> _Evidence:
    on_id = str(ident.campaign_id(source.on_cfg))
    off_id = str(ident.campaign_id(source.off_cfg))
    output_root = target_root / "output" / "exploration" / "campaigns"
    on_layout = CampaignLayout(str(output_root / on_id))
    off_layout = CampaignLayout(str(output_root / off_id))
    target_pair_root = target_root / "critic-pair"
    target_pair_root.mkdir(parents=True, exist_ok=False)
    source_pair_root = source.on_receipt.parents[1]
    C._write_exclusive_bytes(
        target_pair_root / "admission_record_sidecar.json",
        (source_pair_root / "admission_record_sidecar.json").read_bytes(),
    )
    source_pair_id = json.loads(source.on_receipt.read_bytes())["pair_id"]
    assert json.loads(source.off_receipt.read_bytes())["pair_id"] == source_pair_id
    pair_id = f"{source_pair_id}-replica-{iteration:03d}"
    timestamps = {
        assignment[0]: float(iteration * 10 + 1),
        assignment[1]: float(iteration * 10 + 2),
    }
    on_receipt = _clone_arm_evidence_with_writers(
        source=source,
        arm="on",
        cfg=source.on_cfg,
        source_layout=source.on_layout,
        source_receipt_path=source.on_receipt,
        target_layout=on_layout,
        target_pair_root=target_pair_root,
        pair_id=pair_id,
        iteration=iteration,
        ts=timestamps["on"],
        terminal=terminal,
        live_commit_receipt=source.on_commit_receipt,
        replay_non_commit_sidecar=replay_non_commit_sidecar,
    )
    off_receipt = _clone_arm_evidence_with_writers(
        source=source,
        arm="off",
        cfg=source.off_cfg,
        source_layout=source.off_layout,
        source_receipt_path=source.off_receipt,
        target_layout=off_layout,
        target_pair_root=target_pair_root,
        pair_id=pair_id,
        iteration=iteration,
        ts=timestamps["off"],
        terminal=terminal,
        live_commit_receipt=source.off_commit_receipt,
        replay_non_commit_sidecar=replay_non_commit_sidecar,
    )
    return _Evidence(
        admission=source.admission,
        on_cfg=source.on_cfg,
        off_cfg=source.off_cfg,
        on_layout=on_layout,
        off_layout=off_layout,
        on_receipt=on_receipt,
        off_receipt=off_receipt,
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


def _pre_evidence_rejection_request(
    publication: issuer.B4PrerunPublication,
    *,
    attempt_index: int = 0,
) -> dict[str, object]:
    return {
        "attempt_id": publication.manifest.rows[attempt_index].attempt_id,
        "on_campaign_root": "/pre-evidence/on",
        "off_campaign_root": "/pre-evidence/off",
        "on_terminal_receipt_path": "/pre-evidence/on/terminal.json",
        "off_terminal_receipt_path": "/pre-evidence/off/terminal.json",
        "treatment_fired": True,
    }


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


def test_validated_rejection_is_appended_as_one_canonical_event(
    tmp_path: Path,
) -> None:
    publication = _publication(tmp_path)
    result = P.publish_b4_attempt_result(
        publication=publication,
        request=_pre_evidence_rejection_request(publication),
    )

    assert isinstance(result, P.B4RawRecordDurableRejection), result
    assert result.attempt_id == publication.manifest.rows[0].attempt_id
    assert tuple(issue.code for issue in result.issues) == (
        P.B4RawRecordIssueCode.UNKNOWN_FIELD,
    )
    ledger = Path(publication.publication_root) / issuer.B4_RAW_RECORD_REJECTIONS_NAME
    ledger_bytes = ledger.read_bytes()
    assert ledger_bytes.endswith(b"\n")
    assert len(ledger_bytes.splitlines()) == 1
    assert stat.S_IMODE(ledger.stat().st_mode) == 0o600
    event = json.loads(ledger_bytes)
    assert set(event) == {
        "schema_version",
        "issuer_commitment_sha256",
        "attempt_id",
        "issues",
    }
    assert {
        "previous_event_sha256",
        "event_sha256",
        "event_index",
    }.isdisjoint(event)
    assert event["schema_version"] == "p3-b4-raw-record-rejection-event/v1"
    assert event["issuer_commitment_sha256"] == (
        publication.issuer_commitment_sha256
    )
    assert event["attempt_id"] == result.attempt_id
    assert event["issues"] == [
        {
            "artifact": result.issues[0].artifact,
            "field": result.issues[0].field,
            "code": result.issues[0].code.value,
            "detail": result.issues[0].detail,
        }
    ]
    history = P.load_b4_raw_record_rejection_history(publication)
    assert history.status == "readable"
    assert history.fragment_discarded is False
    assert history.events[0].issues == result.issues


def test_unterminated_tail_is_truncated_before_the_next_single_write(
    tmp_path: Path,
) -> None:
    publication = _publication(tmp_path)
    request = _pre_evidence_rejection_request(publication)
    first = P.publish_b4_attempt_result(
        publication=publication,
        request=request,
    )
    assert isinstance(first, P.B4RawRecordDurableRejection), first
    ledger = Path(publication.publication_root) / issuer.B4_RAW_RECORD_REJECTIONS_NAME
    ledger.write_bytes(ledger.read_bytes() + b'{"unterminated"')
    partial_history = P.load_b4_raw_record_rejection_history(publication)
    assert partial_history.status == "readable"
    assert partial_history.fragment_discarded is True
    assert len(partial_history.events) == 1

    second = P.publish_b4_attempt_result(
        publication=publication,
        request=request,
    )

    assert isinstance(second, P.B4RawRecordDurableRejection), second
    assert second.rejection_history_fragment_discarded is True
    ledger_bytes = ledger.read_bytes()
    assert b'{"unterminated"' not in ledger_bytes
    assert ledger_bytes.endswith(b"\n")
    history = P.load_b4_raw_record_rejection_history(publication)
    assert history.status == "readable"
    assert history.fragment_discarded is False
    assert len(history.events) == 3
    first_event, fragment_event, second_event = history.events
    assert first_event.attempt_id == first.attempt_id
    assert first_event.issues == first.issues
    assert fragment_event.attempt_id is None
    assert tuple(issue.code for issue in fragment_event.issues) == (
        P.B4RawRecordIssueCode.IO_ERROR,
    )
    assert fragment_event.issues == (
        P.B4RawRecordIssue(
            artifact=str(ledger),
            field="rejection_history",
            code=P.B4RawRecordIssueCode.IO_ERROR,
            detail=(
                "unterminated rejection ledger fragment was discarded before append"
            ),
        ),
    )
    assert second_event.attempt_id == second.attempt_id
    assert second_event.issues == second.issues

    report = material_report.build_material_report_document(
        publication.publication_root
    ).json_value
    projected_events = report["producer_rejections"]["events"]
    assert [event["attempt_id"] for event in projected_events] == [
        first.attempt_id,
        None,
        second.attempt_id,
    ]
    assert projected_events[1]["issues"][0]["detail"] == (
        "unterminated rejection ledger fragment was discarded before append"
    )


def test_rejection_append_failure_adds_io_error_without_publishing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publication = _publication(tmp_path)
    monkeypatch.setattr(
        P,
        "_append_rejection_event",
        mock.Mock(side_effect=OSError("injected ledger failure")),
    )

    result = P.publish_b4_attempt_result(
        publication=publication,
        request=_pre_evidence_rejection_request(publication),
    )

    assert isinstance(result, P.B4RawRecordDurableRejection), result
    assert tuple(issue.code for issue in result.issues) == (
        P.B4RawRecordIssueCode.UNKNOWN_FIELD,
        P.B4RawRecordIssueCode.IO_ERROR,
    )
    target = publication.planned_result_artifacts[0].artifact_path
    assert not Path(target).exists()
    ledger = Path(publication.publication_root) / issuer.B4_RAW_RECORD_REJECTIONS_NAME
    assert not ledger.exists()


def test_rejection_fsync_failure_rolls_back_to_preappend_length(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publication = _publication(tmp_path)
    request = _pre_evidence_rejection_request(publication)
    first = P.publish_b4_attempt_result(
        publication=publication,
        request=request,
    )
    assert isinstance(first, P.B4RawRecordDurableRejection), first
    ledger = Path(publication.publication_root) / issuer.B4_RAW_RECORD_REJECTIONS_NAME
    before = ledger.read_bytes()
    outcomes = iter((OSError("injected fsync failure"), None))

    def injected_fsync(_fd: int) -> None:
        outcome = next(outcomes)
        if outcome is not None:
            raise outcome

    monkeypatch.setattr(P.os, "fsync", injected_fsync)

    second = P.publish_b4_attempt_result(
        publication=publication,
        request=request,
    )

    assert isinstance(second, P.B4RawRecordDurableRejection), second
    assert tuple(issue.code for issue in second.issues) == (
        P.B4RawRecordIssueCode.UNKNOWN_FIELD,
        P.B4RawRecordIssueCode.IO_ERROR,
    )
    assert ledger.read_bytes() == before
    history = P.load_b4_raw_record_rejection_history(publication)
    assert len(history.events) == 1


def test_rejection_ledger_symlink_is_rejected_without_touching_target(
    tmp_path: Path,
) -> None:
    publication = _publication(tmp_path / "publication-case")
    ledger = Path(publication.publication_root) / issuer.B4_RAW_RECORD_REJECTIONS_NAME
    target = tmp_path / "outside-ledger-target"
    target.write_bytes(b"sentinel")
    ledger.symlink_to(target)

    result = P.publish_b4_attempt_result(
        publication=publication,
        request=_pre_evidence_rejection_request(publication),
    )

    assert isinstance(result, P.B4RawRecordDurableRejection), result
    assert tuple(issue.code for issue in result.issues) == (
        P.B4RawRecordIssueCode.UNKNOWN_FIELD,
        P.B4RawRecordIssueCode.IO_ERROR,
    )
    assert ledger.is_symlink()
    assert target.read_bytes() == b"sentinel"


def test_batch_records_only_rejections_after_publication_validation(
    tmp_path: Path,
) -> None:
    publication = _publication(tmp_path / "items")
    results = P.publish_b4_attempt_results(
        publication=publication,
        requests=[
            _pre_evidence_rejection_request(publication, attempt_index=0),
            _pre_evidence_rejection_request(publication, attempt_index=1),
        ],
    )
    assert [result.attempt_id for result in results] == [
        publication.manifest.rows[0].attempt_id,
        publication.manifest.rows[1].attempt_id,
    ]
    assert all(isinstance(result, P.B4RawRecordDurableRejection) for result in results)
    history = P.load_b4_raw_record_rejection_history(publication)
    assert [event.attempt_id for event in history.events] == [
        publication.manifest.rows[0].attempt_id,
        publication.manifest.rows[1].attempt_id,
    ]

    prevalidation = _publication(tmp_path / "prevalidation")
    rejected = P.publish_b4_attempt_results(
        publication=prevalidation,
        requests={"not": "a collection"},
    )
    assert tuple(issue.code for issue in rejected[0].issues) == (
        P.B4RawRecordIssueCode.ILL_TYPED,
    )
    ledger = Path(prevalidation.publication_root) / issuer.B4_RAW_RECORD_REJECTIONS_NAME
    assert not ledger.exists()


def test_batch_prescan_rejection_is_durably_recorded(
    tmp_path: Path,
) -> None:
    publication = _publication(tmp_path)
    existing = Path(publication.planned_result_artifacts[0].artifact_path)
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_bytes(b"not-json")

    results = P.publish_b4_attempt_results(
        publication=publication,
        requests=(),
    )

    assert len(results) == 1
    assert isinstance(results[0], P.B4RawRecordDurableRejection), results
    assert tuple(issue.code for issue in results[0].issues) == (
        P.B4RawRecordIssueCode.EVIDENCE_SCHEMA,
    )
    history = P.load_b4_raw_record_rejection_history(publication)
    assert len(history.events) == 1
    assert history.events[0].attempt_id is None
    assert tuple(issue.code for issue in history.events[0].issues) == (
        P.B4RawRecordIssueCode.EVIDENCE_SCHEMA,
    )


def test_batch_per_item_unexpected_exception_is_durably_recorded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publication = _publication(tmp_path)
    monkeypatch.setattr(
        P,
        "_request",
        mock.Mock(side_effect=RuntimeError("injected per-item failure")),
    )

    results = P.publish_b4_attempt_results(
        publication=publication,
        requests=[{}],
    )

    assert len(results) == 1
    assert isinstance(results[0], P.B4RawRecordDurableRejection), results
    assert tuple(issue.code for issue in results[0].issues) == (
        P.B4RawRecordIssueCode.IO_ERROR,
    )
    history = P.load_b4_raw_record_rejection_history(publication)
    assert len(history.events) == 1
    assert history.events[0].attempt_id is None
    assert tuple(issue.code for issue in history.events[0].issues) == (
        P.B4RawRecordIssueCode.IO_ERROR,
    )


def test_invalid_rejection_history_does_not_replace_assembly_rejection(
    tmp_path: Path,
) -> None:
    publication = _publication(tmp_path)
    ledger = Path(publication.publication_root) / issuer.B4_RAW_RECORD_REJECTIONS_NAME
    ledger.write_bytes(b"not-json\n")

    assembled = P.assemble_b4_raw_analysis(publication=publication)

    assert isinstance(assembled, P.B4RawAnalysisRejection), assembled
    assert tuple(issue.code for issue in assembled.issues) == (
        P.B4RawRecordIssueCode.INCOMPLETE_SET,
    )
    assert assembled.rejection_history.status == "invalid"
    assert assembled.rejection_history.events == ()


@pytest.fixture(scope="module")
def recorded_rejection_report(tmp_path_factory):
    publication = _publication(tmp_path_factory.mktemp("b4-recorded-rejection-report"))
    rejected = P.publish_b4_attempt_result(
        publication=publication,
        request=_pre_evidence_rejection_request(publication),
    )
    assert isinstance(rejected, P.B4RawRecordDurableRejection), rejected
    report = material_report.build_material_report_document(
        publication.publication_root
    ).json_value
    return publication, rejected, report


def test_unresolved_absent_attempts_exclude_matching_recorded_rejection(
    recorded_rejection_report,
) -> None:
    publication, rejected, report = recorded_rejection_report
    unresolved = report["producer_rejections"]["unresolved_absent_attempts"]
    assert {item["attempt_id"] for item in unresolved} == {
        planned.attempt_id
        for planned in publication.planned_result_artifacts
        if planned.attempt_id != rejected.attempt_id
    }


def test_unresolved_absence_retains_current_reason_non_guarantee(
    recorded_rejection_report,
) -> None:
    _publication_value, _rejected, report = recorded_rejection_report
    assert (
        "current_reason_for_an_absent_planned_leaf_cannot_be_determined"
        in report["provenance"]["report_non_guarantees"]
    )


def _certified_evidence_shared_root(tmp_path_factory) -> Path:
    base = Path(tmp_path_factory.getbasetemp())
    shared_parent = base.parent if base.name.startswith("popen-") else base
    return shared_parent / "b4-producer-certified-shared"


def _write_certified_evidence_metadata(
    metadata_path: Path,
    metadata: dict[str, object],
) -> None:
    payload = json.dumps(
        metadata,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    temp_fd, temp_name = tempfile.mkstemp(
        dir=metadata_path.parent,
        prefix=f".{metadata_path.name}.",
        suffix=".tmp",
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(temp_fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, metadata_path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


@contextlib.contextmanager
def _certified_evidence_lock_scope(
    shared: Path,
    *,
    access_mode: str,
    seed,
):
    """Seed under EX, then hold the requested lock through the caller scope."""

    shared.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(shared / "fixture.lock", os.O_RDWR | os.O_CREAT, 0o600)
    locked = False
    try:
        metadata_path = shared / "evidence.json"
        if not metadata_path.exists():
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            locked = True
            if not metadata_path.exists():
                evidence_root = shared / "evidence"
                if evidence_root.is_symlink() or evidence_root.is_file():
                    evidence_root.unlink()
                elif evidence_root.exists():
                    shutil.rmtree(evidence_root)
                seed()
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            locked = False

        body_operation = {
            "read": fcntl.LOCK_SH,
            "write": fcntl.LOCK_EX,
        }[access_mode]
        fcntl.flock(lock_fd, body_operation)
        locked = True
        yield metadata_path
    finally:
        try:
            if locked:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)


@contextlib.contextmanager
def _certified_evidence_fixture_scope(tmp_path_factory, *, access_mode: str):
    """Build one real pair per pytest run and hold its read or write lock."""

    shared = _certified_evidence_shared_root(tmp_path_factory)

    def seed() -> None:
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
        _write_certified_evidence_metadata(shared / "evidence.json", metadata)

    with _certified_evidence_lock_scope(
        shared,
        access_mode=access_mode,
        seed=seed,
    ) as metadata_path:
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
            stack.enter_context(mock.patch.object(C.shutil, "which", return_value=sys.executable))
            stack.enter_context(mock.patch.object(C, "exploration_campaign_layout", side_effect=layout_for))
            stack.enter_context(mock.patch.object(L, "exploration_campaign_layout", side_effect=layout_for))
            yield evidence


@pytest.fixture
def certified_evidence(tmp_path_factory):
    """Provide shared certified evidence under a reader lock."""

    with _certified_evidence_fixture_scope(
        tmp_path_factory,
        access_mode="read",
    ) as evidence:
        yield evidence


@pytest.fixture
def certified_evidence_writer(tmp_path_factory):
    """Provide shared certified evidence under a writer lock."""

    with _certified_evidence_fixture_scope(
        tmp_path_factory,
        access_mode="write",
    ) as evidence:
        yield evidence


def _seeded_certified_evidence_lock_root(tmp_path: Path) -> Path:
    shared = tmp_path / "certified-lock"
    shared.mkdir()
    (shared / "evidence.json").write_bytes(b"{}")
    return shared


def test_certified_evidence_lock_allows_two_readers(tmp_path: Path) -> None:
    """Without this check, an exclusive reader lock can pass while serializing all consumers."""

    shared = _seeded_certified_evidence_lock_root(tmp_path)
    seed = mock.Mock()
    with _certified_evidence_lock_scope(
        shared,
        access_mode="read",
        seed=seed,
    ):
        competing_fd = os.open(shared / "fixture.lock", os.O_RDWR)
        try:
            fcntl.flock(competing_fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
            fcntl.flock(competing_fd, fcntl.LOCK_UN)
        finally:
            os.close(competing_fd)
    seed.assert_not_called()


def test_certified_evidence_seeded_reader_never_requests_exclusive(
    tmp_path: Path,
) -> None:
    """Without this check, a seeded reader can briefly take EX and rebuild a serial chain."""

    shared = _seeded_certified_evidence_lock_root(tmp_path)
    operations: list[int] = []
    real_flock = fcntl.flock

    def observed_flock(fd: int, operation: int) -> None:
        operations.append(operation)
        real_flock(fd, operation)

    with mock.patch.object(fcntl, "flock", side_effect=observed_flock):
        with _certified_evidence_lock_scope(
            shared,
            access_mode="read",
            seed=mock.Mock(),
        ):
            pass

    assert fcntl.LOCK_SH in operations
    assert fcntl.LOCK_EX not in operations
    assert operations[-1] == fcntl.LOCK_UN


def test_certified_evidence_reader_blocks_nonblocking_writer(
    tmp_path: Path,
) -> None:
    """Without this check, an unlocked reader can observe a writer's temporary damage."""

    shared = _seeded_certified_evidence_lock_root(tmp_path)
    with _certified_evidence_lock_scope(
        shared,
        access_mode="read",
        seed=mock.Mock(),
    ):
        competing_fd = os.open(shared / "fixture.lock", os.O_RDWR)
        try:
            with pytest.raises(OSError) as exc_info:
                fcntl.flock(
                    competing_fd,
                    fcntl.LOCK_EX | fcntl.LOCK_NB,
                )
            assert exc_info.value.errno in {
                errno.EWOULDBLOCK,
                errno.EAGAIN,
            }
        finally:
            os.close(competing_fd)


def test_certified_evidence_writer_blocks_nonblocking_reader(
    tmp_path: Path,
) -> None:
    """Without this check, a shared writer lock can expose temporary damage to readers."""

    shared = _seeded_certified_evidence_lock_root(tmp_path)
    with _certified_evidence_lock_scope(
        shared,
        access_mode="write",
        seed=mock.Mock(),
    ):
        competing_fd = os.open(shared / "fixture.lock", os.O_RDWR)
        try:
            with pytest.raises(OSError) as exc_info:
                fcntl.flock(
                    competing_fd,
                    fcntl.LOCK_SH | fcntl.LOCK_NB,
                )
            assert exc_info.value.errno in {
                errno.EWOULDBLOCK,
                errno.EAGAIN,
            }
        finally:
            os.close(competing_fd)


def test_certified_evidence_seed_double_check_observes_competing_seed(
    tmp_path: Path,
) -> None:
    """Without this check, two workers can both seed and split metadata from evidence."""

    shared = tmp_path / "certified-lock"
    shared.mkdir()
    metadata_path = shared / "evidence.json"
    real_exists = Path.exists
    real_flock = fcntl.flock
    first_metadata_check = True
    operations: list[int] = []
    seed = mock.Mock()

    def staged_exists(path: Path) -> bool:
        nonlocal first_metadata_check
        if path == metadata_path and first_metadata_check:
            first_metadata_check = False
            return False
        return real_exists(path)

    def competing_flock(fd: int, operation: int) -> None:
        real_flock(fd, operation)
        operations.append(operation)
        if operation == fcntl.LOCK_EX:
            metadata_path.write_bytes(b"{}")

    with (
        mock.patch.object(
            Path,
            "exists",
            autospec=True,
            side_effect=staged_exists,
        ),
        mock.patch.object(fcntl, "flock", side_effect=competing_flock),
    ):
        with _certified_evidence_lock_scope(
            shared,
            access_mode="read",
            seed=seed,
        ):
            pass

    seed.assert_not_called()
    assert operations[:3] == [
        fcntl.LOCK_EX,
        fcntl.LOCK_UN,
        fcntl.LOCK_SH,
    ]


def test_certified_evidence_fixture_scope_holds_both_modes_through_yield(
    tmp_path_factory,
) -> None:
    """Without this check, the real fixture can lose its mode or unlock before yield."""

    shared = _certified_evidence_shared_root(tmp_path_factory)

    def assert_competing_lock_is_blocked(operation: int) -> None:
        competing_fd = os.open(shared / "fixture.lock", os.O_RDWR)
        try:
            with pytest.raises(OSError) as exc_info:
                fcntl.flock(competing_fd, operation | fcntl.LOCK_NB)
            assert exc_info.value.errno in {
                errno.EWOULDBLOCK,
                errno.EAGAIN,
            }
        finally:
            os.close(competing_fd)

    with _certified_evidence_fixture_scope(
        tmp_path_factory,
        access_mode="read",
    ):
        competing_reader_fd = os.open(shared / "fixture.lock", os.O_RDWR)
        try:
            fcntl.flock(
                competing_reader_fd,
                fcntl.LOCK_SH | fcntl.LOCK_NB,
            )
            fcntl.flock(competing_reader_fd, fcntl.LOCK_UN)
        finally:
            os.close(competing_reader_fd)
        assert_competing_lock_is_blocked(fcntl.LOCK_EX)

    with _certified_evidence_fixture_scope(
        tmp_path_factory,
        access_mode="write",
    ):
        assert_competing_lock_is_blocked(fcntl.LOCK_SH)


def test_certified_evidence_fixture_scope_yield_is_inside_lock_ast() -> None:
    """Without this check, scopes can drop mode forwarding or yield outside locks."""

    module = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in module.body
        if isinstance(node, ast.FunctionDef)
    }
    scope = functions["_certified_evidence_fixture_scope"]
    yields = [node for node in ast.walk(scope) if isinstance(node, ast.Yield)]
    lock_withs = [
        node
        for node in ast.walk(scope)
        if isinstance(node, ast.With)
        and any(
            isinstance(item.context_expr, ast.Call)
            and isinstance(item.context_expr.func, ast.Name)
            and item.context_expr.func.id == "_certified_evidence_lock_scope"
            for item in node.items
        )
    ]

    assert len(yields) == 1
    assert len(lock_withs) == 1
    lock_call = next(
        item.context_expr
        for item in lock_withs[0].items
        if isinstance(item.context_expr, ast.Call)
        and isinstance(item.context_expr.func, ast.Name)
        and item.context_expr.func.id == "_certified_evidence_lock_scope"
    )
    mode_keywords = [
        keyword
        for keyword in lock_call.keywords
        if keyword.arg == "access_mode"
    ]
    assert len(mode_keywords) == 1
    assert isinstance(mode_keywords[0].value, ast.Name)
    assert mode_keywords[0].value.id == "access_mode"
    assert any(
        yields[0] in tuple(ast.walk(statement))
        for statement in lock_withs[0].body
    )

    for fixture_name, expected_mode in {
        "certified_evidence": "read",
        "certified_evidence_writer": "write",
    }.items():
        wrapper = functions[fixture_name]
        wrapper_yields = [
            node for node in ast.walk(wrapper) if isinstance(node, ast.Yield)
        ]
        fixture_withs = [
            node
            for node in ast.walk(wrapper)
            if isinstance(node, ast.With)
            and any(
                isinstance(item.context_expr, ast.Call)
                and isinstance(item.context_expr.func, ast.Name)
                and item.context_expr.func.id
                == "_certified_evidence_fixture_scope"
                for item in node.items
            )
        ]
        assert len(wrapper_yields) == 1
        assert len(fixture_withs) == 1
        fixture_call = next(
            item.context_expr
            for item in fixture_withs[0].items
            if isinstance(item.context_expr, ast.Call)
            and isinstance(item.context_expr.func, ast.Name)
            and item.context_expr.func.id == "_certified_evidence_fixture_scope"
        )
        wrapper_mode_keywords = [
            keyword
            for keyword in fixture_call.keywords
            if keyword.arg == "access_mode"
        ]
        assert len(wrapper_mode_keywords) == 1
        assert isinstance(wrapper_mode_keywords[0].value, ast.Constant)
        assert wrapper_mode_keywords[0].value.value == expected_mode
        assert any(
            wrapper_yields[0] in tuple(ast.walk(statement))
            for statement in fixture_withs[0].body
        )


def test_certified_evidence_seed_publishes_metadata_only_through_atomic_helper_ast(
) -> None:
    """Without this check, production seed can bypass the atomic metadata helper."""

    module = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    scope = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_certified_evidence_fixture_scope"
    )
    seeds = [
        node
        for node in scope.body
        if isinstance(node, ast.FunctionDef) and node.name == "seed"
    ]
    assert len(seeds) == 1
    seed = seeds[0]

    def is_direct_metadata_path(expression: ast.expr) -> bool:
        return (
            isinstance(expression, ast.BinOp)
            and isinstance(expression.op, ast.Div)
            and isinstance(expression.left, ast.Name)
            and expression.left.id == "shared"
            and isinstance(expression.right, ast.Constant)
            and expression.right.value == "evidence.json"
        )

    calls = [node for node in ast.walk(seed) if isinstance(node, ast.Call)]
    helper_calls = [
        call
        for call in calls
        if isinstance(call.func, ast.Name)
        and call.func.id == "_write_certified_evidence_metadata"
    ]
    assert len(helper_calls) == 1
    assert helper_calls[0].args
    assert is_direct_metadata_path(helper_calls[0].args[0])

    forbidden_file_calls = [
        call
        for call in calls
        if (
            isinstance(call.func, ast.Name)
            and call.func.id == "open"
        )
        or (
            isinstance(call.func, ast.Attribute)
            and call.func.attr
            in {"write_bytes", "write_text", "open", "replace", "rename"}
        )
    ]
    assert forbidden_file_calls == []


def test_certified_evidence_metadata_is_fsynced_and_atomically_replaced(
    tmp_path: Path,
) -> None:
    """Without this check, a direct metadata write can publish a partial seed as ready."""

    metadata_path = tmp_path / "evidence.json"
    metadata = {"iteration": 1, "on_root": "on", "off_root": "off"}
    expected_payload = json.dumps(
        metadata,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    operations: list[tuple[object, ...]] = []
    allocations: list[tuple[int, Path]] = []
    real_mkstemp = tempfile.mkstemp
    real_fdopen = os.fdopen
    real_fsync = os.fsync
    real_replace = os.replace

    class ObservedStream:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def write(self, payload: bytes) -> int:
            written = self.stream.write(payload)
            operations.append(("write", self.stream.fileno(), payload))
            return written

        def flush(self) -> None:
            self.stream.flush()
            operations.append(("flush", self.stream.fileno()))

        def fileno(self) -> int:
            return self.stream.fileno()

    def observed_mkstemp(*args, **kwargs):
        fd, name = real_mkstemp(*args, **kwargs)
        allocations.append((fd, Path(name)))
        return fd, name

    def observed_fdopen(*args, **kwargs):
        return ObservedStream(real_fdopen(*args, **kwargs))

    def observed_fsync(fd: int) -> None:
        temp_path = next(
            path
            for allocated_fd, path in allocations
            if allocated_fd == fd
        )
        operations.append(("fsync", fd, temp_path.read_bytes()))
        real_fsync(fd)

    def observed_replace(source, target) -> None:
        operations.append(("replace", Path(source), Path(target)))
        real_replace(source, target)

    with (
        mock.patch.object(tempfile, "mkstemp", side_effect=observed_mkstemp),
        mock.patch.object(os, "fdopen", side_effect=observed_fdopen),
        mock.patch.object(os, "fsync", side_effect=observed_fsync),
        mock.patch.object(os, "replace", side_effect=observed_replace),
    ):
        _write_certified_evidence_metadata(metadata_path, metadata)

    assert len(allocations) == 1
    assert [operation[0] for operation in operations] == [
        "write",
        "flush",
        "fsync",
        "replace",
    ]
    temp_fd, temp_path = allocations[0]
    assert [operation[1] for operation in operations[:3]] == [temp_fd] * 3
    assert operations[0][2] == expected_payload
    assert operations[2][2] == expected_payload
    source, target = operations[3][1:]
    assert source == temp_path
    assert source != target
    assert source.parent == target.parent == metadata_path.parent
    assert source.name.startswith(f".{target.name}.")
    assert source.name.endswith(".tmp")
    assert target == metadata_path
    assert metadata_path.read_bytes() == expected_payload


def test_certified_evidence_writer_direct_test_file_path_mutation_closure_excludes_called_helpers() -> None:
    """Without this direct test-file path-mutation closure, excluding called helper writes, undeclared shared writers can pass."""

    expected_modes = {
        "test_m01_assembly_rederives_precursor_from_the_sealed_registry": "read",
        "test_m02_planned_path_lookup_and_publish_use_the_issuer_leaf": "read",
        "test_m03_assignment_comes_from_attempt_wal_first_record_timestamps": "read",
        "test_m04_final_assembly_rejects_different_on_off_pair_ids": "read",
        "test_m05_campaign_lock_classification_and_receipt_share_one_byte_buffer": "read",
        "test_m06_lowercase_wal_commit_maps_only_to_uppercase_raw_commit": "read",
        "test_m07_non_binary_exact_decimal_lexeme_is_preserved": "read",
        "test_m08_publication_rejects_reuse_of_campaign_iteration_arm_tuple": "read",
        "test_m10_certified_off_digest_absence_sets_treatment_fired_true": "read",
        "test_m12_nonterminating_reference_ratio_has_only_named_rejection": "read",
        "test_m13_integer_reference_is_the_only_integer_acceptance_control": "read",
        "test_m16_judgment_fields_are_unknown_request_fields": "read",
        "test_m17_terminal_receipt_validation_survives_original_replacement": "write",
        "test_m18_symlinked_evidence_is_rejected_with_regular_control": "write",
        "test_assembly_rederives_judgments_and_requires_non_guarantees": "read",
        "test_manifest_driver_must_match_campaign_and_receipt_driver_kind": "read",
        "test_non_guarantees_name_the_residual_lock_and_closure_limits": "read",
    }
    fixture_modes = {
        "certified_evidence": "read",
        "certified_evidence_writer": "write",
    }
    mutators = {
        "write_bytes",
        "write_text",
        "rename",
        "replace",
        "unlink",
        "symlink_to",
        "hardlink_to",
        "mkdir",
        "rmdir",
        "touch",
        "chmod",
    }
    module = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in module.body
        if isinstance(node, ast.FunctionDef)
    }

    wrapper_modes = {}
    for fixture_name in fixture_modes:
        calls = [
            node
            for node in ast.walk(functions[fixture_name])
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_certified_evidence_fixture_scope"
        ]
        assert len(calls) == 1
        mode_keyword = next(
            keyword
            for keyword in calls[0].keywords
            if keyword.arg == "access_mode"
        )
        assert isinstance(mode_keyword.value, ast.Constant)
        wrapper_modes[fixture_name] = mode_keyword.value.value
    assert wrapper_modes == fixture_modes

    declared_modes = {}
    fixture_arguments = {}
    for function_name, function in functions.items():
        arguments = [
            argument.arg
            for argument in function.args.args
            if argument.arg in fixture_modes
        ]
        if arguments:
            assert len(arguments) == 1
            fixture_arguments[function_name] = arguments[0]
            declared_modes[function_name] = fixture_modes[arguments[0]]
    assert declared_modes == expected_modes

    def is_tainted(expression: ast.expr, tainted_names: set[str]) -> bool:
        if isinstance(expression, ast.Name):
            return expression.id in tainted_names
        if isinstance(expression, ast.Attribute):
            return is_tainted(expression.value, tainted_names)
        if isinstance(expression, ast.Call):
            if (
                isinstance(expression.func, ast.Name)
                and expression.func.id == "Path"
                and expression.args
            ):
                return is_tainted(expression.args[0], tainted_names)
            if (
                isinstance(expression.func, ast.Attribute)
                and expression.func.attr == "with_name"
            ):
                return is_tainted(expression.func.value, tainted_names)
        return False

    def assigned_names(target: ast.expr) -> set[str]:
        if isinstance(target, ast.Name):
            return {target.id}
        if isinstance(target, (ast.Tuple, ast.List)):
            return {
                name
                for element in target.elts
                for name in assigned_names(element)
            }
        return set()

    mutation_functions = set()
    for function_name in expected_modes:
        function = functions[function_name]
        tainted_names = {fixture_arguments[function_name]}
        changed = True
        while changed:
            changed = False
            for node in ast.walk(function):
                targets: list[ast.expr] = []
                value = None
                if isinstance(node, ast.Assign):
                    targets = node.targets
                    value = node.value
                elif isinstance(node, ast.AnnAssign):
                    targets = [node.target]
                    value = node.value
                if value is None or not is_tainted(value, tainted_names):
                    continue
                discovered = {
                    name
                    for target in targets
                    for name in assigned_names(target)
                }
                if not discovered.issubset(tainted_names):
                    tainted_names.update(discovered)
                    changed = True

        if any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in mutators
            and is_tainted(node.func.value, tainted_names)
            for node in ast.walk(function)
        ):
            mutation_functions.add(function_name)

    expected_writers = {
        "test_m17_terminal_receipt_validation_survives_original_replacement",
        "test_m18_symlinked_evidence_is_rejected_with_regular_control",
    }
    declared_writers = {
        function_name
        for function_name, mode in declared_modes.items()
        if mode == "write"
    }
    assert mutation_functions == declared_writers == expected_writers


def _build_full_publication_evidence(
    root: Path,
    *,
    terminal: str,
) -> _PublicationEvidence:
    """Build one real block and non-durable writer replicas for one positive."""

    # Issuance randomizes the schedule, so this exact publication must drive
    # both replica timestamps and the later producer validation.
    schedule_publication = _publication(root / "schedule")
    rows = schedule_publication.manifest.rows
    first_schedule = tuple(arm.value for arm in rows[0].assignment_schedule)
    admission = _committed_admission_fixture()
    with _evidence_scope(
        root / "block-001",
        iteration=1,
        assignment=first_schedule,
        terminal=terminal,
        admission=admission,
    ) as seed:
        evidence = [seed]
        # Replica bytes still pass through the production serializers and
        # writers. Durability is deliberately outside this fixture's claim.
        with mock.patch.object(os, "fsync", return_value=None):
            for ordinal, row in enumerate(rows[1:], start=2):
                schedule = tuple(arm.value for arm in row.assignment_schedule)
                evidence.append(_clone_evidence_with_writers(
                    seed,
                    root / f"block-{ordinal:03d}",
                    iteration=ordinal,
                    assignment=schedule,
                    terminal=terminal,
                ))
        return _PublicationEvidence(
            publication=schedule_publication,
            evidence=tuple(evidence),
        )


@pytest.fixture
def certified_publication_evidence(
    tmp_path: Path,
) -> _PublicationEvidence:
    return _build_full_publication_evidence(
        tmp_path / "certified-evidence",
        terminal="commit",
    )


@pytest.fixture
def terminal_absent_publication_evidence(
    tmp_path: Path,
) -> _PublicationEvidence:
    return _build_full_publication_evidence(
        tmp_path / "terminal-absent-evidence",
        terminal="absent",
    )


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
    with pytest.raises(ArithmeticError) as exc_info:
        P._fraction_token((1, 3))
    assert str(exc_info.value) == "reference_tps has no finite decimal expansion"

    control = _publication(tmp_path / "control")
    _assert_write(_publish(control, certified_evidence))

    publication = _publication(tmp_path / "publication-case")
    with mock.patch.object(
        P,
        "_fraction_token",
        side_effect=ArithmeticError(
            "reference_tps has no finite decimal expansion"
        ),
    ) as fraction_token:
        result = _publish(publication, certified_evidence)
        fraction_token.assert_called_once_with(
            publication.manifest.rows[0].reference_tps
        )

    assert isinstance(result, P.B4RawRecordRejection), result
    assert result.issues == (
        P.B4RawRecordIssue(
            artifact="publication",
            field="reference_tps",
            code=P.B4RawRecordIssueCode.DECIMAL_NOT_TERMINATING,
            detail="reference_tps has no finite decimal JSON representation",
        ),
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
        ledger = (
            Path(publication.publication_root)
            / issuer.B4_RAW_RECORD_REJECTIONS_NAME
        )
        assert not ledger.exists()


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
    certified_evidence_writer: _Evidence,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every later validator consumes the first terminal-receipt snapshot bytes."""
    publication = _publication(tmp_path)
    real = P._snapshot_regular
    receipt_path = str(certified_evidence_writer.on_receipt)
    original = certified_evidence_writer.on_receipt.read_bytes()
    replaced = False

    def replace_after_snapshot(path, **kwargs):
        nonlocal replaced
        snapshot = real(path, **kwargs)
        if os.fspath(path) == receipt_path and not replaced:
            certified_evidence_writer.on_receipt.write_bytes(
                b"not-the-snapshotted-receipt"
            )
            replaced = True
        return snapshot

    monkeypatch.setattr(P, "_snapshot_regular", replace_after_snapshot)
    try:
        _assert_write(_publish(publication, certified_evidence_writer))
    finally:
        certified_evidence_writer.on_receipt.write_bytes(original)
    assert replaced


def test_m18_symlinked_evidence_is_rejected_with_regular_control(
    tmp_path: Path,
    certified_evidence_writer: _Evidence,
) -> None:
    """Acceptance would follow a replaceable receipt leaf. Rejection preserves the regular-file control and rejects the symlinked locator."""
    control = _publication(tmp_path / "control")
    _assert_write(_publish(control, certified_evidence_writer))
    link = tmp_path / "terminal-link.json"
    link.symlink_to(certified_evidence_writer.on_receipt)
    publication = _publication(tmp_path / "attack")
    request = _request(
        certified_evidence_writer,
        publication.manifest.rows[0].attempt_id,
    )
    request["on_terminal_receipt_path"] = str(link)
    _assert_rejection(
        P.publish_b4_attempt_result(publication=publication, request=request),
        P.B4RawRecordIssueCode.EVIDENCE_SYMLINK,
    )

    role_file = Path(certified_evidence_writer.admission.role_file)
    held_role = role_file.with_name("critic-held.md")
    role_file.rename(held_role)
    role_file.symlink_to(held_role)
    try:
        role_publication = _publication(tmp_path / "role-attack")
        _assert_rejection(
            _publish(role_publication, certified_evidence_writer),
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


def _normalized_loop_state(data: bytes) -> dict[str, object]:
    value = json.loads(data)
    whiteboard = value["whiteboard"]
    offset = whiteboard[0]["iteration"] - 1
    value["iteration"] -= offset
    for entry in whiteboard:
        entry["iteration"] -= offset
    return value


def _normalized_receipt_bundle(terminal_path: Path) -> dict[str, object]:
    terminal = json.loads(terminal_path.read_bytes())
    invocation_id = terminal["invocation_id"]
    root = terminal_path.parent
    start = json.loads(
        (root / f"receipt_{invocation_id}_start.json").read_bytes()
    )
    start["pair_id"] = "<pair-identity>"
    terminal["pair_id"] = "<pair-identity>"
    terminal["iteration"] = 1
    terminal["loop_state_sha256"] = "<iteration-derived-sha256>"
    terminal["start_receipt_sha256"] = "<pair-derived-sha256>"
    unchanged = {}
    for stem, suffix in (
        ("payload", ".json"),
        ("argv", ".json"),
        ("effective_prompt", ".txt"),
        ("neutral_root_identity", ".json"),
        ("envelope", ".json"),
    ):
        name = f"{stem}_{invocation_id}{suffix}"
        unchanged[name] = (root / name).read_bytes()
    return {
        "start": start,
        "terminal": terminal,
        "admitted_wal": (
            root / f"admitted_view_{invocation_id}.wal"
        ).read_bytes(),
        "loop_state": _normalized_loop_state(
            (root / f"loop_state_{invocation_id}.json").read_bytes()
        ),
        "unchanged": unchanged,
    }


def _normalized_arm_evidence(
    evidence: _Evidence,
    *,
    arm: str,
) -> dict[str, object]:
    layout = evidence.on_layout if arm == "on" else evidence.off_layout
    terminal_path = evidence.on_receipt if arm == "on" else evidence.off_receipt
    terminal = json.loads(terminal_path.read_bytes())
    invocation_id = terminal["invocation_id"]
    admitted_bytes = (
        terminal_path.parent / f"admitted_view_{invocation_id}.wal"
    ).read_bytes()
    wal_bytes = Path(layout.wal_file).read_bytes()
    assert wal_bytes.startswith(admitted_bytes)
    suffix = []
    for frame in wal_bytes[len(admitted_bytes):].splitlines():
        record = json.loads(frame)
        record["ts"] = "<assignment-identity>"
        suffix.append(record)
    consumption_paths = tuple(
        Path(layout.root).glob("b4_closed_critic_consumption_*.json")
    )
    assert len(consumption_paths) == 1
    consumption = json.loads(consumption_paths[0].read_bytes())
    consumption["terminal_receipt_sha256"] = "<receipt-derived-sha256>"
    consumption["iteration"] = 1
    consumption["pair_id"] = "<pair-identity>"
    return {
        "campaign_lock": Path(layout.lock_file).read_bytes(),
        "launch_sidecar": (
            Path(layout.root) / P.launcher.B4_LAUNCH_SIDECAR
        ).read_bytes(),
        "admitted_wal": admitted_bytes,
        "attempt_suffix": suffix,
        "current_state": _normalized_loop_state(
            Path(L.loop_state_path(layout)).read_bytes()
        ),
        "receipt_bundle": _normalized_receipt_bundle(terminal_path),
        "consumption": consumption,
    }


def _assert_replicas_match_real_except_identity(
    evidence: tuple[_Evidence, ...],
) -> None:
    assert len(evidence) == EXPECTED_BLOCK_COUNT
    seed = evidence[0]
    seed_pair_id = json.loads(seed.on_receipt.read_bytes())["pair_id"]
    seed_sidecar = (
        seed.on_receipt.parents[1] / "admission_record_sidecar.json"
    ).read_bytes()
    expected = {
        arm: _normalized_arm_evidence(seed, arm=arm)
        for arm in ("on", "off")
    }
    for replica in evidence[1:]:
        assert replica.iteration != seed.iteration
        assert json.loads(replica.on_receipt.read_bytes())["pair_id"] != seed_pair_id
        assert (
            replica.on_receipt.parents[1] / "admission_record_sidecar.json"
        ).read_bytes() == seed_sidecar
        assert {
            arm: _normalized_arm_evidence(replica, arm=arm)
            for arm in ("on", "off")
        } == expected


def _publish_full_publication(
    *,
    publication: issuer.B4PrerunPublication,
    evidence: tuple[_Evidence, ...],
) -> tuple[issuer.B4PrerunPublication, P.B4RawAnalysisAssembly]:
    assert len(evidence) == len(publication.manifest.rows) == EXPECTED_BLOCK_COUNT
    admission = evidence[0].admission
    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(C, "REPOSITORY_ROOT", admission.repository))
        stack.enter_context(mock.patch.object(C, "ROLE_FILE", admission.role_file))
        requests = [
            _request(item, row.attempt_id)
            for item, row in zip(evidence, publication.manifest.rows)
        ]
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


def test_positive_201_block_all_terminal_records_absent(
    terminal_absent_publication_evidence: _PublicationEvidence,
) -> None:
    publication = terminal_absent_publication_evidence.publication
    evidence = terminal_absent_publication_evidence.evidence
    _assert_replicas_match_real_except_identity(evidence)
    publication, assembled = _publish_full_publication(
        publication=publication,
        evidence=evidence,
    )
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
    certified_publication_evidence: _PublicationEvidence,
) -> None:
    publication = certified_publication_evidence.publication
    evidence = certified_publication_evidence.evidence
    _assert_replicas_match_real_except_identity(evidence)
    ledger = Path(publication.publication_root) / issuer.B4_RAW_RECORD_REJECTIONS_NAME
    ledger.write_bytes(b"not-json\n")
    publication, assembled = _publish_full_publication(
        publication=publication,
        evidence=evidence,
    )
    assert assembled.rejection_history.status == "invalid"
    assert assembled.rejection_history.events == ()
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
