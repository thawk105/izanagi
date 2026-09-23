# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import ast
import base64
import copy
import contextlib
import dataclasses
import gc
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import sys
import time
import weakref
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from orchestrator.campaign import claude_transport
from orchestrator.campaign import autonomous_trial_completeness as completeness
from orchestrator.campaign import artifact_admission
from orchestrator.campaign import campaign_lock
from orchestrator.campaign import model as campaign_model
from orchestrator.campaign import p3_autonomous_workload_trial as A
from orchestrator.campaign import reflux_origin_client
from orchestrator.campaign import reflux_origin_ledger
from orchestrator.campaign import reflux_origin_topology
from orchestrator.campaign import reflux_source_closure
from orchestrator.campaign import s8b_prediction_runner as S
from orchestrator.campaign import wal
from orchestrator.campaign.claude_projected_provider import ClaudeProjectedRoleProvider
from orchestrator.campaign.s8b_prediction_runner import PredictionRunnerError
from orchestrator.campaign.s8c_generation_projection import PayloadValidationError
from orchestrator.campaign.reflux_ir import RefluxIRError, emit_predicate
from orchestrator.critic.digest import DiffQuarantineRejection
from orchestrator.calibrator import runner as calibrator_runner
from orchestrator.campaign import claude_projected_provider as P
from orchestrator.tests.campaign_lock_test_support import (
    _binding_from_recorded_head,
    build_v2_lock,
)
from orchestrator.tests import reflux_origin_fixture_builder as origin_fixtures

_ROLE_SINK_TRIAL_MAX_WORKERS = 4

_PRE_T343_NO_BUILD_CAMPAIGN_ID = (
    "p3-t178-ycsb-a-workload-conditioned-autonomous-948f4c43"
)
_T343_NO_BUILD_CAMPAIGN_ID = (
    "p3-t178-ycsb-a-workload-conditioned-autonomous-67a4e01c"
)
_T816_NO_BUILD_CAMPAIGN_ID = (
    "p3-t178-ycsb-a-workload-conditioned-autonomous-4b75e24e"
)
# T-2304 admission-policy epoch.
_T2304_NO_BUILD_CAMPAIGN_ID = (
    "p3-t178-ycsb-a-workload-conditioned-autonomous-d567badf"
)
_CURRENT_NO_BUILD_CAMPAIGN_ID = (
    "p3-t178-ycsb-a-workload-conditioned-autonomous-7e44fb98"
)
_T530_NO_BUILD_CAMPAIGN_ID = (
    "p3-t178-ycsb-a-workload-conditioned-autonomous-4bf2256c"
)
_T530_CONTRACT = A.env_contract.GENERATIONS["linux-baremetal"][0].contract
assert _T530_CONTRACT.contract_sha256 == (
    "1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7"
)
_T530_PEGASUS_CONTRACT = A.env_contract.GENERATIONS["pegasus"][1].contract
assert _T530_PEGASUS_CONTRACT.contract_sha256 == (
    "1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c"
)
# T-671 で契約 H が identity から外れ、C01 の golden も H なし preimage へ戻る。
_T816_C01_OTHER_CAMPAIGN_ID = (
    "p3-t178-ycsb-a-workload-conditioned-autonomous-841e8a89"
)
# T-2304 admission-policy epoch.
_T2304_C01_OTHER_CAMPAIGN_ID = (
    "p3-t178-ycsb-a-workload-conditioned-autonomous-407fa1aa"
)
_C01_OTHER_CAMPAIGN_ID = (
    "p3-t178-ycsb-a-workload-conditioned-autonomous-0c1663e7"
)
_T816_C01_PEGASUS_CAMPAIGN_ID = (
    "p3-t178-ycsb-a-workload-conditioned-autonomous-7b2f2838"
)
# T-2304 admission-policy epoch.
_T2304_C01_PEGASUS_CAMPAIGN_ID = (
    "p3-t178-ycsb-a-workload-conditioned-autonomous-46384c28"
)
_C01_PEGASUS_CAMPAIGN_ID = (
    "p3-t178-ycsb-a-workload-conditioned-autonomous-cc139af4"
)


class _CliGateReached(Exception):
    """Sentinel proving that an accepted CLI path reached its next operation."""


def _no_build_context():
    return A.build_run_context(generator_id=A.GeneratorId.S8A_TRIGGER_SWEEP)


def _coder_authority():
    parser = argparse.ArgumentParser()
    A.add_coder_build_authority_argument(parser)
    return parser.parse_args([
        "--allow-coder-derived-build",
    ]).coder_build_authority


@contextlib.contextmanager
def _exploratory_scope(trial_id: str, workloads: list[str]):
    admission = A.trial_registry.admit_unregistered_exploratory(
        trial_id=trial_id,
        workloads=workloads,
        allow_unregistered_exploratory=True,
        repository_root=A.ROOT,
        registry_path=A.ROOT / A.trial_registry.DEFAULT_REGISTRY_PATH,
    )
    scope = A._RunScopeBinding(admission, A._RUN_SCOPE_SEAL)
    token = A._ACTIVE_TRIAL_BINDING.set(scope)
    try:
        yield admission
    finally:
        A._ACTIVE_TRIAL_BINDING.reset(token)


def _run_workload_with_scope(**kwargs):
    kwargs.setdefault(
        "gating_spec_snapshot", A.snapshot_gating_spec(A.GATING_SPEC),
    )
    with _exploratory_scope(kwargs["trial_id"], [kwargs["workload"]]):
        return A._run_workload(**kwargs)


def _fake_drive(
    cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
    cache_root="", proposal_path="", extra_sources=(), dependency_prefix="",
):
    assert do_build is False
    assert dependency_prefix == ""
    assert cfg.search_config["descriptor_sha256"]
    assert perf.workload == cfg.search_config["ycsb"]
    assert auditor.diff_digest == hashlib.sha256(b"fixture diff").hexdigest()
    Path(layout.root).mkdir(parents=True, exist_ok=True)
    state = A.loop_core.load_loop_state(layout) or A.loop_core.LoopState()
    state.iteration += 1
    state.whiteboard.append(A.loop_core.WhiteboardEntry(
        iteration=state.iteration,
        direction=planner.direction,
        magnitude=planner.magnitude,
        result="success",
        delta_pct=None,
    ))
    A.loop_core.save_loop_state(layout, state)
    return {
        "outcome": "dry-pass",
        "variant": None,
        "stop_reason": "continue",
        "iteration": 1,
        "ran": True,
        "trigger_gate_binding_commitment": "b" * 64,
        "critic_digest_generated": False,
    }


_RELATION_GENOME = A.loop_core.Genome(
    "silo", dict(A.trigger._BASE),
)


def _write_admitted_rejection_digest(
    cfg, layout, coder, *, binding=None,
) -> str:
    """実 WAL と実 renderer で no-build reject の digest を作る。"""
    layout = A.CampaignLayout(
        str(Path(layout.root).parent / str(A.trigger.ident.campaign_id(cfg)))
    )
    ir = A.parse_wire(coder.wire)
    implementation = emit_predicate(ir)
    binding_api = A.loop_core.trigger_gate_binding
    trigger_gate_binding = binding_api.TriggerGateBinding(
        mask=ir.mask,
        predicate_sha256=binding_api.expected_predicate_sha256(ir.mask),
        nonce=binding_api.new_nonce(),
        source=None,
    )
    rejection = A.loop_core.DiffQuarantineResult(
        passed=False,
        reason="fixture rejection",
        digest={
            "rejection_type": "diff-quarantine",
            "subtype": "fixture-reject",
            "reason": "fixture rejection",
            "diff_region": A.trigger.SOURCE_REL,
            "template_diff_id": A.trigger.MARKER_ID,
            "evidence": "fixture evidence",
        },
    )
    variant = A.loop_core.record_diff_reject(
        layout, _RELATION_GENOME, implementation, rejection,
        trigger_gate_binding=trigger_gate_binding,
    )
    starts = [
        record
        for record in wal.read_records(layout)
        if record.stage == campaign_model.STAGE_BUILD_START
    ]
    provenance = {
        "entries": {
            str(index): {
                "variant": record.variant,
                "build_attempt_id": record.payload["build_attempt_id"],
                wal.TRIGGER_BINDING_COMMITMENT_KEY: record.payload[
                    wal.TRIGGER_BINDING_COMMITMENT_KEY
                ],
            }
            for index, record in enumerate(starts, 1)
        },
    }
    reports = Path(layout.root) / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / artifact_admission._TRIGGER_PROVENANCE_BASENAME).write_bytes(
        A._canonical_json_bytes(provenance) + b"\n"
    )
    A.loop_core.wal.write_lock(
        layout, build_v2_lock(
            A.ident.canonical_preimage(cfg), binding=binding,
        )
    )
    critic_view = A.require_admitted_campaign(
        layout.root,
        purpose=A.CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )
    raw_digest = A.loop_core.make_critic_digest(
        critic_view,
        tag=A.trigger.CRITIC_TAG,
        reflux=(cfg.search_config.get("reflux") == "on"),
        identity_projection=A.loop_core.IdentityProjection.RAW,
    )
    (Path(layout.root) / A.trigger.DIGEST_BASENAME).write_text(
        raw_digest, encoding="utf-8",
    )
    return variant


def _drive_with_raw_identity_digest(
    cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
    cache_root="", proposal_path="", extra_sources=(),
):
    assert do_build is False
    variant = _write_admitted_rejection_digest(cfg, layout, coder)
    return {
        "outcome": "rejected",
        "variant": variant,
        "verdict": "auditor-pass",
        "stop_reason": "continue",
        "iteration": 1,
        "ran": True,
        "trigger_gate_binding_commitment": "b" * 64,
        "critic_digest_generated": True,
    }


def _fake_drive_with_finite_metrics(
    cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
    cache_root="", proposal_path="", extra_sources=(),
):
    outcome = _fake_drive(
        cfg,
        perf,
        planner,
        coder,
        auditor,
        prior,
        sub,
        do_build,
        layout=layout,
        cache_root=cache_root,
        proposal_path=proposal_path,
        extra_sources=extra_sources,
    )
    outcome.update({
        "outcome": "certified",
        "variant": None,
        "fitness_tps": 12345.0,
        "records": {
            "bench_done": {
                "leading_indicators": {
                    "abort_rate": 0.079,
                    "llc_miss_rate": 0.124,
                    "latency_ns": 456.0,
                    "ipc": 2.5,
                }
            }
        },
        "critic_digest_generated": False,
    })
    return outcome


def _fake_preview(coder, *, sub):
    return {
        "passed": True,
        "working_diff": "fixture diff",
        "diff_digest": hashlib.sha256(b"fixture diff").hexdigest(),
        "subtype": None,
        "reason": "",
        "forbidden_identifiers": [],
    }


class _RecordingFixture(A.FixtureRoleProvider):
    def __init__(self, role):
        super().__init__(role)
        self.payloads = []
        self.payload_bytes = []

    def invoke(self, *, invocation_id, payload):
        self.payloads.append(dict(payload))
        self.payload_bytes.append(A._canonical_json_bytes(payload))
        return super().invoke(invocation_id=invocation_id, payload=payload)


class _ArtifactRecordingFixture(_RecordingFixture):
    def __init__(self, role, artifact_root: Path):
        super().__init__(role)
        self.artifact_root = artifact_root
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.invocation_ids = []

    def invoke(self, *, invocation_id, payload):
        self.invocation_ids.append(invocation_id)
        payload_bytes = A._canonical_json_bytes(payload)
        envelope_bytes = b'{"result":"fixture","type":"result"}'
        (self.artifact_root / f"payload_{invocation_id}.json").write_bytes(
            payload_bytes
        )
        (self.artifact_root / f"envelope_{invocation_id}.json").write_bytes(
            envelope_bytes
        )
        response = super().invoke(
            invocation_id=invocation_id, payload=payload,
        )
        return dataclasses.replace(
            response,
            provenance={
                **response.provenance,
                "envelope_sha256": hashlib.sha256(envelope_bytes).hexdigest(),
            },
        )


class _MalformedRecordingCritic:
    def __init__(self) -> None:
        self.payloads = []

    def invoke(self, *, invocation_id, payload):
        self.payloads.append(dict(payload))
        return A.ProviderResponse(
            raw_response="{}",
            provenance={"child_id": invocation_id},
        )


class _WireRecordingFixture(_RecordingFixture):
    def __init__(self, role, *, wire):
        super().__init__(role)
        self.wire = wire

    def invoke(self, *, invocation_id, payload):
        response = super().invoke(invocation_id=invocation_id, payload=payload)
        if self.role != "coder":
            return response
        value = json.loads(response.raw_response)
        value["proposal"]["wire"] = self.wire
        return dataclasses.replace(
            response,
            raw_response=A._canonical_json_bytes(value).decode("utf-8"),
        )


def _actual_campaign_layout(
    run_root: Path, *, trial_id: str, generations: int = 1,
) -> A.CampaignLayout:
    flags = A.WORKLOADS["ycsb-a"]
    descriptor, descriptor_record = A._descriptor_for(flags)
    cfg = A._campaign_for(
        workload="ycsb-a",
        entry=flags,
        descriptor=descriptor,
        descriptor_record=descriptor_record,
        trial_id=trial_id,
        generations=generations,
        contract=_T530_CONTRACT,
        build_context=_no_build_context(),
    )
    return A.CampaignLayout(
        str(run_root / "campaigns" / str(A.trigger.ident.campaign_id(cfg)))
    )


def test_no_build_campaign_identity_binds_shared_policy_context() -> None:
    flags = A.WORKLOADS["ycsb-a"]
    descriptor, descriptor_record = A._descriptor_for(flags)
    context = _no_build_context()
    cfg = A._campaign_for(
        workload="ycsb-a", entry=flags,
        descriptor=descriptor, descriptor_record=descriptor_record,
        trial_id="fixture-completeness", generations=1,
        contract=_T530_CONTRACT, build_context=context,
    )
    assert cfg.search_config["build_admission"] == context.policy.as_preimage()
    # T-671 で H が identity から外れた current golden を独立に pin する。
    assert str(A.ident.campaign_id(cfg)) == _CURRENT_NO_BUILD_CAMPAIGN_ID
    assert _T343_NO_BUILD_CAMPAIGN_ID == (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-67a4e01c"
    )
    assert _PRE_T343_NO_BUILD_CAMPAIGN_ID == (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-948f4c43"
    )
    assert str(A.ident.campaign_id(cfg)) != _T816_NO_BUILD_CAMPAIGN_ID
    assert str(A.ident.campaign_id(cfg)) != _T2304_NO_BUILD_CAMPAIGN_ID
    assert str(A.ident.campaign_id(cfg)) != _T530_NO_BUILD_CAMPAIGN_ID


def test_t1333_exploratory_entries_preserve_baseline_projection_bytes() -> None:
    expected = {
        "ycsb-a": "905581959eac248cd744313e33b64627d6db880f9abba9a7016d04681f507b98",
        "ycsb-b": "980fc86a4ecd623b56b647a8553e419575611410b7919d01ed4896ff38907ac8",
        "ycsb-c": "865793da2a7824d003f6badd07aa8b1219bd6df5249ddb0d28f8ae0661317039",
    }
    assert tuple(A.WORKLOADS) == ("ycsb-a", "ycsb-b", "ycsb-c")
    for workload, expected_sha256 in expected.items():
        entry = A.WORKLOADS[workload]
        assert set(entry) == {"ycsb", "records", "threads"}
        descriptor, descriptor_record = A._descriptor_for(entry)
        value = {
            "descriptor": descriptor,
            "descriptor_record": descriptor_record,
            "perf": dataclasses.asdict(A._perf_for(entry)),
            "workload_flags": dict(entry["ycsb"]),
        }
        assert hashlib.sha256(A._canonical_json_bytes(value)).hexdigest() == (
            expected_sha256
        )


def test_t1333_all_three_sinks_use_the_same_synthetic_scale_entry() -> None:
    entry = A.WorkloadEntry(
        ycsb=dict(A.WORKLOADS["ycsb-a"]["ycsb"]),
        records=123_457,
        threads=13,
    )
    descriptor, descriptor_record = A._descriptor_for(entry)
    campaign = A._campaign_for(
        workload="ycsb-a",
        entry=entry,
        descriptor=descriptor,
        descriptor_record=descriptor_record,
        trial_id="synthetic-entry",
        generations=1,
        contract=_T530_CONTRACT,
        build_context=_no_build_context(),
    )
    perf = A._perf_for(entry)
    assert campaign.search_config["records"] == perf.records == 123_457
    assert campaign.search_config["threads"] == perf.threads == 13
    assert descriptor["scale"] == {"records": 123_457, "threads": 13}
    assert campaign.search_config["ycsb"] == perf.workload == entry["ycsb"]


def test_t1349_formal_entries_bind_legacy_module_and_arm_descriptor() -> None:
    known_digests = {
        "rr80": "80501db0235d88314edd4a4c29a1949e67acc2b466ae426fbbb1cb3da4b7d843",
        "rr20": "53230b8b1f0e0d82def3c384f4d8d8b050a1ce872afd2ed9e2a403c61c3c550b",
    }
    source_record = A._formal_profile_source_record(repository_root=A.ROOT)
    legacy = A.s8b_ratified_freeze.load_legacy_freeze(A.ROOT)
    assert source_record["path"] == A.s8b_ratified_freeze.V1_FREEZE_PATH
    assert source_record["sha256"] == legacy.sha256
    for name, authority in A.s8b_holdout_freeze.HOLDOUTS.items():
        entry = A.FORMAL_WORKLOADS[name]
        assert set(entry) == {"candidate_id", "ycsb", "records", "threads"}
        descriptor, record = A._descriptor_for(entry)
        perf = A._perf_for(entry)
        campaign = A._campaign_for(
            workload=name,
            entry=entry,
            descriptor=descriptor,
            descriptor_record=record,
            trial_id=f"formal-{name}",
            generations=1,
            contract=_T530_CONTRACT,
            build_context=_no_build_context(),
        )
        selected_name, arm_descriptor = A.s8c_arm_inputs._descriptor_for_candidate(
            authority["candidate_id"]
        )
        assert selected_name == name
        assert descriptor == arm_descriptor
        assert record["output_sha256"] == known_digests[name]
        assert campaign.search_config["records"] == perf.records == entry["records"]
        assert campaign.search_config["threads"] == perf.threads == entry["threads"]
        assert campaign.search_config["ycsb"] == perf.workload == entry["ycsb"]


def test_t1349_formal_ycsb_entries_do_not_alias_module_authority(
    monkeypatch,
) -> None:
    name = next(iter(A.FORMAL_WORKLOADS))
    formal_ycsb = A.FORMAL_WORKLOADS[name]["ycsb"]
    module_ycsb = A.s8b_holdout_freeze.HOLDOUTS[name]["ycsb"]
    assert formal_ycsb == module_ycsb
    assert formal_ycsb is not module_ycsb
    key = A.s8b_holdout_freeze.SKEW_KEY
    original = module_ycsb[key]
    monkeypatch.setitem(formal_ycsb, key, original + "0")
    assert module_ycsb[key] == original


def test_t1333_each_formal_sink_rejects_a_wrong_scale() -> None:
    name = next(iter(A.FORMAL_WORKLOADS))
    valid = A.FORMAL_WORKLOADS[name]
    descriptor, descriptor_record = A._descriptor_for(valid)
    invalid = A.WorkloadEntry(copy.deepcopy(valid))
    invalid["records"] += 1
    with pytest.raises(A.AutonomousTrialError, match="formal workload campaign scale"):
        A._campaign_for(
            workload=name,
            entry=invalid,
            descriptor=descriptor,
            descriptor_record=descriptor_record,
            trial_id="wrong-formal-campaign-scale",
            generations=1,
            contract=_T530_CONTRACT,
            build_context=_no_build_context(),
        )
    with pytest.raises(A.AutonomousTrialError, match="formal workload perf scale"):
        A._perf_for(invalid)
    with pytest.raises(A.AutonomousTrialError, match="formal workload descriptor scale"):
        A._descriptor_for(invalid)


def test_t1349_formal_binding_rejects_module_projection_mismatch(
    monkeypatch,
) -> None:
    name = next(iter(A.FORMAL_WORKLOADS))
    descriptor, _record = A._descriptor_for(A.FORMAL_WORKLOADS[name])
    tampered = copy.deepcopy(A.s8b_holdout_freeze.HOLDOUTS)
    tampered[name]["candidate_id"] += "-tampered"
    monkeypatch.setattr(A.s8b_holdout_freeze, "HOLDOUTS", tampered)
    monkeypatch.setattr(
        A.s8c_arm_inputs,
        "_descriptor_for_candidate",
        lambda _candidate_id: (name, descriptor),
    )
    with pytest.raises(A.AutonomousTrialError, match="module bytes differ"):
        A._assert_formal_entry_binding(name, A.FORMAL_WORKLOADS[name])


def test_t1349_formal_binding_rejects_producer_projection_mismatch(
    monkeypatch,
) -> None:
    name = next(iter(A.FORMAL_WORKLOADS))
    original = A.FORMAL_WORKLOADS[name]
    descriptor, _record = A._descriptor_for(original)
    tampered = A.WorkloadEntry(copy.deepcopy(original))
    tampered["candidate_id"] += "-tampered"
    monkeypatch.setattr(
        A.s8c_arm_inputs,
        "_descriptor_for_candidate",
        lambda _candidate_id: (name, descriptor),
    )
    with pytest.raises(A.AutonomousTrialError, match="module bytes differ"):
        A._assert_formal_entry_binding(name, tampered)


def test_t1349_formal_source_rejects_legacy_projection_mismatch(
    monkeypatch,
) -> None:
    original_loader = A.s8b_ratified_freeze.load_legacy_freeze
    legacy = original_loader(A.ROOT)
    document = json.loads(json.dumps(legacy.document, default=dict))
    name = next(iter(A.FORMAL_WORKLOADS))
    document["holdouts"][name]["candidate_id"] += "-tampered"
    monkeypatch.setattr(
        A.s8b_ratified_freeze,
        "load_legacy_freeze",
        lambda _root: SimpleNamespace(document=document, sha256=legacy.sha256),
    )
    with pytest.raises(A.AutonomousTrialError, match="authority bytes differ"):
        A._formal_profile_source_record(repository_root=A.ROOT)


def test_t1349_formal_binding_rejects_arm_descriptor_mismatch(
    monkeypatch,
) -> None:
    name = next(iter(A.FORMAL_WORKLOADS))
    entry = A.FORMAL_WORKLOADS[name]
    descriptor, _record = A._descriptor_for(entry)
    mismatched = copy.deepcopy(descriptor)
    mismatched["read_write"]["read_ratio_percent"] += 1
    monkeypatch.setattr(
        A.s8c_arm_inputs,
        "_descriptor_for_candidate",
        lambda _candidate_id: (name, mismatched),
    )
    with pytest.raises(A.AutonomousTrialError, match="descriptor authority differs"):
        A._assert_formal_entry_binding(name, entry)


def test_t1310_producer_source_has_no_holdout_conjunction() -> None:
    source = Path(A.__file__).read_text(encoding="utf-8")
    hits = A.s8b_holdout_freeze.holdout_conjunction_hits(
        {Path(A.__file__).name: source}
    )
    assert set(hits) == set(A.s8b_holdout_freeze.HOLDOUTS)
    assert all(not paths for paths in hits.values())


def test_m12_scale_tokens_alone_do_not_create_a_holdout_conjunction() -> None:
    source = Path(A.__file__).read_text(encoding="utf-8")
    scale_only_mutation = source + "\nrecords = 1_000_000\nthreads = 48\n"
    hits = A.s8b_holdout_freeze.holdout_conjunction_hits(
        {Path(A.__file__).name: scale_only_mutation}
    )
    assert all(not paths for paths in hits.values())


def test_formal_selector_rederives_source_then_fails_closed_before_run_root(
    tmp_path,
) -> None:
    run_root = tmp_path / "must-not-exist"
    with pytest.raises(
        A.AutonomousTrialError,
        match=(
            r"^formal launch is not admissible: effective "
            r"preregistration unavailable$"
        ),
    ):
        A.run_trial(
            trial_id="formal-blocked",
            workloads=list(A.s8b_holdout_freeze.HOLDOUTS),
            generations=1,
            provider_kind="fixture",
            run_root=run_root,
            sub="/unused",
            do_build=False,
            workload_profile=A.FORMAL_LEGACY_WORKLOAD_PROFILE,
        )
    assert not run_root.exists()


def test_programmatic_workload_profile_is_a_plain_string_closed_set(tmp_path) -> None:
    for selector in ("not-a-profile", None, 1):
        with pytest.raises(A.AutonomousTrialError, match="unknown workload profile"):
            A.run_trial(
                trial_id="profile-closed-set",
                workloads=["ycsb-a"],
                generations=1,
                provider_kind="fixture",
                run_root=tmp_path / f"run-{selector}",
                sub="/unused",
                do_build=False,
                workload_profile=selector,
            )


def test_cli_default_workloads_stay_exploratory_after_formal_entries(
    tmp_path, monkeypatch,
) -> None:
    observed = {}

    def stop_at_admission(**kwargs):
        observed.update(kwargs)
        raise _CliGateReached

    monkeypatch.setattr(A, "_trial_launch_admission", stop_at_admission)
    with pytest.raises(_CliGateReached):
        A.main([
            "--trial-id", "default-workload-profile",
            "--provider", "fixture",
            "--no-build",
            "--allow-unregistered-exploratory",
            "--ccbench-dir", str(tmp_path / "ccbench"),
            "--run-root", str(tmp_path / "run"),
        ])
    assert observed["workloads"] == list(A.WORKLOADS)


def test_cli_formal_selector_fails_before_launch_admission(
    tmp_path, monkeypatch,
) -> None:
    def unexpected_admission(**_kwargs):
        pytest.fail("formal selector reached launch admission")

    monkeypatch.setattr(A, "_trial_launch_admission", unexpected_admission)
    with pytest.raises(
        A.AutonomousTrialError,
        match=(
            r"^formal launch is not admissible: effective "
            r"preregistration unavailable$"
        ),
    ):
        A.main([
            "--trial-id", "formal-cli-blocked",
            "--provider", "fixture",
            "--workload-profile", A.FORMAL_LEGACY_WORKLOAD_PROFILE,
            "--no-build",
            "--ccbench-dir", str(tmp_path / "ccbench"),
            "--run-root", str(tmp_path / "run"),
        ])


def test_cli_workload_profile_rejects_values_outside_closed_set(tmp_path) -> None:
    run_root = tmp_path / "must-not-exist"
    with pytest.raises(SystemExit):
        A.main([
            "--trial-id", "unknown-profile-cli",
            "--provider", "fixture",
            "--workload-profile", "not-a-profile",
            "--no-build",
            "--run-root", str(run_root),
        ])
    assert not run_root.exists()


def test_prepare_campaign_identity_uses_injected_contract_once(monkeypatch) -> None:
    calls = []

    def lookup(env_tag):
        calls.append(env_tag)
        return _T530_CONTRACT

    monkeypatch.setattr(A.trigger, "_lookup", lookup)
    site = A.trigger.site_policy.OTHER
    contract = A.trigger._admit_env_contract(site)
    prepared = A._prepare_campaign_identity(
        workload="ycsb-a", trial_id="fixture-completeness",
        generations=1, site=site, contract=contract,
        build_context=_no_build_context(),
    )
    assert calls == ["linux-baremetal"]
    assert "environment_contract_sha256" not in prepared.campaign.search_config
    assert prepared.campaign.bound_environment_contract is _T530_CONTRACT


def _pegasus_transport_fixture():
    source_env = {
        "PBS_JOBID": "12345.pegasus",
        "http_proxy": "http://proxy.example:18080",
        "https_proxy": "http://proxy.example:18443",
    }
    policy_bytes = json.dumps({
        "schema_version": "pegasus-claude-transport-policy/v1",
        "site": "PEGASUS_COMPUTE",
        "mode": "explicit-http-proxy-env",
        "endpoint_values": {
            "http_proxy": source_env["http_proxy"],
            "https_proxy": source_env["https_proxy"],
        },
    }).encode("utf-8")
    admission = claude_transport.evaluate_transport_admission(
        source_env=source_env,
        policy_bytes=policy_bytes,
        site=A.trigger.site_policy.PEGASUS_COMPUTE,
    )
    return admission, admission.receipt.as_dict()


def _assert_workload_campaign_uses_site_contract(
    tmp_path, monkeypatch, *, site, contract, other_site, other_contract,
    expected_env_tag, expected_campaign_id,
) -> None:
    site_calls = []
    lookup_calls = []
    observed = {}

    def current_site():
        site_calls.append(site)
        return site

    def lookup(env_tag):
        lookup_calls.append(env_tag)
        assert env_tag == expected_env_tag
        return contract

    monkeypatch.setattr(A.trigger, "_current_site", current_site)
    monkeypatch.setattr(A.trigger, "_lookup", lookup)
    prepare = A._prepare_campaign_identity

    def prepare_campaign_identity(
        *, workload, trial_id, generations, site, contract, build_context,
        arm_execution=None,
    ):
        prepared = prepare(
            workload=workload,
            trial_id=trial_id,
            generations=generations,
            site=site,
            contract=contract,
            build_context=build_context,
            arm_execution=arm_execution,
        )
        observed["site"] = site
        observed["contract"] = contract
        observed["cfg"] = prepared.campaign
        return prepared

    monkeypatch.setattr(A, "_prepare_campaign_identity", prepare_campaign_identity)
    factory = A.exploration_campaign_layout

    def campaign_layout(campaign_id):
        layout = factory(campaign_id, str(tmp_path))
        observed["layout"] = layout
        return layout

    monkeypatch.setattr(
        A,
        "exploration_campaign_layout",
        campaign_layout,
    )
    run_root = tmp_path / "run"
    for child in (run_root, run_root / "raw", run_root / "proposals"):
        child.mkdir(exist_ok=True)
    context = _no_build_context()

    def drive(
        cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
        cache_root="", proposal_path="", extra_sources=(), build_context=None,
        _resolved_site=None, _contract=None,
    ):
        observed.update({
            "cfg": cfg,
            "layout": layout,
            "site": _resolved_site,
            "contract": _contract,
        })
        Path(layout.root).mkdir(parents=True, exist_ok=True)
        return {
            "outcome": "dry-pass",
            "variant": None,
            "stop_reason": "continue",
            "iteration": 1,
            "ran": True,
            "critic_digest_generated": False,
            "trigger_gate_binding_commitment": "b" * 64,
        }

    transport_admission = None
    transport_receipt = None
    if site == A.trigger.site_policy.PEGASUS_COMPUTE:
        transport_admission, transport_receipt = _pegasus_transport_fixture()
    monkeypatch.setattr(A.trigger, "drive_iteration", drive)
    result = _run_workload_with_scope(
        workload="ycsb-a",
        generations=1,
        providers={
            role: _RecordingFixture(role)
            for role in ("planner", "coder", "auditor", "critic")
        },
        journal=A.AttemptJournal(run_root / "attempts.jsonl"),
        run_root=run_root,
        sub="/unused",
        do_build=True,
        cache_root="",
        trial_id="c01-site-contract",
        started_monotonic=time.monotonic(),
        max_wall_s=60,
        drive=A.trigger.drive_iteration,
        preview=_fake_preview,
        transport_admission=transport_admission,
        transport_receipt=transport_receipt,
        build_context=context,
    )
    other = prepare(
        workload="ycsb-a",
        trial_id="c01-site-contract",
        generations=1,
        site=other_site,
        contract=other_contract,
        build_context=context,
    )
    expected_root = (
        tmp_path / "exploration" / "campaigns" / expected_campaign_id
    )
    assert site_calls == [site]
    assert lookup_calls == [expected_env_tag]
    assert observed["site"] == site
    assert observed["contract"] is contract
    assert "environment_contract_sha256" not in observed["cfg"].search_config
    assert observed["cfg"].bound_environment_contract is contract
    if site == A.trigger.site_policy.PEGASUS_COMPUTE:
        assert observed["cfg"].search_config["measurement_env"] == "pegasus"
    else:
        assert "measurement_env" not in observed["cfg"].search_config
    assert result["campaign_id"] == expected_campaign_id
    assert result["campaign_id"] != other.campaign_id
    assert str(A.ident.campaign_id(observed["cfg"])) == expected_campaign_id
    assert Path(result["campaign_root"]) == expected_root
    assert Path(observed["layout"].root) == expected_root


def test_pegasus_workload_identity_layout_and_drive_use_pegasus_contract(
    tmp_path, monkeypatch,
) -> None:
    assert _C01_PEGASUS_CAMPAIGN_ID != _T816_C01_PEGASUS_CAMPAIGN_ID
    assert _C01_PEGASUS_CAMPAIGN_ID != _T2304_C01_PEGASUS_CAMPAIGN_ID
    _assert_workload_campaign_uses_site_contract(
        tmp_path,
        monkeypatch,
        site=A.trigger.site_policy.PEGASUS_COMPUTE,
        contract=_T530_PEGASUS_CONTRACT,
        other_site=A.trigger.site_policy.OTHER,
        other_contract=_T530_CONTRACT,
        expected_env_tag="pegasus",
        expected_campaign_id=_C01_PEGASUS_CAMPAIGN_ID,
    )


def test_other_workload_identity_layout_and_drive_use_linux_contract(
    tmp_path, monkeypatch,
) -> None:
    assert _C01_OTHER_CAMPAIGN_ID != _T816_C01_OTHER_CAMPAIGN_ID
    assert _C01_OTHER_CAMPAIGN_ID != _T2304_C01_OTHER_CAMPAIGN_ID
    _assert_workload_campaign_uses_site_contract(
        tmp_path,
        monkeypatch,
        site=A.trigger.site_policy.OTHER,
        contract=_T530_CONTRACT,
        other_site=A.trigger.site_policy.PEGASUS_COMPUTE,
        other_contract=_T530_PEGASUS_CONTRACT,
        expected_env_tag="linux-baremetal",
        expected_campaign_id=_C01_OTHER_CAMPAIGN_ID,
    )


def test_parse_coder_accepts_wire_and_rejects_implementation() -> None:
    accepted = A.parse_coder(json.dumps({
        "proposal": {
            "axis": A.trigger.MARKER_ID,
            "wire": "10100",
            "justification": "fixture",
            "confidence": "medium",
        }
    }))
    assert accepted.wire == "10100"
    for proposal in (
        {
            "axis": A.trigger.MARKER_ID,
            "implementation": "izanagi_gate_pass = true;",
            "justification": "fixture",
            "confidence": "medium",
        },
        {
            "axis": A.trigger.MARKER_ID,
            "wire": "10100",
            "implementation": "izanagi_gate_pass = true;",
            "justification": "fixture",
            "confidence": "medium",
        },
    ):
        with pytest.raises(A.AutonomousTrialError):
            A.parse_coder(json.dumps({"proposal": proposal}))


@pytest.mark.parametrize("bad_wire", [None, True, 0, "", "0000", "000000", "0000x"])
def test_parse_coder_rejects_invalid_wire_corpus(bad_wire) -> None:
    with pytest.raises(RefluxIRError, match="^invalid reflux IR$"):
        A.parse_coder(json.dumps({
            "proposal": {
                "axis": A.trigger.MARKER_ID,
                "wire": bad_wire,
                "justification": "fixture",
                "confidence": "medium",
            }
        }))


@pytest.mark.parametrize("raw", ["[]", '{"value":1,"value":2}'])
def test_parse_raw_object_classifies_json_shape_failures(raw) -> None:
    with pytest.raises(A.RoleResponseJsonShapeError):
        A._parse_raw_object(raw, role="planner")


def test_parse_raw_object_classifies_json_syntax_failure() -> None:
    with pytest.raises(A.RoleResponseJsonSyntaxError):
        A._parse_raw_object('{"proposal":', role="planner")


def test_fixture_provider_emits_only_wire() -> None:
    provider = A.FixtureRoleProvider("coder")
    for generation, expected in ((1, "11111"), (2, "10000")):
        response = provider.invoke(
            invocation_id=f"fixture-g{generation}",
            payload={"generation": generation},
        )
        proposal = json.loads(response.raw_response)["proposal"]
        assert proposal["wire"] == expected
        assert set(proposal) == {"axis", "wire", "justification", "confidence"}


def test_auditor_trial_projection_contains_only_closed_codes_and_counts() -> None:
    auditor = A.AuditorVerdict(
        verdict="reject",
        diff_digest="a" * 64,
        violations=[{
            "type": 16,
            "location": "wire=10100 mask=5",
            "correctness_impact": "candidate 10100",
            "verifier_blind_spot": "mask 5",
        }],
        nits=[{"finding": "wire 10100"}],
        proposed_tests=[{
            "mutation": "wire 10100",
            "expected_gate": "mask 5",
            "machine_judgment": "reject",
        }],
        uncertainty="wire 10100",
    )
    projected = A._jsonable_role_value("auditor", auditor)
    assert projected == {
        "verdict": "reject",
        "diff_digest": "a" * 64,
        "violation_codes": [16],
        "nit_count": 1,
        "proposed_test_count": 1,
        "uncertainty_present": True,
    }
    encoded = json.dumps(projected, sort_keys=True)
    assert "10100" not in encoded and "mask 5" not in encoded


def test_preview_uses_canonical_emitter(tmp_path, monkeypatch) -> None:
    template = """// EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating
#if BACKOFF_TRIGGER_GATING
  izanagi_gate_pass = true;
#else
  Backoff::backoff(FLAGS_clocks_per_us);
#endif
// EVOLVE-BLOCK-END silo-backoff-trigger-gating
"""
    source = tmp_path / A.trigger.SOURCE_REL
    source.parent.mkdir(parents=True)
    source.write_text(template, encoding="utf-8")
    monkeypatch.setattr(A, "assert_pinned_clean", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        A, "applied", lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    original = A.loop_core.quarantine
    seen = []

    def quarantine_spy(sub, predicate, **kwargs):
        seen.append(predicate)
        return original(sub, predicate, **kwargs)

    monkeypatch.setattr(A.loop_core, "quarantine", quarantine_spy)
    coder = A.trigger.CoderProposalTriggerGating(
        axis=A.trigger.MARKER_ID, wire="10100",
    )
    result = A._preview(coder, sub=str(tmp_path))
    assert result["passed"] is True
    assert seen == [emit_predicate(A.parse_wire("10100"))]


def test_generation_budget_boundary_at_ratified_launch() -> None:
    A._validate_generation_budget(1)
    A._validate_generation_budget(2)
    with pytest.raises(A.AutonomousTrialError, match="承認済み上限"):
        A._validate_generation_budget(3)


def test_generation_budget_rejects_bool() -> None:
    with pytest.raises(A.AutonomousTrialError):
        A._validate_generation_budget(True)


def test_generation_budget_rejects_int_subclass_with_overridden_add() -> None:
    class _ExpandingBudget(int):
        def __add__(self, other: object) -> int:
            return 4

    generations = _ExpandingBudget(1)
    assert int(generations) == 1
    assert list(range(1, generations + 1)) == [1, 2, 3]
    with pytest.raises(A.AutonomousTrialError, match="1..10 必須"):
        A._validate_generation_budget(generations)


def test_generation_budget_rejects_below_minimum() -> None:
    with pytest.raises(A.AutonomousTrialError):
        A._validate_generation_budget(0)


def test_generation_budget_rejects_non_int_float() -> None:
    with pytest.raises(A.AutonomousTrialError):
        A._validate_generation_budget(1.0)


def test_generation_budget_absolute_upper_bound_rejects_eleven(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        A, "MAX_APPROVED_GENERATIONS", A.MAX_GENERATIONS + 1,
    )
    with pytest.raises(A.AutonomousTrialError, match="1..10 必須"):
        A._validate_generation_budget(11)


def test_metric_projection_uses_ratio_keys_and_units() -> None:
    metrics = A._metric_projection({
        "fitness_tps": 12345,
        "records": {
            "bench_done": {
                "leading_indicators": {
                    "abort_rate": 0.079,
                    "latency_ns": 456.0,
                    "llc_miss_rate": 0.124,
                    "ipc": 2.5,
                }
            }
        },
    })

    assert set(metrics) == {
        "throughput_tps",
        "abort_rate",
        "latency_ns",
        "llc_miss_rate",
        "ipc",
    }
    assert metrics == {
        "throughput_tps": 12345.0,
        "abort_rate": 0.079,
        "latency_ns": 456.0,
        "llc_miss_rate": 0.124,
        "ipc": 2.5,
    }
    assert type(metrics["throughput_tps"]) is float


def test_metric_projection_rejects_only_invalid_numbers() -> None:
    def project(value):
        return A._metric_projection({
            "fitness_tps": value,
            "records": {
                "bench_done": {
                    "leading_indicators": {
                        "abort_rate": value,
                        "latency_ns": value,
                        "llc_miss_rate": value,
                        "ipc": value,
                    }
                }
            },
        })

    invalid = [
        None,
        True,
        False,
        float("nan"),
        float("inf"),
        -float("inf"),
        10**400,
    ]
    for value in invalid:
        assert all(metric is None for metric in project(value).values())
    assert all(metric is None for metric in project("0.5").values())
    for value in (0.0, -0.001, 1.5):
        assert set(project(value).values()) == {value}


def test_finite_metric_or_none_accepts_finite_boundaries() -> None:
    assert A._finite_metric_or_none(1.0) == 1.0
    assert A._finite_metric_or_none(sys.float_info.max) == sys.float_info.max


def test_role_metric_payloads_convert_only_percent_fields() -> None:
    perf_payload, leading_payload = A._role_metric_payloads(
        {
            "throughput_tps": 12345.0,
            "abort_rate": 0.079,
            "latency_ns": 456.0,
            "llc_miss_rate": 0.124,
            "ipc": 2.5,
        },
        contention_level="high",
    )

    assert set(perf_payload) == {
        "throughput_tps",
        "abort_rate_pct",
        "latency_ns",
        "llc_miss_rate",
        "ipc",
    }
    assert set(leading_payload) == {
        "contention_level",
        "cache_miss_rate_pct",
        "IPC_overall",
    }
    assert perf_payload["abort_rate_pct"] == 7.9
    assert leading_payload["cache_miss_rate_pct"] == 12.4
    assert perf_payload["llc_miss_rate"] == 0.124
    assert perf_payload["throughput_tps"] == 12345.0
    assert perf_payload["latency_ns"] == 456.0
    assert perf_payload["ipc"] == 2.5
    assert leading_payload["IPC_overall"] == 2.5


def test_role_metric_payloads_preserve_out_of_range_ratios() -> None:
    perf_payload, leading_payload = A._role_metric_payloads(
        {
            "throughput_tps": 12345.0,
            "abort_rate": 1.5,
            "latency_ns": 456.0,
            "llc_miss_rate": -0.001,
            "ipc": 2.5,
        },
        contention_level="high",
    )

    assert perf_payload["abort_rate_pct"] == 150.0
    assert perf_payload["abort_rate_pct"] is not None
    assert leading_payload["cache_miss_rate_pct"] == -0.1
    assert leading_payload["cache_miss_rate_pct"] is not None


def test_role_metric_payloads_reject_percent_overflow() -> None:
    perf_payload, leading_payload = A._role_metric_payloads(
        {
            "throughput_tps": sys.float_info.max,
            "abort_rate": sys.float_info.max,
            "latency_ns": sys.float_info.max,
            "llc_miss_rate": sys.float_info.max,
            "ipc": sys.float_info.max,
        },
        contention_level="high",
    )

    assert perf_payload["abort_rate_pct"] is None
    assert leading_payload["cache_miss_rate_pct"] is None
    assert perf_payload["llc_miss_rate"] == sys.float_info.max


def test_role_metric_payloads_preserve_unobserved_none() -> None:
    perf_payload, leading_payload = A._role_metric_payloads(
        {
            "throughput_tps": None,
            "abort_rate": None,
            "latency_ns": None,
            "llc_miss_rate": None,
            "ipc": None,
        },
        contention_level="medium",
    )

    assert all(value is None for value in perf_payload.values())
    assert leading_payload == {
        "contention_level": "medium",
        "cache_miss_rate_pct": None,
        "IPC_overall": None,
    }


def test_cli_default_is_literal_one_by_ast() -> None:
    tree = ast.parse(Path(A.__file__).read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        and any(
            isinstance(argument, ast.Constant)
            and argument.value == "--max-generations"
            for argument in node.args
        )
    ]
    assert len(calls) == 1
    defaults = [
        keyword.value
        for keyword in calls[0].keywords
        if keyword.arg == "default"
    ]
    assert len(defaults) == 1
    default = defaults[0]
    assert isinstance(default, ast.Constant)
    assert type(default.value) is int
    assert default.value == 1


class _ClosableRecordingFixture(_RecordingFixture):
    def __init__(self, role, close_order=None):
        super().__init__(role)
        self.close_calls = 0
        self.close_order = close_order

    def close(self):
        self.close_calls += 1
        if self.close_order is not None:
            self.close_order.append(self.role)


def test_fixture_trial_runs_ycsb_abc_and_binds_descriptor(tmp_path) -> None:
    run_root = tmp_path / "run"
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="fixture-abc",
        workloads=["ycsb-a", "ycsb-b", "ycsb-c"],
        generations=1,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "complete"
    assert report["schema_version"] == "p3-autonomous-workload-trial-report/v3"
    assert report["generation_driver"] == {
        "wrapper": "s8c-generation/v1",
        "delegate": "caller-injected-unsupported",
    }
    assert report["honest_accounting"] == {
        "role_query_count": 12,
        "bench_wall_seconds": 0.0,
    }
    assert report["stop_policy"]["performance_early_stop"] is False
    assert report["claim_scope"]["scientific_claim"] is False
    ratios = [
        cell["descriptor"]["read_write"]["read_ratio_percent"]
        for cell in report["cells"]
    ]
    assert ratios == [50, 95, 100]
    for cell in report["cells"]:
        generation = cell["generations"][0]
        assert generation["outcome"] == "dry-pass"
        assert "metrics" not in generation
        assert generation["harness"]["trigger_gate_binding_commitment"] == "b" * 64
        assert set(generation["roles"]) == {"planner", "coder", "auditor", "critic"}
        descriptor_sha = cell["descriptor_binding"]["output_sha256"]
        for event in generation["roles"].values():
            assert event["status"] == "valid"
            assert event["descriptor_sha256"] == descriptor_sha
            assert len(event["input_payload_sha256"]) == 64
            assert event["attempt"] == 1
            assert event["retry"] is False
    on_disk = json.loads((run_root / "report.json").read_text(encoding="utf-8"))
    assert on_disk == report
    report_json = json.dumps(report, sort_keys=True)
    assert '"trigger_gate_binding_commitment"' in report_json
    assert '"trigger_gate_binding"' not in report_json
    assert '"mask"' not in report_json
    assert '"wire"' not in report_json
    events = [
        json.loads(line)
        for line in (run_root / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert sum(event["event"] == "role-attempt" for event in events) == 12
    assert events[-1]["event"] == "run-finish"
    assert report["attempt_journal_sha256"] == hashlib.sha256(
        (run_root / "attempts.jsonl").read_bytes()
    ).hexdigest()
    assert (run_root / "namespace.json").read_bytes() == (
        b'{"namespace":"exploration"}\n'
    )
    for payload in providers["coder"].payloads:
        assert set(payload["planner_direction"]) == {"axis", "direction", "magnitude"}
        assert "justification" not in payload["planner_direction"]
    for proposal_path in sorted((run_root / "proposals").glob("*.json")):
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
        assert "wire" in proposal["coder"]
        assert "implementation" not in proposal["coder"]
    for planner_payload, coder_payload, critic_payload in zip(
        providers["planner"].payloads,
        providers["coder"].payloads,
        providers["critic"].payloads,
        strict=True,
    ):
        assert planner_payload["schema_version"] == "p3-autonomous-workload-trial/v4"
        assert coder_payload["schema_version"] == "p3-autonomous-workload-trial/v4"
        assert critic_payload["schema_version"] == "p3-autonomous-workload-trial/v4"
        critic_keys = json.dumps(critic_payload, sort_keys=True)
        assert "trigger_gate_binding" not in critic_keys
        assert '"mask"' not in critic_keys
        assert '"wire"' not in critic_keys
        assert critic_payload["critic_digest"] is None
        assert critic_payload["harness_result"]["candidate_label"] is None

        current_perf = planner_payload["current_perf"]
        leading_indicators = planner_payload["leading_indicators"]
        baseline = coder_payload["baseline"]
        critic_metrics = critic_payload["harness_result"]["metrics"]
        assert set(current_perf) == {
            "throughput_tps",
            "abort_rate_pct",
            "latency_ns",
            "llc_miss_rate",
            "ipc",
        }
        assert set(leading_indicators) == {
            "contention_level",
            "cache_miss_rate_pct",
            "IPC_overall",
        }
        assert set(baseline) == {
            "throughput_tps",
            "abort_rate_pct",
            "latency_ns",
            "llc_miss_rate",
            "ipc",
        }
        assert set(critic_metrics) == {
            "throughput_tps",
            "abort_rate",
            "latency_ns",
            "llc_miss_rate",
            "ipc",
        }
        assert "abort_rate_pct" not in critic_metrics
        assert "cache_miss_rate_pct" not in critic_metrics
        assert all(value is None for value in current_perf.values())
        assert all(
            leading_indicators[key] is None
            for key in ("cache_miss_rate_pct", "IPC_overall")
        )
        assert all(value is None for value in baseline.values())
        assert all(value is None for value in critic_metrics.values())


def test_fixture_no_build_cli_uses_public_drive_without_critic_digest(
    tmp_path, monkeypatch, ratified_enforcement_source,
) -> None:
    """P+1: documented 8c CLI reaches the real public drive on a fresh layout."""
    from orchestrator.campaign import patchharness

    ccbench = tmp_path / "ccbench"
    source = ccbench / A.trigger.SOURCE_REL
    source.parent.mkdir(parents=True)
    source.write_text(
        """// EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating
#if BACKOFF_TRIGGER_GATING
  izanagi_gate_pass = true;
#else
  Backoff::backoff(FLAGS_clocks_per_us);
#endif
// EVOLVE-BLOCK-END silo-backoff-trigger-gating
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(A, "assert_pinned_clean", lambda *_a, **_k: None)
    monkeypatch.setattr(
        A, "applied", lambda *_a, **_k: contextlib.nullcontext(),
    )
    monkeypatch.setattr(
        patchharness, "applied", lambda *_a, **_k: contextlib.nullcontext(),
    )
    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )

    run_root = tmp_path / "fresh-run"
    assert A.main([
        "--trial-id", "fixture-public-drive",
        "--provider", "fixture",
        "--workloads", "ycsb-a",
        "--max-generations", "1",
        "--no-build",
        "--allow-unregistered-exploratory",
        "--ccbench-dir", str(ccbench),
        "--run-root", str(run_root),
    ]) == 0

    report = json.loads((run_root / "report.json").read_text(encoding="utf-8"))
    generation = report["cells"][0]["generations"][0]
    assert generation["outcome"] == "dry-pass"
    assert generation["harness"]["critic_digest_generated"] is False
    assert generation["roles"]["critic"]["status"] == "valid"
    campaign_root = Path(report["cells"][0]["campaign_root"])
    assert (campaign_root / "reports" / A.trigger.PROVENANCE_BASENAME).exists()
    assert (campaign_root / "loop_state.json").exists()
    assert not (campaign_root / A.trigger.DIGEST_BASENAME).exists()


def test_generation_one_recipient_wiring_uses_role_projection(
    tmp_path, monkeypatch,
) -> None:
    expected_perf = {
        "throughput_tps": 12345.0,
        "abort_rate_pct": 7.9,
        "latency_ns": 456.0,
        "llc_miss_rate": 0.124,
        "ipc": 2.5,
    }
    expected_leading = {
        "contention_level": "fixture-contention",
        "cache_miss_rate_pct": 12.4,
        "IPC_overall": 2.5,
    }
    calls = []

    def role_projection(current_metrics, *, contention_level):
        calls.append((dict(current_metrics), contention_level))
        return dict(expected_perf), dict(expected_leading)

    monkeypatch.setattr(A, "_role_metric_payloads", role_projection)
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="generation-one-recipient-wiring",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    assert report["status"] == "complete"
    assert len(calls) == 1
    assert set(calls[0][0]) == {
        "throughput_tps",
        "abort_rate",
        "latency_ns",
        "llc_miss_rate",
        "ipc",
    }
    assert providers["planner"].payloads[0]["current_perf"] == expected_perf
    assert providers["planner"].payloads[0]["leading_indicators"] == expected_leading
    assert providers["coder"].payloads[0]["baseline"] == expected_perf


def test_generation_one_finite_metrics_preserve_recipient_units_and_report_schema(
    tmp_path,
) -> None:
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="generation-one-finite-metrics",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive_with_finite_metrics,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    assert report["status"] == "complete"
    cell = report["cells"][0]
    assert cell["admission_decision"] == {
        "admission_status": "not-applicable",
    }
    generation_record = cell["generations"][0]
    assert generation_record["outcome"] == "certified"

    planner_payload = providers["planner"].payloads[0]
    coder_payload = providers["coder"].payloads[0]
    auditor_payload = providers["auditor"].payloads[0]
    critic_payload = providers["critic"].payloads[0]
    common_keys = {
        "schema_version",
        "pilot_scope",
        "scientific_claim",
        "workload",
        "generation",
        "workload_descriptor",
        "descriptor_binding",
        "attempt_policy",
        "stop_policy",
    }
    assert set(planner_payload) == common_keys | {
        "current_perf",
        "leading_indicators",
        "whiteboard",
    }
    assert set(coder_payload) == common_keys | {
        "leakproof_context",
        "gating_spec",
        "planner_direction",
        "baseline",
        "whiteboard",
    }
    assert set(auditor_payload) == common_keys | {
        "working_diff",
        "diff_digest",
        "designated_source_context",
        "correctness_digest",
    }
    assert set(critic_payload) == common_keys | {
        "harness_result",
        "critic_digest",
    }
    assert set(critic_payload["harness_result"]) == {
        "outcome",
        "candidate_label",
        "verdict",
        "metrics",
        "stop_reason",
    }
    assert critic_payload["harness_result"]["candidate_label"] is None
    assert critic_payload["critic_digest"] is None

    critic_metrics = critic_payload["harness_result"]["metrics"]
    assert critic_metrics == {
        "throughput_tps": 12345.0,
        "abort_rate": 0.079,
        "latency_ns": 456.0,
        "llc_miss_rate": 0.124,
        "ipc": 2.5,
    }

    planner_indicators = planner_payload["leading_indicators"]
    assert (
        planner_indicators["contention_level"]
        == cell["descriptor"]["contention"]["label"]
    )
    assert "metrics" not in generation_record


def test_auditor_declassification_annotation_is_exact_and_pins_sunset(
    tmp_path,
) -> None:
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="auditor-declassification-account",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "invoked",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    policy = {
        "source_class": "candidate-wire",
        "current_precondition": "raw-ir-equals-effective-ir/v1",
        "sunset_trigger": "reflux-control-separates-raw-and-effective-ir/v1",
        "successor": {
            "working_diff_source": (
                "independent-canonical-emitter-from-raw-ir/v1"
            ),
            "allowed_json_pointers": ["/working_diff"],
            "forbidden_json_pointers": ["/diff_digest"],
        },
    }
    assert A.AUDITOR_DIFF_DECLASSIFICATION_POLICY == policy
    auditor_payload = providers["auditor"].payloads[0]
    expected = [{
        "policy_id": "t244-auditor-diff-declassification/v1",
        "policy_sha256": hashlib.sha256(
            A._canonical_json_bytes(policy)
        ).hexdigest(),
        "disclosures": [
            {
                "json_pointer": "/working_diff",
                "transform": "identity",
                "value_sha256": hashlib.sha256(
                    A._canonical_json_bytes(auditor_payload["working_diff"])
                ).hexdigest(),
            },
            {
                "json_pointer": "/diff_digest",
                "transform": "sha256-hex-of-/working_diff",
                "value_sha256": hashlib.sha256(
                    A._canonical_json_bytes(auditor_payload["diff_digest"])
                ).hexdigest(),
            },
        ],
    }]
    events = report["cells"][0]["generations"][0]["roles"]
    assert events["auditor"]["declassifications"] == expected
    assert all(
        events[role]["declassifications"] == []
        for role in ("planner", "coder", "critic")
    )
    journal_events = [
        json.loads(line)
        for line in (tmp_path / "invoked" / "attempts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if json.loads(line).get("event") == "role-attempt"
    ]
    journal_auditor = next(
        event for event in journal_events if event["role"] == "auditor"
    )
    assert journal_auditor["declassifications"] == expected

    def reject_before_audit(coder, *, sub):
        preview_result = _fake_preview(coder, sub=sub)
        preview_result["passed"] = False
        preview_result["reason"] = "fixture pre-audit rejection"
        return preview_result

    skipped_providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    skipped = A.run_trial(
        trial_id="auditor-declassification-skip",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "skipped",
        sub="/unused",
        do_build=False,
        providers=skipped_providers,
        drive=_fake_drive,
        preview=reject_before_audit,
        allow_unregistered_exploratory=True,
    )
    skipped_event = skipped["cells"][0]["generations"][0]["roles"]["auditor"]
    assert skipped_event["status"] == "skipped"
    assert skipped_event["declassifications"] == []
    assert skipped_providers["auditor"].payload_bytes == []


_AUDITOR_D_POINTERS = frozenset({
    "/working_diff",
    "/diff_digest",
})
_CRITIC_D_SELECTORS = frozenset({
    "/harness_result/outcome",
    "/harness_result/verdict",
    "/harness_result/metrics",
    "/harness_result/stop_reason",
    "critic_digest:rejection-class",
    "critic_digest:rejection-count",
})


def _canonical_without_json_pointers(
    payload_bytes: bytes, pointers: frozenset[str],
) -> bytes:
    value = json.loads(payload_bytes)
    for pointer in sorted(pointers):
        parent = value
        parts = pointer.removeprefix("/").split("/")
        for part in parts[:-1]:
            parent = parent[part]
        del parent[parts[-1]]
    return A._canonical_json_bytes(value)


def _critic_bytes_without_declared_d(payload_bytes: bytes) -> bytes:
    """宣言 selector が指す field だけを declassify して canonicalize する。"""
    value = json.loads(payload_bytes)
    digest = value["critic_digest"]
    assert isinstance(digest, str)
    structure: dict[str, Any] = {
        "outside_rejection_sections": [],
        "rejection_count": 0,
        "rejections": [],
    }
    current = None
    for line in digest.splitlines():
        if (
            line.startswith("## [")
            and "] candidate_label=" in line
        ):
            classification, identity = line.split("] candidate_label=", 1)
            current = {
                "class": classification.removeprefix("## ["),
                "identity_and_context": identity,
                "body": [],
            }
            structure["rejections"].append(current)
        else:
            target = (
                structure["outside_rejection_sections"]
                if current is None
                else current["body"]
            )
            target.append(line)
    structure["rejection_count"] = len(structure["rejections"])

    for selector in sorted(_CRITIC_D_SELECTORS):
        if selector.startswith("/harness_result/"):
            del value["harness_result"][selector.rsplit("/", 1)[1]]
        elif selector == "critic_digest:rejection-class":
            for rejection in structure["rejections"]:
                rejection.pop("class")
        elif selector == "critic_digest:rejection-count":
            structure.pop("rejection_count")
        else:  # selector を足すだけで暗黙に行を消せないよう fail-closed にする。
            raise AssertionError(f"未実装の critic D selector: {selector}")
    value["critic_digest"] = structure
    return A._canonical_json_bytes(value)


def _critic_relation_equivalent(payloads: list[bytes]) -> bool:
    return len({_critic_bytes_without_declared_d(raw) for raw in payloads}) == 1


def test_critic_relation_oracle_detects_candidate_derived_evidence_leak() -> None:
    """候補由来 evidence は D の外なので、比較を同値にしてはならない。"""
    assert _CRITIC_D_SELECTORS == frozenset({
        "/harness_result/outcome",
        "/harness_result/verdict",
        "/harness_result/metrics",
        "/harness_result/stop_reason",
        "critic_digest:rejection-class",
        "critic_digest:rejection-count",
    })
    payloads = []
    for raw_variant in ("diffq-candidate-a", "diffq-candidate-b"):
        digest = A.loop_core.render_rejections(
            [],
            [],
            diff_rejections=[DiffQuarantineRejection(
                genome="g",
                flags={},
                subtype="fixture",
                reason="fixture rejection",
                diff_region="r",
                template_diff_id="m",
                evidence=f"raw_variant={raw_variant}",
            )],
            identity_projection=A.loop_core.IdentityProjection.RAW,
        )
        value = {
            "harness_result": {
                "outcome": "rejected",
                "candidate_label": "candidate-0001",
                "verdict": "auditor-pass",
                "metrics": {},
                "stop_reason": "continue",
            },
            "critic_digest": digest,
        }
        payloads.append(A._canonical_json_bytes(value))
    assert not _critic_relation_equivalent(payloads)


def _assert_role_sink_report_complete(report, wire):
    assert report["status"] == "complete", (
        f"wire={wire}: expected complete, got status={report['status']}"
    )
    return report["cells"][0]


def test_role_sink_bytes_vary_only_at_declared_declassifications(tmp_path) -> None:
    """32 wire の実 trial で wire と role sink bytes の関係を検査する。

    親裁定により逐次スケジュールは被覆対象に含めない。
    損失として、逐次時だけ wire を混ぜる欠陥は決定的には捕まらなくなる。
    """
    # P は S の決定前に固定される descriptor/workload/generation/policy、
    # planner 入出力、coder 入力、baseline metrics、empty whiteboard だけである。
    # outcome/metrics/stop/rejection 観測は P に含めず、上の D selector で除外する。
    sink_bytes = {role: [] for role in ("planner", "coder", "auditor", "critic")}
    trusted_variants = []
    secret_records = []
    recorded_binding = _binding_from_recorded_head()

    def run_wire(value):
        wire = f"{value:05b}"
        providers = {
            role: _WireRecordingFixture(role, wire=wire)
            for role in ("planner", "coder", "auditor", "critic")
        }

        def preview(coder, *, sub):
            predicate = emit_predicate(A.parse_wire(coder.wire))
            working_diff = "fixture-working-diff\n" + predicate
            return {
                "passed": True,
                "working_diff": working_diff,
                "diff_digest": hashlib.sha256(
                    working_diff.encode("utf-8")
                ).hexdigest(),
                "subtype": None,
                "reason": "",
                "forbidden_identifiers": [],
            }

        def drive(
            cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
            cache_root="", proposal_path="", extra_sources=(),
        ):
            assert do_build is False, wire
            variant = _write_admitted_rejection_digest(
                cfg, layout, coder, binding=recorded_binding,
            )
            return {
                "outcome": "rejected",
                "variant": variant,
                "verdict": "auditor-pass",
                "stop_reason": "continue",
                "iteration": 1,
                "ran": True,
                "trigger_gate_binding_commitment": hashlib.sha256(
                    ("fixture-binding:" + coder.wire).encode("utf-8")
                ).hexdigest(),
                "critic_digest_generated": True,
            }

        report = A.run_trial(
            trial_id="role-sink-relation",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="fixture",
            run_root=tmp_path / f"wire-{wire}",
            sub="/unused",
            do_build=False,
            providers=providers,
            drive=drive,
            preview=preview,
            allow_unregistered_exploratory=True,
        )
        cell = _assert_role_sink_report_complete(report, wire)
        role_payloads = {}
        for role in ("planner", "coder", "auditor", "critic"):
            assert len(providers[role].payload_bytes) == 1, (wire, role)
            role_payloads[role] = providers[role].payload_bytes[0]

        generation = cell["generations"][0]
        raw_variant = generation["harness"]["variant"]
        predicate = emit_predicate(A.parse_wire(wire))
        working_diff = "fixture-working-diff\n" + predicate
        expected_variant = A.loop_core.diffq_variant_id(
            _RELATION_GENOME, predicate,
        )
        assert raw_variant == expected_variant, wire
        assert raw_variant != providers["critic"].payloads[0][
            "harness_result"
        ]["candidate_label"], wire
        campaign_layout = A.CampaignLayout(cell["campaign_root"])
        build_starts = [
            record
            for record in wal.read_records(campaign_layout)
            if record.stage == campaign_model.STAGE_BUILD_START
        ]
        assert len(build_starts) == 1, wire
        raw_build_attempt_id = build_starts[0].payload["build_attempt_id"]
        assert raw_build_attempt_id.encode("ascii") not in (
            providers["critic"].payload_bytes[0]
        ), wire
        return wire, role_payloads, raw_variant, {
            "wire": wire,
            "canonical_predicate": predicate,
            "working_diff": working_diff,
            "diff_digest": hashlib.sha256(
                working_diff.encode("utf-8")
            ).hexdigest(),
            "src_token": hashlib.sha256(
                predicate.encode("utf-8")
            ).hexdigest(),
            "variant": raw_variant,
            "build_attempt_id": raw_build_attempt_id,
            "trigger_gate_binding_commitment": generation["harness"][
                "trigger_gate_binding_commitment"
            ],
        }

    with ThreadPoolExecutor(
        max_workers=_ROLE_SINK_TRIAL_MAX_WORKERS,
    ) as executor:
        for value, result in enumerate(executor.map(run_wire, range(32))):
            wire, role_payloads, raw_variant, secret_record = result
            assert wire == f"{value:05b}"
            for role in sink_bytes:
                sink_bytes[role].append(role_payloads[role])
            trusted_variants.append(raw_variant)
            secret_records.append(secret_record)

    assert len(sink_bytes["planner"]) == 32
    assert len(sink_bytes["coder"]) == 32
    assert len(sink_bytes["auditor"]) == 32
    assert len(sink_bytes["critic"]) == 32
    assert len(trusted_variants) == 32
    assert len(secret_records) == 32
    assert len(set(sink_bytes["planner"])) == 1
    assert len(set(sink_bytes["coder"])) == 1
    assert len(set(sink_bytes["auditor"])) == 32
    assert len({
        _canonical_without_json_pointers(raw, _AUDITOR_D_POINTERS)
        for raw in sink_bytes["auditor"]
    }) == 1
    assert _critic_relation_equivalent(sink_bytes["critic"])
    assert len(set(trusted_variants)) == 32
    for secret_field in (
        "wire",
        "canonical_predicate",
        "working_diff",
        "diff_digest",
        "src_token",
        "variant",
        "build_attempt_id",
        "trigger_gate_binding_commitment",
    ):
        assert len({record[secret_field] for record in secret_records}) == 32


def test_role_sink_report_complete_rejects_partial_reports(tmp_path) -> None:
    """この負例が守るのは helper の述語本体であり、role-sink test 側の呼出し接続そのものではない（D387 の射程）。
    実 producer の report は _fake_drive 経由であり、role-sink test の drive 経路そのものではない。
    partial の2形（fatal_error あり／なし）を覆うが、status ではなく stop_reason を見る形への helper の弱化は検出できない。
    """
    wire = "00000"
    providers = {
        role: A.FixtureRoleProvider(role)
        for role in ("planner", "coder", "auditor")
    }
    report = A.run_trial(
        trial_id="role-sink-missing-critic",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "missing-critic",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "partial"
    assert "fatal_error" in report
    assert report["fatal_error"]["type"] == "KeyError"
    assert len(report["cells"]) == 1
    assert report["cells"][0]["stop_reason"] == "supervisor-error"
    with pytest.raises(
        AssertionError, match=f"wire={wire}: expected complete, got status=partial",
    ):
        _assert_role_sink_report_complete(report, wire)

    providers = {
        role: A.FixtureRoleProvider(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    providers["planner"] = _InvalidPlanner()
    report = A.run_trial(
        trial_id="role-sink-invalid-planner",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "invalid-planner",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "partial"
    assert "fatal_error" not in report
    assert len(report["cells"]) == 1
    assert report["cells"][0]["stop_reason"] == "role-invalid"
    with pytest.raises(
        AssertionError, match=f"wire={wire}: expected complete, got status=partial",
    ):
        _assert_role_sink_report_complete(report, wire)


class _InvalidPlanner:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, *, invocation_id, payload):
        self.calls += 1
        return A.ProviderResponse(
            raw_response='{"proposal":{},"extra":true}',
            provenance={"child_id": invocation_id},
        )


class _InvalidProvenancePlanner(A.FixtureRoleProvider):
    def __init__(self) -> None:
        super().__init__("planner")

    def invoke(self, *, invocation_id, payload):
        response = super().invoke(invocation_id=invocation_id, payload=payload)
        return dataclasses.replace(
            response,
            provenance={**response.provenance, "transport_receipt": {}},
        )


class _UnknownKeyPlanner:
    def __init__(self, unknown_key: str) -> None:
        self.unknown_key = unknown_key

    def invoke(self, *, invocation_id, payload):
        return A.ProviderResponse(
            raw_response=json.dumps({
                "proposal": {},
                self.unknown_key: True,
            }),
            provenance={"child_id": invocation_id},
        )


def test_unknown_response_key_is_not_reflected_to_journal_or_trial_report(
    tmp_path,
) -> None:
    raw_key = "wire=10100 mask=5"
    providers = {
        role: A.FixtureRoleProvider(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    providers["planner"] = _UnknownKeyPlanner(raw_key)
    run_root = tmp_path / "run"
    report = A.run_trial(
        trial_id="unknown-key-redaction",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    journal_text = (run_root / "attempts.jsonl").read_text(encoding="utf-8")
    report_text = (run_root / "report.json").read_text(encoding="utf-8")
    assert raw_key not in journal_text
    assert raw_key not in report_text
    assert raw_key not in json.dumps(report, ensure_ascii=False, sort_keys=True)
    assert "response object keys 不一致" in journal_text
    assert "response object keys 不一致" in report_text


def test_invalid_role_is_single_attempt_and_stops_cell(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(A, "MAX_APPROVED_GENERATIONS", 3)
    providers = {
        role: A.FixtureRoleProvider(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    planner = _InvalidPlanner()
    providers["planner"] = planner
    report = A.run_trial(
        trial_id="invalid-planner",
        workloads=["ycsb-a"],
        generations=3,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "partial"
    cell = report["cells"][0]
    assert cell["stop_reason"] == "role-invalid"
    assert len(cell["generations"]) == 1
    event = cell["generations"][0]["roles"]["planner"]
    assert event["attempt"] == 1
    assert event["retry"] is False
    assert event["status"] == "invalid"
    assert event["role_query_ordinal"] == 1
    error_artifacts = event["error_artifacts"]
    assert error_artifacts["failure_phase"] == "role-schema"
    assert error_artifacts["child_id"] == event["invocation_id"]
    raw_path = Path(error_artifacts["raw_response_path"])
    assert raw_path.is_file()
    assert error_artifacts["raw_response_sha256"] == hashlib.sha256(
        raw_path.read_bytes()
    ).hexdigest()
    assert report["honest_accounting"] == {
        "role_query_count": 1,
        "bench_wall_seconds": 0.0,
    }
    assert planner.calls == 1


def test_unexpected_parser_exception_has_distinct_failure_phase(
    tmp_path, monkeypatch,
) -> None:
    def raise_recursion(_raw):
        raise RecursionError("fixture parser recursion")

    monkeypatch.setitem(A.PARSERS, "planner", raise_recursion)
    providers = {
        role: A.FixtureRoleProvider(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="unexpected-parser-error",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    event = report["cells"][0]["generations"][0]["roles"]["planner"]
    assert event["status"] == "invalid"
    assert event["error_type"] == "RecursionError"
    assert event["error_artifacts"]["failure_phase"] == "parser-error"
    assert Path(event["error_artifacts"]["raw_response_path"]).is_file()


def test_pre_raw_failure_records_session_id_without_raw_pointer(tmp_path) -> None:
    providers = {
        role: A.FixtureRoleProvider(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    providers["planner"] = _InvalidProvenancePlanner()
    report = A.run_trial(
        trial_id="invalid-provenance",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    event = report["cells"][0]["generations"][0]["roles"]["planner"]
    assert event["status"] == "invalid"
    error_artifacts = event["error_artifacts"]
    assert error_artifacts == {
        "failure_phase": "pre-raw-write",
        "child_id": f"fixture-{event['invocation_id']}",
    }


def test_raw_write_failure_omits_incomplete_raw_pointer(
    tmp_path, monkeypatch,
) -> None:
    def fail_after_path_binding(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        raise PredictionRunnerError("fixture raw write failure")

    monkeypatch.setattr(A, "_write_bytes_bound", fail_after_path_binding)
    providers = {
        role: A.FixtureRoleProvider(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    run_root = tmp_path / "run"
    with pytest.raises(
        completeness.AutonomousTrialCompletenessError,
        match=r"failure_phase contradicts an existing raw response$",
    ):
        A.run_trial(
            trial_id="raw-write-failure",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="fixture",
            run_root=run_root,
            sub="/unused",
            do_build=False,
            providers=providers,
            drive=_fake_drive,
            preview=_fake_preview,
            allow_unregistered_exploratory=True,
        )
    events = [
        json.loads(line)
        for line in (run_root / "attempts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    event = next(item for item in events if item["event"] == "role-attempt")
    assert event["status"] == "invalid"
    assert event["error_artifacts"] == {
        "failure_phase": "raw-write",
        "child_id": f"fixture-{event['invocation_id']}",
    }
    assert not (run_root / "report.json").exists()


class _MalformedAuditorBase(A.FixtureRoleProvider):
    def __init__(self) -> None:
        super().__init__("auditor")
        self.calls = 0
        self.last_payload: dict[str, Any] = {}
        self.last_raw_response = ""

    def invoke(self, *, invocation_id, payload):
        self.calls += 1
        self.last_payload = dict(payload)
        response = super().invoke(
            invocation_id=invocation_id,
            payload=payload,
        )
        raw_response = self.malformed_raw(
            response.raw_response,
            payload,
        )
        self.last_raw_response = raw_response
        return dataclasses.replace(
            response,
            raw_response=raw_response,
        )


class _AuditorDescriptorBindingExtraKey(_MalformedAuditorBase):
    def malformed_raw(self, raw_response, payload):
        value = json.loads(raw_response)
        value["descriptor_binding"] = payload["descriptor_binding"]
        return A._canonical_json_bytes(value).decode("utf-8")


class _AuditorJsonFence(_MalformedAuditorBase):
    def malformed_raw(self, raw_response, payload):
        return f"```json\n{raw_response}\n```"


class _AuditorMissingDelimiter(_MalformedAuditorBase):
    def malformed_raw(self, raw_response, payload):
        malformed = raw_response.replace(
            ',"nits":',
            '"nits":',
            1,
        )
        assert malformed != raw_response
        return malformed


class _AuditorTopLevelArray(_MalformedAuditorBase):
    def malformed_raw(self, raw_response, payload):
        return '["auditor-top-level-array-sentinel"]'


def _assert_malformed_auditor_common(report, run_root, provider):
    assert report["status"] == "partial"
    cell = report["cells"][0]
    assert cell["stop_reason"] == "role-invalid"
    assert len(cell["generations"]) == 1
    generation = cell["generations"][0]
    assert generation["outcome"] == "auditor-invalid"
    event = generation["roles"]["auditor"]
    assert event["status"] == "invalid"
    assert event["attempt"] == 1
    assert event["retry"] is False
    assert event["role_query_ordinal"] == 3
    assert report["honest_accounting"] == {
        "role_query_count": 3,
        "bench_wall_seconds": 0.0,
    }
    assert provider.calls == 1
    journal_text = (run_root / "attempts.jsonl").read_text(encoding="utf-8")
    report_text = (run_root / "report.json").read_text(encoding="utf-8")
    assert provider.last_raw_response not in journal_text
    assert provider.last_raw_response not in report_text
    assert provider.last_raw_response not in json.dumps(
        report,
        ensure_ascii=False,
        sort_keys=True,
    )
    error_artifacts = event["error_artifacts"]
    assert error_artifacts["child_id"] == f"fixture-{event['invocation_id']}"
    raw_path = Path(error_artifacts["raw_response_path"])
    assert raw_path.read_text(encoding="utf-8") == provider.last_raw_response
    assert error_artifacts["raw_response_sha256"] == hashlib.sha256(
        raw_path.read_bytes()
    ).hexdigest()
    assert "provenance" not in error_artifacts
    return event


def test_auditor_descriptor_binding_extra_key_is_single_attempt_and_stops_cell(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(A, "MAX_APPROVED_GENERATIONS", 3)
    auditor = _AuditorDescriptorBindingExtraKey()
    providers = {
        role: A.FixtureRoleProvider(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    providers["auditor"] = auditor
    run_root = tmp_path / "run"
    report = A.run_trial(
        trial_id="auditor-extra-descriptor-binding",
        workloads=["ycsb-a"],
        generations=3,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    event = _assert_malformed_auditor_common(report, run_root, auditor)
    malformed = json.loads(auditor.last_raw_response)
    assert len(malformed) == 7
    assert "descriptor_binding" in malformed
    assert malformed["descriptor_binding"] == auditor.last_payload[
        "descriptor_binding"
    ]
    assert "response object keys 不一致" in event["error"]
    assert event["error_type"] == "AutonomousTrialError"
    assert event["error_artifacts"]["failure_phase"] == "role-schema"


def test_auditor_json_fence_is_single_attempt_and_stops_cell(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(A, "MAX_APPROVED_GENERATIONS", 3)
    auditor = _AuditorJsonFence()
    providers = {
        role: A.FixtureRoleProvider(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    providers["auditor"] = auditor
    run_root = tmp_path / "run"
    report = A.run_trial(
        trial_id="auditor-json-fence",
        workloads=["ycsb-a"],
        generations=3,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    event = _assert_malformed_auditor_common(report, run_root, auditor)
    assert auditor.last_raw_response.startswith("```json\n")
    assert auditor.last_raw_response.endswith("\n```")
    assert "JSON object を読めない" in event["error"]
    assert event["error_type"] == "RoleResponseJsonSyntaxError"
    assert event["error_artifacts"]["failure_phase"] == "json-syntax"


def test_auditor_missing_json_delimiter_is_single_attempt_and_stops_cell(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(A, "MAX_APPROVED_GENERATIONS", 3)
    auditor = _AuditorMissingDelimiter()
    providers = {
        role: A.FixtureRoleProvider(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    providers["auditor"] = auditor
    run_root = tmp_path / "run"
    report = A.run_trial(
        trial_id="auditor-missing-delimiter",
        workloads=["ycsb-a"],
        generations=3,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    event = _assert_malformed_auditor_common(report, run_root, auditor)
    assert ',"nits":' not in auditor.last_raw_response
    assert '"nits":' in auditor.last_raw_response
    assert "JSON object を読めない" in event["error"]
    assert event["error_type"] == "RoleResponseJsonSyntaxError"
    assert event["error_artifacts"]["failure_phase"] == "json-syntax"


def test_auditor_top_level_array_is_classified_as_json_shape(
    tmp_path,
) -> None:
    auditor = _AuditorTopLevelArray()
    providers = {
        role: A.FixtureRoleProvider(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    providers["auditor"] = auditor
    run_root = tmp_path / "run"
    report = A.run_trial(
        trial_id="auditor-top-level-array",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    event = _assert_malformed_auditor_common(report, run_root, auditor)
    assert event["error_type"] == "RoleResponseJsonShapeError"
    assert event["error_artifacts"]["failure_phase"] == "json-shape"


def test_run_trial_rejects_unapproved_budget_before_artifact_creation(tmp_path) -> None:
    run_root = tmp_path / "run"
    with pytest.raises(A.AutonomousTrialError, match="承認済み上限"):
        A.run_trial(
            trial_id="unapproved-programmatic-budget",
            workloads=["ycsb-a"],
            generations=3,
            provider_kind="fixture",
            run_root=run_root,
            sub="/unused",
            do_build=False,
        )
    assert not run_root.exists()


@pytest.mark.parametrize(
    "mismatch",
    ("job-id", "boot-id", "remaining-time"),
)
def test_run_trial_reservation_rejects_each_live_binding_mismatch_before_launch(
    tmp_path,
    monkeypatch,
    valid_reservation_environment,
    mismatch,
) -> None:
    monkeypatch.setattr(
        A.trigger,
        "_current_site",
        lambda: A.trigger.site_policy.PEGASUS_COMPUTE,
    )
    environment = dict(valid_reservation_environment)
    if mismatch == "job-id":
        environment["PBS_JOBID"] = "different.pegasus"
    elif mismatch == "boot-id":
        environment["IZANAGI_RESERVATION_BOOT_ID"] = "different-boot"
    else:
        requested_s = int(environment["IZANAGI_RESERVATION_REQUESTED_S"])
        scheduler_started = time.time() - requested_s + 1
        environment["IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH"] = str(
            scheduler_started
        )
        environment["IZANAGI_RESERVATION_DEADLINE_EPOCH"] = str(
            scheduler_started + requested_s
        )
    for key, value in environment.items():
        monkeypatch.setenv(key, value)

    launches: list[str] = []

    def blocked_provider(**_kwargs):
        launches.append("provider")
        raise AssertionError("provider launch must remain after reservation gate")

    def blocked_campaign(*_args, **_kwargs):
        launches.append("campaign")
        raise AssertionError("campaign launch must remain after reservation gate")

    monkeypatch.setattr(A, "_provider_set", blocked_provider)
    monkeypatch.setattr(A.trigger, "drive_iteration", blocked_campaign)
    run_root = tmp_path / f"reservation-{mismatch}"
    with pytest.raises(A.reservation.ReservationError):
        A.run_trial(
            trial_id=f"reservation-{mismatch}",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="claude-headless",
            run_root=run_root,
            sub="/unused",
            do_build=False,
            allow_pegasus_compute_transport=True,
            allow_unregistered_exploratory=True,
        )
    assert launches == []
    assert not run_root.exists()


def test_run_trial_reservation_rejects_when_remaining_time_is_less_than_max_wall(
    tmp_path,
    monkeypatch,
    valid_reservation_environment,
) -> None:
    monkeypatch.setattr(
        A.trigger,
        "_current_site",
        lambda: A.trigger.site_policy.PEGASUS_COMPUTE,
    )
    environment = dict(valid_reservation_environment)
    now = time.time()
    requested_s = 1860
    scheduler_started = now - 60
    environment["IZANAGI_RESERVATION_REQUESTED_S"] = str(requested_s)
    environment["IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH"] = str(
        scheduler_started
    )
    environment["IZANAGI_RESERVATION_DEADLINE_EPOCH"] = str(
        scheduler_started + requested_s
    )
    for key, value in environment.items():
        monkeypatch.setenv(key, value)

    launches: list[str] = []

    def blocked_provider(**_kwargs):
        launches.append("provider")
        raise AssertionError("provider launch must remain after reservation gate")

    def blocked_campaign(*_args, **_kwargs):
        launches.append("campaign")
        raise AssertionError("campaign launch must remain after reservation gate")

    monkeypatch.setattr(A, "_provider_set", blocked_provider)
    monkeypatch.setattr(A.trigger, "drive_iteration", blocked_campaign)
    run_root = tmp_path / "reservation-max-wall"
    with pytest.raises(A.reservation.ReservationError):
        A.run_trial(
            trial_id="reservation-max-wall",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="claude-headless",
            run_root=run_root,
            sub="/unused",
            do_build=False,
            max_wall_s=3600,
            allow_pegasus_compute_transport=True,
            allow_unregistered_exploratory=True,
        )
    assert launches == []
    assert not run_root.exists()


def test_reservation_error_stays_outside_run_trial_crash_terminalizer(
    tmp_path,
    monkeypatch,
    valid_reservation_environment,
) -> None:
    monkeypatch.setattr(
        A.trigger,
        "_current_site",
        lambda: A.trigger.site_policy.PEGASUS_COMPUTE,
    )
    for key, value in valid_reservation_environment.items():
        monkeypatch.setenv(key, value)

    def fail_check(*_args, **_kwargs):
        raise A.reservation.ReservationError("synthetic reservation rejection")

    terminal_calls: list[object] = []

    def forbidden_terminal(*args, **kwargs):
        terminal_calls.append((args, kwargs))
        raise AssertionError("preflight reservation errors have no lifecycle token")

    monkeypatch.setattr(A.reservation, "check_reservation", fail_check)
    monkeypatch.setattr(A.trial_registry, "record_trial_terminal", forbidden_terminal)
    with pytest.raises(
        A.reservation.ReservationError,
        match="synthetic reservation rejection",
    ):
        A.run_trial(
            trial_id="reservation-error-order",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="claude-headless",
            run_root=tmp_path / "reservation-error-order",
            sub="/unused",
            do_build=False,
            allow_pegasus_compute_transport=True,
            allow_unregistered_exploratory=True,
        )
    assert terminal_calls == []


def test_run_trial_does_not_read_reservation_for_other_isolation(
    tmp_path, monkeypatch,
) -> None:
    read_calls: list[object] = []

    def forbidden_read(*args, **kwargs):
        read_calls.append((args, kwargs))
        raise AssertionError("reservation binding is not needed for OTHER")

    monkeypatch.setattr(A.reservation, "read_binding", forbidden_read)
    report = A.run_trial(
        trial_id="reservation-not-required",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "reservation-not-required",
        sub="/unused",
        do_build=False,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "complete"
    assert read_calls == []


def test_run_trial_no_build_uses_actual_compute_site_for_reservation(
    tmp_path, monkeypatch,
) -> None:
    site_calls: list[str] = []
    monkeypatch.setattr(
        A.trigger,
        "_current_site",
        lambda: site_calls.append(A.trigger.site_policy.PEGASUS_COMPUTE)
        or A.trigger.site_policy.PEGASUS_COMPUTE,
    )
    read_calls: list[object] = []

    def reject_unreserved_compute(environ):
        read_calls.append(environ)
        raise A.reservation.ReservationError(
            "actual compute site requires a reservation"
        )

    monkeypatch.setattr(A.reservation, "read_binding", reject_unreserved_compute)
    launches: list[str] = []

    def blocked_provider(**_kwargs):
        launches.append("provider")
        raise AssertionError("provider launch preceded the reservation gate")

    def blocked_campaign(*_args, **_kwargs):
        launches.append("campaign")
        raise AssertionError("campaign launch preceded the reservation gate")

    monkeypatch.setattr(A, "_provider_set", blocked_provider)
    monkeypatch.setattr(A.trigger, "drive_iteration", blocked_campaign)
    run_root = tmp_path / "actual-compute-no-build"
    with pytest.raises(
        A.reservation.ReservationError,
        match="actual compute site requires a reservation",
    ):
        A.run_trial(
            trial_id="actual-compute-no-build",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="fixture",
            run_root=run_root,
            sub="/unused",
            do_build=False,
            allow_pegasus_compute_transport=False,
            allow_unregistered_exploratory=True,
        )
    assert site_calls == [A.trigger.site_policy.PEGASUS_COMPUTE]
    assert len(read_calls) == 1
    assert launches == []
    assert not run_root.exists()


def test_run_trial_no_build_other_site_is_not_overrejected_by_transport_opt_in(
    tmp_path, monkeypatch,
) -> None:
    site_calls: list[str] = []

    def current_site():
        site_calls.append(A.trigger.site_policy.OTHER)
        return A.trigger.site_policy.OTHER

    monkeypatch.setattr(A.trigger, "_current_site", current_site)
    admission, _receipt = _pegasus_transport_fixture()
    monkeypatch.setattr(
        A,
        "admit_claude_transport",
        lambda **_kwargs: admission,
    )
    monkeypatch.setattr(
        A,
        "_provider_set",
        lambda **_kwargs: {
            role: A.FixtureRoleProvider(role) for role in A.ROLE_FILES
        },
    )
    monkeypatch.setattr(A.trigger, "drive_iteration", _fake_drive)
    monkeypatch.setattr(A, "_preview", _fake_preview)
    read_calls: list[object] = []

    def forbidden_read(*args, **kwargs):
        read_calls.append((args, kwargs))
        raise AssertionError("OTHER site must not read reservation binding")

    monkeypatch.setattr(A.reservation, "read_binding", forbidden_read)
    # Fake-drive terminal status is incidental; returning without ReservationError is the invariant.
    A.run_trial(
        trial_id="actual-other-no-build-opt-in",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="claude-headless",
        run_root=tmp_path / "actual-other-no-build-opt-in",
        sub="/unused",
        do_build=False,
        allow_pegasus_compute_transport=True,
        allow_unregistered_exploratory=True,
    )
    assert site_calls == [A.trigger.site_policy.OTHER] * 2
    assert read_calls == []


def test_run_trial_rejects_compute_build_before_artifact_or_provider(
    tmp_path, monkeypatch,
) -> None:
    run_root = tmp_path / "run"
    monkeypatch.setattr(
        A.trigger, "_current_site",
        lambda: A.trigger.site_policy.PEGASUS_COMPUTE,
    )
    with pytest.raises(A.AutonomousTrialError, match="T-276"):
        A.run_trial(
            trial_id="compute-build-still-closed",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="claude-headless",
            run_root=run_root,
            sub="/unused",
            do_build=True,
            allow_unregistered_exploratory=True,
        )
    assert not run_root.exists()


def test_run_trial_other_build_requires_parser_authority_before_artifact(
    tmp_path, monkeypatch,
) -> None:
    run_root = tmp_path / "run"
    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    with pytest.raises(A.AutonomousTrialError, match="parser-issued"):
        A.run_trial(
            trial_id="other-build-missing-authority",
            workloads=["ycsb-a"], generations=1,
            provider_kind="claude-headless", run_root=run_root,
            sub="/unused", do_build=True,
            allow_unregistered_exploratory=True,
        )
    assert not run_root.exists()


def test_8c_internal_entrypoints_have_no_site_injection_surface() -> None:
    assert "site" not in inspect.signature(A._run_workload).parameters
    assert "site" not in inspect.signature(A._finish_trial).parameters


def test_run_workload_direct_call_without_sealed_scope_is_rejected(
    tmp_path,
) -> None:
    class _Poison:
        def __getattr__(self, name):
            pytest.fail(f"scope rejection reached provider/journal: {name}")

    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=r"\[run-scope\] workload requires a sealed launch admission",
    ):
        A._run_workload(
            workload="ycsb-a", generations=1,
            providers={role: _Poison() for role in A.ROLE_FILES},
            journal=_Poison(), run_root=tmp_path / "run", sub="/unused",
            do_build=True, cache_root="", trial_id="compute-direct-rejected",
            started_monotonic=time.monotonic(), max_wall_s=60,
            gating_spec_snapshot=A.snapshot_gating_spec(A.GATING_SPEC),
        )
    assert not (tmp_path / "run").exists()


def test_public_run_trial_scope_preserves_t276_worker_gate(
    tmp_path, monkeypatch,
) -> None:
    sites = iter((
        A.trigger.site_policy.OTHER,
        A.trigger.site_policy.PEGASUS_COMPUTE,
    ))
    monkeypatch.setattr(A.trigger, "_current_site", lambda: next(sites))

    def exercise_worker(**kwargs):
        return A._run_workload(
            workload="ycsb-a",
            generations=1,
            providers={},
            journal=kwargs["journal"],
            run_root=kwargs["run_root"],
            sub="/unused",
            do_build=True,
            cache_root="",
            trial_id=kwargs["trial_id"],
            started_monotonic=kwargs["started_monotonic"],
            max_wall_s=60,
            build_context=kwargs["build_context"],
            gating_spec_snapshot=kwargs["gating_spec_snapshot"],
        )

    monkeypatch.setattr(A, "_finish_trial", exercise_worker)
    with pytest.raises(A.AutonomousTrialError, match="T-276"):
        A.run_trial(
            trial_id="public-scope-t276",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="fixture",
            run_root=tmp_path / "public-scope-t276",
            sub="/unused",
            do_build=True,
            providers={},
            coder_authority=_coder_authority(),
            allow_unregistered_exploratory=True,
        )


def test_finish_trial_direct_compute_build_rejects_before_provider(
    tmp_path, monkeypatch,
) -> None:
    monkeypatch.setattr(
        A.trigger, "_current_site",
        lambda: A.trigger.site_policy.PEGASUS_COMPUTE,
    )
    with _exploratory_scope(
        "compute-finish-rejected", ["ycsb-a"],
    ) as admission:
        with pytest.raises(A.AutonomousTrialError, match="T-276"):
            A._finish_trial(
                trial_id="compute-finish-rejected", selected=["ycsb-a"], generations=1,
                provider_kind="claude-headless", run_root=tmp_path / "run",
                sub="/unused", do_build=True, cache_root="", max_wall_s=60,
                drive=lambda *_a, **_k: pytest.fail("drive reached"),
                preview=lambda *_a, **_k: pytest.fail("preview reached"),
                journal=SimpleNamespace(), started="fixture",
                started_monotonic=time.monotonic(), active_providers={},
                fatal_error=None,
                transport_receipt=None,
                launch_admission=admission,
                gating_spec_snapshot=A.snapshot_gating_spec(A.GATING_SPEC),
            )
    assert not (tmp_path / "run").exists()


def test_finish_trial_rejects_copied_seal_from_different_admission(
    tmp_path,
) -> None:
    copied = A.trial_registry.admit_unregistered_exploratory(
        trial_id="copied-admission-source",
        workloads=["ycsb-a"],
        allow_unregistered_exploratory=True,
        repository_root=A.ROOT,
        registry_path=A.ROOT / A.trial_registry.DEFAULT_REGISTRY_PATH,
    )
    with _exploratory_scope("copied-admission-target", ["ycsb-a"]):
        with pytest.raises(
            A.trial_registry.TrialRegistryError,
            match=r"\[launch-admission\] supplied admission differs from fresh derivation$",
        ):
            A._finish_trial(
                trial_id="copied-admission-target",
                selected=["ycsb-a"],
                generations=1,
                provider_kind="fixture",
                run_root=tmp_path / "copied-admission",
                sub="/unused",
                do_build=False,
                cache_root="",
                max_wall_s=60,
                drive=lambda *_args, **_kwargs: pytest.fail("drive reached"),
                preview=lambda *_args, **_kwargs: pytest.fail("preview reached"),
                journal=SimpleNamespace(),
                started="fixture",
                started_monotonic=time.monotonic(),
                active_providers={},
                fatal_error={"type": "Fixture", "message": "stop"},
                transport_receipt=None,
                launch_admission=copied,
                gating_spec_snapshot=A.snapshot_gating_spec(A.GATING_SPEC),
            )


def test_compute_build_requires_matching_t276_transport_admission(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        A.trigger, "_current_site",
        lambda: A.trigger.site_policy.PEGASUS_COMPUTE,
    )
    source_env = {
        "PBS_JOBID": "12345.pegasus",
        "http_proxy": "http://proxy.example:18080",
        "https_proxy": "http://proxy.example:18443",
    }
    policy_bytes = json.dumps({
        "schema_version": "pegasus-claude-transport-policy/v1",
        "site": "PEGASUS_COMPUTE",
        "mode": "explicit-http-proxy-env",
        "endpoint_values": {
            "http_proxy": source_env["http_proxy"],
            "https_proxy": source_env["https_proxy"],
        },
    }).encode("utf-8")
    admission = claude_transport.evaluate_transport_admission(
        source_env=source_env,
        policy_bytes=policy_bytes,
        site=A.trigger.site_policy.PEGASUS_COMPUTE,
    )
    receipt = admission.receipt.as_dict()

    A._assert_build_site_opted_in(
        True, allow_pegasus_compute_transport=True,
    )
    A._assert_build_transport_admitted(
        True,
        transport_admission=admission,
        transport_receipt=receipt,
    )

    with pytest.raises(A.AutonomousTrialError, match="transport admission"):
        A._assert_build_transport_admitted(
            True,
            transport_admission=None,
            transport_receipt=None,
        )
    mismatched = dict(receipt)
    mismatched["pbs_jobid"] = "67890.pegasus"
    with pytest.raises(A.AutonomousTrialError, match="run-level snapshot"):
        A._assert_build_transport_admitted(
            True,
            transport_admission=admission,
            transport_receipt=mismatched,
        )


def test_transport_admission_error_persists_verified_partial_report(
    tmp_path, monkeypatch, valid_reservation_environment,
) -> None:
    class FixtureTransportAdmissionError(RuntimeError):
        pass

    admission_calls = []

    def reject_transport_admission(**kwargs):
        admission_calls.append(kwargs)
        raise FixtureTransportAdmissionError("fixture transport admission failed")

    monkeypatch.setattr(
        A.trigger, "_current_site",
        lambda: A.trigger.site_policy.PEGASUS_COMPUTE,
    )
    for key, value in valid_reservation_environment.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(A, "admit_claude_transport", reject_transport_admission)
    run_root = tmp_path / "transport-admission-error"
    report = A.run_trial(
        trial_id="transport-admission-error",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="claude-headless",
        run_root=run_root,
        sub="/unused",
        do_build=True,
        coder_authority=_coder_authority(),
        allow_pegasus_compute_transport=True,
        allow_unregistered_exploratory=True,
    )

    assert len(admission_calls) == 1
    persisted = json.loads((run_root / "report.json").read_text(encoding="utf-8"))
    assert persisted == report
    assert report["status"] == "partial"
    assert report["cells"] == []
    assert report["honest_accounting"] == {
        "role_query_count": 0,
        "bench_wall_seconds": 0.0,
    }
    assert "transport_receipt" not in report
    events = [
        json.loads(line)
        for line in (run_root / "attempts.jsonl").read_text(
            encoding="utf-8",
        ).splitlines()
    ]
    assert [event["event"] for event in events] == [
        "transport-admission-error", "run-start", "run-finish",
    ]
    assert set(events[0]) == {"event", "type", "message", "seq", "ts"}
    assert report["fatal_error"] == {
        "type": events[0]["type"],
        "message": events[0]["message"],
    }
    assert all("transport_receipt" not in event for event in events)
    completeness.verify_autonomous_trial_files(
        run_root / "attempts.jsonl", run_root / "report.json",
    )


def test_redacted_transport_error_replaces_endpoint_and_pbs_secrets() -> None:
    endpoint_secret = "http://user:secret@example.test:18080"
    pbs_jobid = "12345.pegasus"
    receipt = {
        "endpoint_values": {"http_proxy": endpoint_secret},
        "pbs_jobid": pbs_jobid,
    }

    message = A._redacted_transport_error(
        RuntimeError(f"endpoint={endpoint_secret} job={pbs_jobid}"),
        receipt,
    )

    assert endpoint_secret not in message
    assert pbs_jobid not in message
    assert message == "endpoint=<redacted> job=<redacted>"


def test_redacted_transport_error_removes_control_chars_without_receipt() -> None:
    message = A._redacted_transport_error(
        RuntimeError("left\r\n\t\x00middle right "),
        None,
    )

    assert message == "leftmiddleright"
    assert all(char not in message for char in "\r\n\t\x00  ")


def test_redacted_transport_error_caps_long_messages() -> None:
    marker = "...(truncated)"
    message = A._redacted_transport_error(RuntimeError("x" * 600), None)

    assert len(message) == 500
    assert message == "x" * (500 - len(marker)) + marker
    assert message.endswith(marker)


def test_redacted_transport_error_exactly_500_chars_unchanged() -> None:
    message = "x" * 500
    assert A._redacted_transport_error(RuntimeError(message), None) == message


def test_redacted_transport_error_501_chars_gets_capped() -> None:
    marker = "...(truncated)"
    message = A._redacted_transport_error(RuntimeError("x" * 501), None)

    assert len(message) == 500
    assert message == "x" * (500 - len(marker)) + marker


def test_redacted_transport_error_preserves_short_messages() -> None:
    message = "short provider failure"

    assert A._redacted_transport_error(RuntimeError(message), None) == message


def test_run_workload_other_build_reaches_drive_positive(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(A, "MAX_APPROVED_GENERATIONS", 2)
    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    run_root = tmp_path / "run"
    for child in (run_root, run_root / "raw", run_root / "proposals"):
        child.mkdir(exist_ok=True)
    campaign = _actual_campaign_layout(
        tmp_path,
        trial_id="other-build-positive",
        generations=2,
    )
    monkeypatch.setattr(
        A, "exploration_campaign_layout", lambda _campaign_id: campaign,
    )
    calls = []
    context = A.build_run_context(generator_id=A.GeneratorId.S8A_TRIGGER_SWEEP)

    def drive(*args, layout, **kwargs):
        calls.append((args, kwargs))
        assert args[7] is True
        assert "site" not in kwargs
        Path(layout.root).mkdir(parents=True, exist_ok=True)
        return {
            "outcome": "certified", "variant": "fixture-variant",
            "fitness_tps": 1.0, "stop_reason": "continue",
            "iteration": 1, "ran": True,
            "critic_digest_generated": False,
            "trigger_gate_binding_commitment": "b" * 64,
        }

    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    result = _run_workload_with_scope(
        workload="ycsb-a", generations=2, providers=providers,
        journal=A.AttemptJournal(run_root / "attempts.jsonl"), run_root=run_root,
        sub="/unused", do_build=True, cache_root="",
        trial_id="other-build-positive", started_monotonic=time.monotonic(),
        max_wall_s=60, drive=drive, preview=_fake_preview,
        build_context=context,
    )
    assert len(calls) == 2
    assert all(kwargs["build_context"] is context for _args, kwargs in calls)
    assert [item["outcome"] for item in result["generations"]] == [
        "certified", "certified",
    ]


def test_run_workload_direct_call_rejects_unapproved_budget(tmp_path) -> None:
    with pytest.raises(A.AutonomousTrialError, match="承認済み上限"):
        _run_workload_with_scope(
            workload="ycsb-a",
            generations=3,
            providers={},
            journal=SimpleNamespace(),
            run_root=tmp_path / "run",
            sub="/unused",
            do_build=False,
            cache_root="",
            trial_id="unapproved-direct-budget",
            started_monotonic=0.0,
            max_wall_s=1,
        )


def test_run_workload_rejects_existing_campaign_state(tmp_path, monkeypatch) -> None:
    """Monkeypatched loader poisons any provider call, fixing gate ordering."""

    class _ProviderMustNotRun:
        def invoke(self, *, invocation_id, payload):
            pytest.fail(f"freshness rejection reached provider: {invocation_id}")

    monkeypatch.setattr(
        A.loop_core, "load_loop_state", lambda layout: A.loop_core.LoopState()
    )
    providers = {
        role: _ProviderMustNotRun()
        for role in ("planner", "coder", "auditor", "critic")
    }
    with pytest.raises(A.AutonomousTrialError, match="既存 campaign state"):
        _run_workload_with_scope(
            workload="ycsb-a",
            generations=1,
            providers=providers,
            journal=SimpleNamespace(),
            run_root=tmp_path / "run",
            sub="/unused",
            do_build=False,
            cache_root="",
            trial_id="existing-state-rejected",
            started_monotonic=time.monotonic(),
            max_wall_s=60,
            build_context=_no_build_context(),
            gating_spec_snapshot=A.snapshot_gating_spec(A.GATING_SPEC),
        )


def test_run_workload_accepts_fresh_campaign_state(tmp_path, monkeypatch) -> None:
    """Monkeypatched loader fixes the fresh branch before provider invocation."""

    monkeypatch.setattr(A.loop_core, "load_loop_state", lambda layout: None)
    run_root = tmp_path / "run"
    run_root.mkdir()
    for child in ("raw", "proposals"):
        (run_root / child).mkdir()
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    result = _run_workload_with_scope(
        workload="ycsb-a",
        generations=1,
        providers=providers,
        journal=A.AttemptJournal(run_root / "attempts.jsonl"),
        run_root=run_root,
        sub="/unused",
        do_build=False,
        cache_root="",
        trial_id="fresh-state-accepted",
        started_monotonic=time.monotonic(),
        max_wall_s=60,
        drive=_fake_drive,
        preview=_fake_preview,
        build_context=_no_build_context(),
    )
    assert [generation["outcome"] for generation in result["generations"]] == [
        "dry-pass"
    ]
    assert all(
        len(providers[role].payloads) == 1
        for role in ("planner", "coder", "auditor")
    )
    assert providers["critic"].payloads == []
    assert len(result["_pending_critics"]) == 1


def test_run_workload_rejects_actual_existing_campaign_state(tmp_path) -> None:
    class _ProviderMustNotRun:
        def invoke(self, *, invocation_id, payload):
            pytest.fail(f"actual freshness rejection reached provider: {invocation_id}")

    run_root = tmp_path / "run"
    trial_id = "actual-existing-state-rejected"
    layout = _actual_campaign_layout(run_root, trial_id=trial_id)
    A.loop_core.save_loop_state(layout, A.loop_core.LoopState())
    providers = {
        role: _ProviderMustNotRun()
        for role in ("planner", "coder", "auditor", "critic")
    }
    with pytest.raises(A.AutonomousTrialError, match="既存 campaign state"):
        _run_workload_with_scope(
            workload="ycsb-a",
            generations=1,
            providers=providers,
            journal=SimpleNamespace(),
            run_root=run_root,
            sub="/unused",
            do_build=False,
            cache_root="",
            trial_id=trial_id,
            started_monotonic=time.monotonic(),
            max_wall_s=60,
            build_context=_no_build_context(),
            gating_spec_snapshot=A.snapshot_gating_spec(A.GATING_SPEC),
        )


def test_run_workload_accepts_actual_fresh_campaign_layout(tmp_path) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    for child in ("raw", "proposals"):
        (run_root / child).mkdir()
    layout = _actual_campaign_layout(
        run_root, trial_id="actual-fresh-state-accepted"
    )
    assert not Path(layout.root).exists()
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    result = _run_workload_with_scope(
        workload="ycsb-a",
        generations=1,
        providers=providers,
        journal=A.AttemptJournal(run_root / "attempts.jsonl"),
        run_root=run_root,
        sub="/unused",
        do_build=False,
        cache_root="",
        trial_id="actual-fresh-state-accepted",
        started_monotonic=time.monotonic(),
        max_wall_s=60,
        drive=_fake_drive,
        preview=_fake_preview,
        build_context=_no_build_context(),
    )
    assert [generation["outcome"] for generation in result["generations"]] == [
        "dry-pass"
    ]
    assert all(
        len(providers[role].payloads) == 1
        for role in ("planner", "coder", "auditor")
    )
    assert providers["critic"].payloads == []
    assert len(result["_pending_critics"]) == 1


def test_run_workload_build_passes_exploration_layout_to_trigger(
    tmp_path, monkeypatch,
) -> None:
    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    run_root = tmp_path / "run"
    run_root.mkdir()
    for child in ("raw", "proposals"):
        (run_root / child).mkdir()
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    factory = A.exploration_campaign_layout
    monkeypatch.setattr(
        A,
        "exploration_campaign_layout",
        lambda campaign_id: factory(campaign_id, str(tmp_path)),
    )
    passed_layouts = []
    context = A.build_run_context(generator_id=A.GeneratorId.S8A_TRIGGER_SWEEP)

    def drive_build(
        cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
        cache_root="", proposal_path="", extra_sources=(), build_context=None,
    ):
        assert do_build is True
        assert build_context is context
        passed_layouts.append(layout)
        Path(layout.root).mkdir(parents=True, exist_ok=True)
        return {
            "outcome": "dry-pass",
            "variant": None,
            "stop_reason": "continue",
            "iteration": 1,
            "ran": True,
            "critic_digest_generated": False,
            "trigger_gate_binding_commitment": "b" * 64,
        }

    result = _run_workload_with_scope(
        workload="ycsb-a",
        generations=1,
        providers=providers,
        journal=A.AttemptJournal(run_root / "attempts.jsonl"),
        run_root=run_root,
        sub="/unused",
        do_build=True,
        cache_root="/unused-cache",
        trial_id="build-exploration-layout",
        started_monotonic=time.monotonic(),
        max_wall_s=60,
        drive=drive_build,
        preview=_fake_preview,
        build_context=context,
    )

    expected = tmp_path / "exploration" / "campaigns" / result["campaign_id"]
    assert Path(result["campaign_root"]) == expected
    assert [Path(layout.root) for layout in passed_layouts] == [expected]


def test_run_trial_build_public_entry_passes_exploration_layout_to_trigger(
    tmp_path, monkeypatch,
) -> None:
    """F5/M08: public run_trial から実際に trigger sink へ渡る root を見る。"""
    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    factory = A.exploration_campaign_layout
    monkeypatch.setattr(
        A,
        "exploration_campaign_layout",
        lambda campaign_id: factory(campaign_id, str(tmp_path)),
    )
    passed_layouts = []

    def fake_finalize(cell, *, launch_admission):
        assert launch_admission.certifying is False
        cell["admission_decision"] = {
            "schema_version": "campaign-artifact-admission-decision/v1",
            "admission_status": "admitted",
            "classification": "admitted-new-schema",
        }

    monkeypatch.setattr(A, "_finalize_build_cell_admission", fake_finalize)
    monkeypatch.setattr(A, "assert_campaign_layer3_chain", lambda **_kwargs: None)

    def drive_build(
        cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
        cache_root="", proposal_path="", extra_sources=(), build_context=None,
    ):
        assert do_build is True
        assert type(build_context) is A.BuildRunContext
        assert build_context._authority_nonce is not None
        passed_layouts.append(layout)
        Path(layout.root).mkdir(parents=True, exist_ok=True)
        return {
            "outcome": "dry-pass",
            "variant": None,
            "stop_reason": "continue",
            "iteration": 1,
            "ran": True,
            "critic_digest_generated": False,
            "trigger_gate_binding_commitment": "b" * 64,
        }

    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="public-build-exploration-layout",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=True,
        providers=providers,
        drive=drive_build,
        preview=_fake_preview,
        coder_authority=_coder_authority(),
        allow_unregistered_exploratory=True,
    )
    expected = (
        tmp_path / "exploration" / "campaigns" / report["cells"][0]["campaign_id"]
    )
    assert [Path(layout.root) for layout in passed_layouts] == [expected]
    assert Path(report["cells"][0]["campaign_root"]) == expected
    assert not (tmp_path / "campaigns" / report["cells"][0]["campaign_id"]).exists()


def test_three_workload_build_positive_admission_passes_real_layer3_chain(
    tmp_path, monkeypatch,
) -> None:
    # The campaign fixture lives outside the repository.  Keep Layer 3's
    # authority fallback and the complete campaign-chain verifier real.
    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    factory = A.exploration_campaign_layout
    monkeypatch.setattr(
        A,
        "exploration_campaign_layout",
        lambda campaign_id: factory(campaign_id, str(tmp_path)),
    )
    checked_campaigns = []
    real_chain_check = A.assert_campaign_layer3_chain

    def observe_real_chain(*, report, output_root):
        real_chain_check(report=report, output_root=output_root)
        checked_campaigns.append([
            cell["campaign_id"] for cell in report["cells"]
        ])

    monkeypatch.setattr(A, "assert_campaign_layer3_chain", observe_real_chain)

    def drive_build(
        cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
        cache_root="", proposal_path="", extra_sources=(), build_context=None,
    ):
        assert do_build is True
        assert type(build_context) is A.BuildRunContext
        variant = _write_admitted_rejection_digest(cfg, layout, coder)
        return {
            "outcome": "rejected",
            "variant": variant,
            "verdict": "auditor-pass",
            "stop_reason": "continue",
            "iteration": 1,
            "ran": True,
            "critic_digest_generated": True,
            "trigger_gate_binding_commitment": "b" * 64,
        }

    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    run_root = tmp_path / "run"
    report = A.run_trial(
        trial_id="three-workload-build-positive-admission",
        workloads=["ycsb-a", "ycsb-b", "ycsb-c"],
        generations=1,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=True,
        providers=providers,
        drive=drive_build,
        preview=_fake_preview,
        coder_authority=_coder_authority(),
        allow_unregistered_exploratory=True,
    )

    report_path = run_root / "report.json"
    assert report["status"] == "complete"
    assert report["do_build"] is True
    assert report_path.is_file()
    assert json.loads(report_path.read_bytes()) == report
    assert [cell["workload"] for cell in report["cells"]] == [
        "ycsb-a", "ycsb-b", "ycsb-c",
    ]
    assert [
        (
            cell["admission_decision"]["schema_version"],
            cell["admission_decision"]["admission_status"],
            cell["admission_decision"]["classification"],
        )
        for cell in report["cells"]
    ] == [
        (
            "campaign-artifact-admission-decision/v1",
            "admitted",
            "admitted-new-schema",
        ),
        (
            "campaign-artifact-admission-decision/v1",
            "admitted",
            "admitted-new-schema",
        ),
        (
            "campaign-artifact-admission-decision/v1",
            "admitted",
            "admitted-new-schema",
        ),
    ]
    assert checked_campaigns == [[
        cell["campaign_id"] for cell in report["cells"]
    ]]
    assert all(
        (Path(cell["campaign_root"]) / "reports" / "layer3_report.json").is_file()
        for cell in report["cells"]
    )
    for cell in report["cells"]:
        campaign_root = Path(cell["campaign_root"])
        decoded_lock = campaign_lock.decode_campaign_lock(
            (campaign_root / "campaign.lock").read_text(encoding="utf-8")
        )
        assert decoded_lock.authority is not None
        persisted = json.loads(
            (campaign_root / "reports" / "layer3_report.json").read_bytes()
        )
        assert persisted["meta"]["generated_from_head"] == (
            decoded_lock.authority.contract_loader_commit
        )


def test_build_cell_admission_precedes_critic_invocation(
    tmp_path, monkeypatch,
) -> None:
    """Keep the real finalizer and observe its render boundary before critic."""
    order = []

    class _OrderedCritic(_RecordingFixture):
        def invoke(self, *, invocation_id, payload):
            order.append("critic")
            return super().invoke(invocation_id=invocation_id, payload=payload)

    def fake_render(campaign_root, persisted, *, output_root):
        order.append("admission")
        assert persisted == campaign_root / "reports" / "layer3_report.json"
        assert output_root == campaign_root.parent.parent
        return {
            "admission_decision": {
                "schema_version": "campaign-artifact-admission-decision/v1",
                "admission_status": "admitted",
                "classification": "admitted-new-schema",
            },
        }

    def drive_build(
        cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
        cache_root="", proposal_path="", extra_sources=(), build_context=None,
    ):
        assert do_build is True
        assert type(build_context) is A.BuildRunContext
        (Path(layout.root) / "reports").mkdir(parents=True, exist_ok=True)
        return {
            "outcome": "dry-pass",
            "variant": None,
            "stop_reason": "continue",
            "iteration": 1,
            "ran": True,
            "critic_digest_generated": False,
            "trigger_gate_binding_commitment": "b" * 64,
        }

    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    factory = A.exploration_campaign_layout
    monkeypatch.setattr(
        A,
        "exploration_campaign_layout",
        lambda campaign_id: factory(campaign_id, str(tmp_path)),
    )
    monkeypatch.setattr(A.layer3_report, "render", fake_render)
    monkeypatch.setattr(A, "assert_campaign_layer3_chain", lambda **_kwargs: None)
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor")
    }
    providers["critic"] = _OrderedCritic("critic")

    report = A.run_trial(
        trial_id="admission-before-critic",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=True,
        providers=providers,
        drive=drive_build,
        preview=_fake_preview,
        coder_authority=_coder_authority(),
        allow_unregistered_exploratory=True,
    )

    assert order == ["admission", "critic"]
    assert report["cells"][0]["admission_decision"] == {
        "schema_version": "campaign-artifact-admission-decision/v1",
        "admission_status": "admitted",
        "classification": "admitted-new-schema",
    }


def test_post_admission_invalid_critic_marks_cell_role_invalid(tmp_path) -> None:
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor")
    }
    providers["critic"] = _MalformedRecordingCritic()

    report = A.run_trial(
        trial_id="post-admission-invalid-critic",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    cell = report["cells"][0]
    assert cell["stop_reason"] == "role-invalid"
    assert report["status"] == "partial"
    assert cell["admission_decision"] == {
        "admission_status": "not-applicable",
    }


def test_build_post_admission_invalid_critic_keeps_positive_admission(
    tmp_path, monkeypatch,
) -> None:
    def fake_render(campaign_root, persisted, *, output_root):
        assert persisted == campaign_root / "reports" / "layer3_report.json"
        assert output_root == campaign_root.parent.parent
        return {
            "admission_decision": {
                "schema_version": "campaign-artifact-admission-decision/v1",
                "admission_status": "admitted",
                "classification": "admitted-new-schema",
            },
        }

    def drive_build(
        cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
        cache_root="", proposal_path="", extra_sources=(), build_context=None,
    ):
        assert do_build is True
        assert type(build_context) is A.BuildRunContext
        (Path(layout.root) / "reports").mkdir(parents=True, exist_ok=True)
        return {
            "outcome": "dry-pass",
            "variant": None,
            "stop_reason": "continue",
            "iteration": 1,
            "ran": True,
            "critic_digest_generated": False,
            "trigger_gate_binding_commitment": "b" * 64,
        }

    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    factory = A.exploration_campaign_layout
    monkeypatch.setattr(
        A,
        "exploration_campaign_layout",
        lambda campaign_id: factory(campaign_id, str(tmp_path)),
    )
    monkeypatch.setattr(A.layer3_report, "render", fake_render)
    monkeypatch.setattr(A, "assert_campaign_layer3_chain", lambda **_kwargs: None)
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor")
    }
    providers["critic"] = _MalformedRecordingCritic()

    report = A.run_trial(
        trial_id="build-invalid-critic-keeps-admission",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=True,
        providers=providers,
        drive=drive_build,
        preview=_fake_preview,
        coder_authority=_coder_authority(),
        allow_unregistered_exploratory=True,
    )

    cell = report["cells"][0]
    assert report["status"] == "partial"
    assert cell["stop_reason"] == "role-invalid"
    assert cell["admission_decision"] == {
        "schema_version": "campaign-artifact-admission-decision/v1",
        "admission_status": "admitted",
        "classification": "admitted-new-schema",
    }


def test_critic_invalid_cannot_drop_build_admission_decision(
    tmp_path, monkeypatch,
) -> None:
    render_calls = 0

    def fake_render(campaign_root, persisted, *, output_root):
        nonlocal render_calls
        render_calls += 1
        assert persisted == campaign_root / "reports" / "layer3_report.json"
        assert output_root == campaign_root.parent.parent
        return {
            "admission_decision": {
                "schema_version": "campaign-artifact-admission-decision/v1",
                "admission_status": "admitted",
                "classification": "admitted-new-schema",
            },
        }

    def drive_build(
        cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
        cache_root="", proposal_path="", extra_sources=(), build_context=None,
    ):
        assert do_build is True
        assert type(build_context) is A.BuildRunContext
        (Path(layout.root) / "reports").mkdir(parents=True, exist_ok=True)
        return {
            "outcome": "dry-pass",
            "variant": None,
            "stop_reason": "continue",
            "iteration": 1,
            "ran": True,
            "critic_digest_generated": False,
            "trigger_gate_binding_commitment": "b" * 64,
        }

    original = A._run_pending_critics

    def drop_admission_after_invalid_critic(cell, **kwargs):
        original(cell, **kwargs)
        assert cell["stop_reason"] == "role-invalid"
        cell.pop("admission_decision")

    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    factory = A.exploration_campaign_layout
    monkeypatch.setattr(
        A,
        "exploration_campaign_layout",
        lambda campaign_id: factory(campaign_id, str(tmp_path)),
    )
    monkeypatch.setattr(A.layer3_report, "render", fake_render)
    monkeypatch.setattr(A, "assert_campaign_layer3_chain", lambda **_kwargs: None)
    monkeypatch.setattr(
        A, "_run_pending_critics", drop_admission_after_invalid_critic,
    )
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor")
    }
    providers["critic"] = _MalformedRecordingCritic()
    run_root = tmp_path / "run"

    with pytest.raises(
        A.AutonomousTrialError,
        match="^cell admission decision missing before report construction$",
    ):
        A.run_trial(
            trial_id="critic-invalid-drops-build-admission",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="fixture",
            run_root=run_root,
            sub="/unused",
            do_build=True,
            providers=providers,
            drive=drive_build,
            preview=_fake_preview,
            coder_authority=_coder_authority(),
            allow_unregistered_exploratory=True,
        )

    assert render_calls == 1
    assert not (run_root / "report.json").exists()


def test_invalid_critic_overrides_harness_terminal_stop(tmp_path) -> None:
    def terminal_drive(*args, **kwargs):
        outcome = _fake_drive(*args, **kwargs)
        outcome["stop_reason"] = "converged"
        return outcome

    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor")
    }
    providers["critic"] = _MalformedRecordingCritic()

    report = A.run_trial(
        trial_id="invalid-critic-overrides-harness",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=terminal_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    cell = report["cells"][0]
    assert cell["generations"][0]["harness"]["stop_reason"] == "converged"
    assert cell["stop_reason"] == "role-invalid"


def test_pending_critic_phase_sets_role_invalid_directly(tmp_path) -> None:
    def exercise(initial_stop_reason: str, label: str) -> dict[str, Any]:
        run_root = tmp_path / label
        (run_root / "raw").mkdir(parents=True)
        journal = A.AttemptJournal(run_root / "attempts.jsonl")
        accounting = A._new_generation_accounting(
            workload="ycsb-a",
            generation=1,
            journal=journal,
            generation_driver={
                "wrapper": "s8c-generation/v1",
                "delegate": "caller-injected-unsupported",
            },
            gating_spec_sha256=hashlib.sha256(
                A.GATING_SPEC.encode("utf-8")
            ).hexdigest(),
            authority="excluded-caller-injected-unsupported",
        )
        cell = {
            "workload": "ycsb-a",
            "campaign_root": str(run_root / "campaign"),
            "generations": [{"generation": 1, "roles": {}}],
            "stop_reason": initial_stop_reason,
            "admission_decision": {"admission_status": "not-applicable"},
            "_pending_critics": [{
                "generation": 1,
                "common": {
                    "generation": 1,
                    "descriptor_binding": {"output_sha256": "d" * 64},
                },
                "outcome": {
                    "outcome": "dry-pass",
                    "verdict": None,
                    "stop_reason": "continue",
                },
                "metrics": {
                    "throughput_tps": None,
                    "abort_rate": None,
                    "latency_ns": None,
                    "llc_miss_rate": None,
                    "ipc": None,
                },
                "raw_variant": None,
                "critic_digest_generated": False,
                "critic_attempted": False,
                "accounting": accounting,
            }],
        }
        A._run_pending_critics(
            cell,
            providers={"critic": _MalformedRecordingCritic()},
            journal=journal,
            run_root=run_root,
            transport_receipt=None,
        )
        return cell

    fixed_budget = exercise("fixed-generation-budget", "fixed-budget")
    assert fixed_budget["stop_reason"] == "role-invalid"
    harness_terminal = exercise("converged", "harness-terminal")
    assert harness_terminal["stop_reason"] == "role-invalid"


def test_finish_trial_status_follows_both_critic_phases_by_ast() -> None:
    tree = ast.parse(Path(A.__file__).read_text(encoding="utf-8"))
    finish = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_finish_trial"
    )
    status_assignments = [
        node
        for node in ast.walk(finish)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "status"
            for target in node.targets
        )
    ]
    assert len(status_assignments) == 1
    helper_calls = {
        name: [
            node
            for node in ast.walk(finish)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == name
        ]
        for name in ("_finalize_cell_admission", "_run_pending_critics")
    }
    assert {name: len(calls) for name, calls in helper_calls.items()} == {
        "_finalize_cell_admission": 2,
        "_run_pending_critics": 2,
    }
    workload_loop = next(
        node
        for node in ast.walk(finish)
        if isinstance(node, ast.For)
        and isinstance(node.target, ast.Name)
        and node.target.id == "workload"
    )
    workload_try = next(
        node
        for node in workload_loop.body
        if isinstance(node, ast.Try)
        and any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "_run_workload"
            for call in ast.walk(node)
        )
    )
    assert len(workload_try.handlers) == 1
    handler = workload_try.handlers[0]
    handler_helper_calls = {
        name: [
            node
            for node in ast.walk(handler)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == name
        ]
        for name in helper_calls
    }
    assert {name: len(calls) for name, calls in handler_helper_calls.items()} == {
        "_finalize_cell_admission": 1,
        "_run_pending_critics": 1,
    }
    normal_body = workload_loop.body[workload_loop.body.index(workload_try) + 1:]
    normal_helper_calls = {
        name: [
            node
            for statement in normal_body
            for node in ast.walk(statement)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == name
        ]
        for name in helper_calls
    }
    assert {name: len(calls) for name, calls in normal_helper_calls.items()} == {
        "_finalize_cell_admission": 1,
        "_run_pending_critics": 1,
    }
    handler_append = next(
        node
        for node in ast.walk(handler)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "cells"
        and node.func.attr == "append"
    )
    assert handler_append.lineno < min(
        call.lineno
        for calls in handler_helper_calls.values()
        for call in calls
    )
    assert status_assignments[0].lineno > max(
        call.lineno
        for calls in helper_calls.values()
        for call in calls
    )


def test_cell_admission_failure_is_not_converted_to_supervisor_error(
    tmp_path, monkeypatch,
) -> None:
    def fail_finalize(cell, *, launch_admission):
        raise A.AutonomousTrialError("fixture admission failure")

    def drive_build(
        cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
        cache_root="", proposal_path="", extra_sources=(), build_context=None,
    ):
        assert do_build is True
        Path(layout.root).mkdir(parents=True, exist_ok=True)
        return {
            "outcome": "dry-pass",
            "variant": None,
            "stop_reason": "continue",
            "iteration": 1,
            "ran": True,
            "critic_digest_generated": False,
            "trigger_gate_binding_commitment": "b" * 64,
        }

    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    factory = A.exploration_campaign_layout
    monkeypatch.setattr(
        A,
        "exploration_campaign_layout",
        lambda campaign_id: factory(campaign_id, str(tmp_path)),
    )
    monkeypatch.setattr(A, "_finalize_build_cell_admission", fail_finalize)
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    run_root = tmp_path / "run"

    report = A.run_trial(
        trial_id="cell-admission-failure",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=True,
        providers=providers,
        drive=drive_build,
        preview=_fake_preview,
        coder_authority=_coder_authority(),
        allow_unregistered_exploratory=True,
    )

    assert providers["critic"].payloads == []
    report_path = run_root / "report.json"
    assert report_path.is_file()
    assert json.loads(report_path.read_bytes()) == report
    assert report["status"] == "partial"
    decision = report["cells"][0]["admission_decision"]
    assert decision == {
        "schema_version": (
            "p3-autonomous-workload-trial-cell-admission-failure/v1"
        ),
        "admission_status": "failed",
        "error": {
            "type": "AutonomousTrialError",
            "message": "fixture admission failure",
        },
    }
    assert decision["admission_status"] != "admitted"
    assert report["cells"][0]["pending_critic_disposition"] == {
        "schema_version": (
            "p3-autonomous-workload-trial-pending-critic-disposition/v1"
        ),
        "action": "discarded",
        "reason": "cell-admission-failure",
        "count": 1,
    }
    events = [
        json.loads(line)
        for line in (run_root / "attempts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert all(event["event"] != "supervisor-error" for event in events)
    accounting = [
        event for event in events
        if event["event"] == "generation-accounting"
    ]
    assert len(accounting) == 1
    assert accounting[0]["state"] == "partial-generation"
    assert events[-1]["event"] == "run-finish"
    assert events[-1]["cell_admission_failures"] == [{
        "cell_index": 0,
        "workload": "ycsb-a",
        "admission_decision": decision,
    }]
    mutated = copy.deepcopy(report)
    mutated["cells"][0]["admission_decision"]["error"]["message"] = (
        "mutated admission failure"
    )
    with pytest.raises(
        completeness.AutonomousTrialCompletenessError,
        match="run-finish cell admission failures differ from report",
    ):
        completeness.assert_autonomous_trial_completeness(
            report=mutated,
            attempt_journal=run_root / "attempts.jsonl",
        )


def test_cell_admission_does_not_catch_unexpected_finalizer_exception(
    tmp_path, monkeypatch,
) -> None:
    def fail_finalize(cell, *, launch_admission):
        raise KeyError("unexpected finalizer bug")

    monkeypatch.setattr(A, "_finalize_build_cell_admission", fail_finalize)
    run_root = tmp_path / "run"
    run_root.mkdir()
    journal = A.AttemptJournal(run_root / "attempts.jsonl")
    cell = {"_pending_critics": []}
    with _exploratory_scope("unexpected-finalizer", ["ycsb-a"]) as admission:
        with pytest.raises(KeyError, match="unexpected finalizer bug"):
            A._finalize_cell_admission(
                cell,
                do_build=True,
                launch_admission=admission,
                journal=journal,
            )
    assert "admission_decision" not in cell
    assert "pending_critic_disposition" not in cell


def test_three_workload_normal_return_admission_failure_writes_partial_report(
    tmp_path, monkeypatch,
) -> None:
    def fail_finalize(cell, *, launch_admission):
        raise A.AutonomousTrialError("fixture admission failure")

    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    factory = A.exploration_campaign_layout
    monkeypatch.setattr(
        A,
        "exploration_campaign_layout",
        lambda campaign_id: factory(campaign_id, str(tmp_path)),
    )
    monkeypatch.setattr(A, "_finalize_build_cell_admission", fail_finalize)
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "auditor", "critic")
    }
    providers["coder"] = _MalformedRecordingCritic()
    run_root = tmp_path / "run"

    report = A.run_trial(
        trial_id="three-workload-normal-admission-failure",
        workloads=["ycsb-a", "ycsb-b", "ycsb-c"],
        generations=1,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=True,
        providers=providers,
        drive=lambda *_args, **_kwargs: pytest.fail(
            "coder-invalid path must not invoke the harness"
        ),
        preview=_fake_preview,
        coder_authority=_coder_authority(),
        allow_unregistered_exploratory=True,
    )

    report_path = run_root / "report.json"
    assert report_path.is_file()
    assert json.loads(report_path.read_bytes()) == report
    assert report["status"] == "partial"
    assert [cell["workload"] for cell in report["cells"]] == ["ycsb-a"]
    decision = report["cells"][0]["admission_decision"]
    assert decision == {
        "schema_version": (
            "p3-autonomous-workload-trial-cell-admission-failure/v1"
        ),
        "admission_status": "failed",
        "error": {
            "type": "AutonomousTrialError",
            "message": "fixture admission failure",
        },
    }
    assert decision["admission_status"] != "admitted"
    assert providers["critic"].payloads == []
    events = [
        json.loads(line)
        for line in (run_root / "attempts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert all(event["event"] != "supervisor-error" for event in events)
    accounting = [
        event for event in events
        if event["event"] == "generation-accounting"
    ]
    assert len(accounting) == 1
    assert accounting[0]["state"] == "partial-generation"
    assert events[-1]["cell_admission_failures"] == [{
        "cell_index": 0,
        "workload": "ycsb-a",
        "admission_decision": decision,
    }]


def test_three_workload_supervisor_error_admission_failure_writes_partial_report(
    tmp_path, monkeypatch,
) -> None:
    def fail_finalize(cell, *, launch_admission):
        raise A.AutonomousTrialError("fixture admission failure")

    def fail_drive(
        cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
        cache_root="", proposal_path="", extra_sources=(), build_context=None,
    ):
        assert do_build is True
        Path(layout.root).mkdir(parents=True, exist_ok=True)
        raise KeyError("build_start")

    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    factory = A.exploration_campaign_layout
    monkeypatch.setattr(
        A,
        "exploration_campaign_layout",
        lambda campaign_id: factory(campaign_id, str(tmp_path)),
    )
    monkeypatch.setattr(A, "_finalize_build_cell_admission", fail_finalize)
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    run_root = tmp_path / "run"

    report = A.run_trial(
        trial_id="three-workload-supervisor-admission-failure",
        workloads=["ycsb-a", "ycsb-b", "ycsb-c"],
        generations=1,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=True,
        providers=providers,
        drive=fail_drive,
        preview=_fake_preview,
        coder_authority=_coder_authority(),
        allow_unregistered_exploratory=True,
    )

    report_path = run_root / "report.json"
    assert report_path.is_file()
    assert json.loads(report_path.read_bytes()) == report
    assert report["status"] == "partial"
    assert report["fatal_error"] == {
        "type": "KeyError",
        "message": "'build_start'",
    }
    decision = report["cells"][0]["admission_decision"]
    assert decision == {
        "schema_version": (
            "p3-autonomous-workload-trial-cell-admission-failure/v1"
        ),
        "admission_status": "failed",
        "error": {
            "type": "AutonomousTrialError",
            "message": "fixture admission failure",
        },
    }
    assert decision["admission_status"] != "admitted"
    assert providers["critic"].payloads == []
    events = [
        json.loads(line)
        for line in (run_root / "attempts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert [event["event"] for event in events][-2:] == [
        "supervisor-error", "run-finish",
    ]
    assert events[-1]["cell_admission_failures"] == [{
        "cell_index": 0,
        "workload": "ycsb-a",
        "admission_decision": decision,
    }]


def test_pending_critic_failure_is_converted_to_supervisor_error(
    tmp_path,
) -> None:
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor")
    }
    run_root = tmp_path / "run"

    report = A.run_trial(
        trial_id="pending-critic-supervisor-error",
        workloads=["ycsb-a", "ycsb-b"],
        generations=1,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    assert report["status"] == "partial"
    assert report["fatal_error"]["type"] == "KeyError"
    assert len(report["cells"]) == 1
    cell = report["cells"][0]
    assert cell["stop_reason"] == "supervisor-error"
    assert cell["admission_decision"] == {
        "admission_status": "not-applicable",
    }
    assert (run_root / "report.json").is_file()
    events = [
        json.loads(line)
        for line in (run_root / "attempts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert [event["event"] for event in events][-2:] == [
        "supervisor-error", "run-finish",
    ]


def test_registered_pending_critic_failure_is_indeterminate(
    tmp_path, t325_registered_trial,
) -> None:
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor")
    }

    # Stop after generation one so the missing critic is reached by the
    # _finish_trial pending-critic drain (the second exception branch).
    def stop_after_first_generation(*args, **kwargs):
        outcome = _fake_drive(*args, **kwargs)
        outcome["stop_reason"] = "converged"
        return outcome

    run_root = tmp_path / "registered-critic-failure"
    report = _t325_run(
        t325_registered_trial,
        run_root,
        providers=providers,
        drive=stop_after_first_generation,
    )

    assert report["status"] == "partial"
    assert report["cells"][0]["stop_reason"] == "supervisor-error"
    assert report["lifecycle_terminal_status"] == "indeterminate"
    attempt_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_ATTEMPT_REGISTRY_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    attempt_terminal = next(
        row for row in attempt_rows if row.get("event") == "terminal"
    )
    assert attempt_terminal["terminal_status"] == "not-consumed"
    assert attempt_terminal["report_sha256"] is None
    assert attempt_terminal["observation_sha256"] is None
    assert attempt_terminal["primary_value"] is None
    lifecycle_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_LIFECYCLE_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    assert lifecycle_rows[-1]["terminal_status"] == "indeterminate"


def test_residual_pending_critics_block_report_publish(
    tmp_path, monkeypatch,
) -> None:
    """This seam restores an artificial state unreachable from today's producer."""
    original = A._run_pending_critics

    def restore_consumed_pending(cell, **kwargs):
        pending = list(cell["_pending_critics"])
        original(cell, **kwargs)
        cell["_pending_critics"] = pending

    monkeypatch.setattr(A, "_run_pending_critics", restore_consumed_pending)
    run_root = tmp_path / "run"
    with pytest.raises(
        A.AutonomousTrialError,
        match="^pending critic remained before report construction$",
    ):
        A.run_trial(
            trial_id="residual-pending-blocks-report",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="fixture",
            run_root=run_root,
            sub="/unused",
            do_build=False,
            drive=_fake_drive,
            preview=_fake_preview,
            allow_unregistered_exploratory=True,
        )
    assert not (run_root / "report.json").exists()


def test_two_generation_critic_feedback_precedes_next_planner(
    tmp_path, monkeypatch,
) -> None:
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    run_root = tmp_path / "run"

    report = A.run_trial(
        trial_id="multi-generation-critic-feedback",
        workloads=["ycsb-a"],
        generations=2,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    events = [
        json.loads(line)
        for line in (run_root / "attempts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert [
        (event["generation"], event["role"])
        for event in events
        if event["event"] == "role-attempt"
    ] == [
        (1, "planner"),
        (1, "coder"),
        (1, "auditor"),
        (1, "critic"),
        (2, "planner"),
        (2, "coder"),
        (2, "auditor"),
        (2, "critic"),
    ]
    assert [
        payload["generation"] for payload in providers["critic"].payloads
    ] == [1, 2]
    assert report["status"] == "complete"
    assert "critic_feedback" not in providers["planner"].payloads[0]
    feedback = providers["planner"].payloads[1]["critic_feedback"]
    assert feedback["source_generation"] == 1
    assert set(feedback) == {
        "source_generation", "diagnostics", "uncertainty_present",
        "reverse_recommended",
    }
    for payload in providers["planner"].payloads:
        assert all(value is None for value in payload["current_perf"].values())
        assert payload["leading_indicators"]["cache_miss_rate_pct"] is None
        assert payload["leading_indicators"]["IPC_overall"] is None
    for payload in providers["coder"].payloads:
        assert all(value is None for value in payload["baseline"].values())
    assert report["honest_accounting"] == {
        "role_query_count": 8,
        "bench_wall_seconds": 0.0,
    }
    assert (run_root / "report.json").is_file()


def test_payload_validation_receipts_are_durable_in_journal_and_report(
    tmp_path,
) -> None:
    run_root = tmp_path / "durable-validation-receipts"
    report = A.run_trial(
        trial_id="durable-validation-receipts",
        workloads=["ycsb-a"],
        generations=2,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        drive=_fake_drive_with_finite_metrics,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    journal_roles = {
        (event["generation"], event["role"]): event
        for event in (
            json.loads(line)
            for line in (run_root / "attempts.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
        )
        if event["event"] == "role-attempt"
    }
    for generation in report["cells"][0]["generations"]:
        for role in ("planner", "coder"):
            event = generation["roles"][role]
            receipt = event["payload_validation_receipt"]
            assert receipt == journal_roles[(generation["generation"], role)][
                "payload_validation_receipt"
            ]
            assert receipt["payload_sha256"] == event["input_payload_sha256"]
            assert receipt["payload_allowlist_sha256"] == (
                A.ROLE_PAYLOAD_ALLOWLIST_SHA256
            )
            assert receipt["safe_projection_sha256"] == hashlib.sha256(
                A._canonical_json_bytes(receipt["safe_projection"])
            ).hexdigest()
            assert "fitness_tps" not in json.dumps(
                receipt["safe_projection"], sort_keys=True,
            )


def test_two_generation_role_metric_snapshot_fields_are_byte_identical(
    tmp_path, monkeypatch,
) -> None:
    expected_perf = {
        "throughput_tps": 12345.0,
        "abort_rate_pct": 7.9,
        "latency_ns": 456.0,
        "llc_miss_rate": 0.124,
        "ipc": 2.5,
    }
    expected_leading = {
        "contention_level": "fixture-contention",
        "cache_miss_rate_pct": 12.4,
        "IPC_overall": 2.5,
    }

    def role_projection(current_metrics, *, contention_level):
        return dict(expected_perf), dict(expected_leading)

    monkeypatch.setattr(A, "_role_metric_payloads", role_projection)
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="two-generation-role-metric-snapshot-bytes",
        workloads=["ycsb-a"],
        generations=2,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    assert report["status"] == "complete"
    assert providers["planner"].payloads[0]["current_perf"] == expected_perf
    assert providers["planner"].payloads[0][
        "leading_indicators"
    ] == expected_leading
    assert providers["coder"].payloads[0]["baseline"] == expected_perf
    for role, field in (
        ("planner", "current_perf"),
        ("planner", "leading_indicators"),
        ("coder", "baseline"),
    ):
        first, second = providers[role].payloads
        assert A._canonical_json_bytes(first[field]) == A._canonical_json_bytes(
            second[field]
        )


def test_finite_generation_one_metrics_do_not_refresh_generation_two_payload(
    tmp_path,
) -> None:
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="finite-metrics-do-not-refresh-role-snapshot",
        workloads=["ycsb-a"],
        generations=2,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive_with_finite_metrics,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    assert report["cells"][0]["generations"][0]["harness"][
        "fitness_tps"
    ] == 12345.0
    for payload in providers["planner"].payloads:
        assert all(value is None for value in payload["current_perf"].values())
        assert payload["leading_indicators"]["cache_miss_rate_pct"] is None
        assert payload["leading_indicators"]["IPC_overall"] is None
    for payload in providers["coder"].payloads:
        assert all(value is None for value in payload["baseline"].values())


@pytest.mark.parametrize(
    ("anchor", "expected_message", "target_role"),
    [
        (
            "_planner_current_perf_payload",
            "payload.current_perf.throughput_tps",
            "planner",
        ),
        (
            "_planner_leading_indicators_payload",
            "payload.leading_indicators.cache_miss_rate_pct",
            "planner",
        ),
        (
            "_coder_baseline_payload",
            "payload.baseline.throughput_tps",
            "coder",
        ),
    ],
)
def test_generation_updated_metric_reinsertion_fails_before_target_provider(
    tmp_path, monkeypatch, anchor, expected_message, target_role,
) -> None:
    def reinsert_generation_metrics(
        frozen, *, current_metrics, contention_level,
    ):
        del frozen
        perf, leading = A._role_metric_payloads(
            current_metrics, contention_level=contention_level,
        )
        return leading if "leading" in anchor else perf

    monkeypatch.setattr(A, anchor, reinsert_generation_metrics)
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    run_root = tmp_path / anchor
    run_root.mkdir()
    for child in ("raw", "proposals"):
        (run_root / child).mkdir()
    with pytest.raises(PayloadValidationError, match=expected_message):
        _run_workload_with_scope(
            workload="ycsb-a",
            generations=2,
            providers=providers,
            journal=A.AttemptJournal(run_root / "attempts.jsonl"),
            run_root=run_root,
            sub="/unused",
            do_build=False,
            cache_root="",
            trial_id=f"metric-reinsertion-{target_role}-{anchor[-8:]}",
            started_monotonic=time.monotonic(),
            max_wall_s=60,
            drive=_fake_drive_with_finite_metrics,
            preview=_fake_preview,
            build_context=_no_build_context(),
        )
    assert len(providers[target_role].payloads) == 1


def test_allowed_whiteboard_origin_substitution_fails_before_planner(
    tmp_path, monkeypatch,
) -> None:
    original = A._whiteboard
    substituted = False

    def substitute_once(layout):
        nonlocal substituted
        whiteboard = original(layout)
        if whiteboard and not substituted:
            substituted = True
            changed = copy.deepcopy(whiteboard)
            changed[0]["direction"] = (
                "increase"
                if changed[0]["direction"] != "increase"
                else "decrease"
            )
            return changed
        return whiteboard

    monkeypatch.setattr(A, "_whiteboard", substitute_once)
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    run_root = tmp_path / "whiteboard-origin-substitution"
    run_root.mkdir()
    for child in ("raw", "proposals"):
        (run_root / child).mkdir()
    with pytest.raises(PayloadValidationError, match="whiteboard.*外部期待値"):
        _run_workload_with_scope(
            workload="ycsb-a",
            generations=2,
            providers=providers,
            journal=A.AttemptJournal(run_root / "attempts.jsonl"),
            run_root=run_root,
            sub="/unused",
            do_build=False,
            cache_root="",
            trial_id="whiteboard-origin-substitution",
            started_monotonic=time.monotonic(),
            max_wall_s=60,
            drive=_fake_drive,
            preview=_fake_preview,
            build_context=_no_build_context(),
        )
    assert substituted is True
    assert len(providers["planner"].payloads) == 1


def test_role_metric_payload_and_validation_projections_use_initial_state(
    tmp_path, monkeypatch,
) -> None:
    calls = []
    original = A._role_metric_payloads

    def recording_projection(current_metrics, *, contention_level):
        calls.append((dict(current_metrics), contention_level))
        return original(current_metrics, contention_level=contention_level)

    monkeypatch.setattr(A, "_role_metric_payloads", recording_projection)
    report = A.run_trial(
        trial_id="one-role-metric-snapshot-per-workload",
        workloads=["ycsb-a", "ycsb-b"],
        generations=2,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        drive=_fake_drive_with_finite_metrics,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    assert report["status"] == "complete"
    assert len(calls) == 2
    assert all(
        all(value is None for value in metrics.values())
        for metrics, _contention_level in calls
    )


def test_role_metric_payloads_do_not_alias_frozen_validator_expectations(
    tmp_path, monkeypatch,
) -> None:
    planner_aliases = []
    coder_aliases = []
    original_planner_validator = A.validate_planner_payload
    original_coder_validator = A.validate_coder_payload

    def planner_validator(payload, **kwargs):
        planner_aliases.append((
            payload["current_perf"] is kwargs["expected_current_perf"],
            payload["leading_indicators"]
            is kwargs["expected_leading_indicators"],
        ))
        return original_planner_validator(payload, **kwargs)

    def coder_validator(payload, **kwargs):
        coder_aliases.append(
            payload["baseline"] is kwargs["expected_baseline"]
        )
        return original_coder_validator(payload, **kwargs)

    monkeypatch.setattr(A, "validate_planner_payload", planner_validator)
    monkeypatch.setattr(A, "validate_coder_payload", coder_validator)
    report = A.run_trial(
        trial_id="role-metric-snapshot-no-alias",
        workloads=["ycsb-a"],
        generations=2,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        drive=_fake_drive_with_finite_metrics,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    assert report["status"] == "complete"
    assert planner_aliases == [(False, False), (False, False)]
    assert coder_aliases == [False, False]


def test_standard_drive_two_generation_no_build_uses_s8c_wrapper(
    tmp_path, monkeypatch, ratified_enforcement_source,
) -> None:
    from orchestrator.campaign import patchharness

    ccbench = tmp_path / "ccbench"
    source = ccbench / A.trigger.SOURCE_REL
    source.parent.mkdir(parents=True)
    source.write_text(
        """// EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating
#if BACKOFF_TRIGGER_GATING
  izanagi_gate_pass = true;
#else
  Backoff::backoff(FLAGS_clocks_per_us);
#endif
// EVOLVE-BLOCK-END silo-backoff-trigger-gating
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(A, "assert_pinned_clean", lambda *_a, **_k: None)
    monkeypatch.setattr(
        A, "applied", lambda *_a, **_k: contextlib.nullcontext(),
    )
    monkeypatch.setattr(
        patchharness, "applied", lambda *_a, **_k: contextlib.nullcontext(),
    )
    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="standard-drive-two-generation",
        workloads=["ycsb-a"],
        generations=2,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub=str(ccbench),
        do_build=False,
        providers=providers,
        allow_unregistered_exploratory=True,
    )
    cell = report["cells"][0]
    assert [
        generation["harness"]["iteration"]
        for generation in cell["generations"]
    ] == [1, 2]
    provenance = json.loads(
        (
            Path(cell["campaign_root"])
            / "reports"
            / A.trigger.PROVENANCE_BASENAME
        ).read_text(encoding="utf-8")
    )
    assert sorted(provenance["entries"]) == ["1", "2"]
    assert report["generation_driver"] == {
        "wrapper": "s8c-generation/v1",
        "delegate": "trigger.drive_iteration",
    }
    assert report["honest_accounting_authority"] == "supervisor-authoritative"


def test_generation_one_payload_bytes_are_exactly_legacy_shape(tmp_path) -> None:
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="generation-one-payload-bytes",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    cell = report["cells"][0]
    common = {
        "schema_version": "p3-autonomous-workload-trial/v4",
        "pilot_scope": "exploratory-ycsb-abc",
        "scientific_claim": False,
        "workload": "ycsb-a",
        "generation": 1,
        "workload_descriptor": cell["descriptor"],
        "descriptor_binding": cell["descriptor_binding"],
        "attempt_policy": {"attempts_per_role_generation": 1, "retry": False},
        "stop_policy": {
            "performance_early_stop": False,
            "generation_budget_is_fixed": True,
        },
    }
    null_perf = {
        "throughput_tps": None,
        "abort_rate_pct": None,
        "latency_ns": None,
        "llc_miss_rate": None,
        "ipc": None,
    }
    expected_planner = {
        **common,
        "current_perf": null_perf,
        "leading_indicators": {
            "contention_level": cell["descriptor"]["contention"]["label"],
            "cache_miss_rate_pct": None,
            "IPC_overall": None,
        },
        "whiteboard": [],
    }
    assert providers["planner"].payload_bytes[0] == A._canonical_json_bytes(
        expected_planner
    )
    assert "critic_feedback" not in expected_planner
    expected_coder = {
        **common,
        "leakproof_context": (
            "Use only this campaign's projected descriptor, metrics, planner direction, "
            "and abstract whiteboard. No prior sweep winner, candidate ranking, or "
            "unmeasured performance is available."
        ),
        "gating_spec": A.GATING_SPEC,
        "planner_direction": {
            "axis": "silo-backoff-trigger-gating",
            "direction": "explore_both",
            "magnitude": "small",
        },
        "baseline": null_perf,
        "whiteboard": [],
    }
    assert providers["coder"].payload_bytes[0] == A._canonical_json_bytes(
        expected_coder
    )


def test_off_common_payload_is_holdout_invariant(t325_registered_trial) -> None:
    commit = _t325_git(t325_registered_trial.repo, "rev-parse", "HEAD")
    payloads = []
    records = []
    for holdout, workload in (("H1", "rr80"), ("H2", "rr20")):
        resolved = A.s8c_arm_inputs.resolve_arm_input(
            arm="off",
            holdout=holdout,
            repository_root=t325_registered_trial.repo,
            commit=commit,
        )
        descriptor, descriptor_record = A._descriptor_from_resolved_arm_input(
            resolved
        )
        before = copy.deepcopy(descriptor_record)
        records.append(descriptor_record)
        payloads.append(A._common_payload(
            workload=workload,
            generation=1,
            descriptor=descriptor,
            descriptor_record=descriptor_record,
            arm="off",
        ))
        assert descriptor_record == before

    assert A._canonical_json_bytes(payloads[0]) == A._canonical_json_bytes(
        payloads[1]
    )
    assert payloads[0]["workload"] == A.OFF_NEUTRAL_PAYLOAD_WORKLOAD
    assert payloads[1]["workload"] == A.OFF_NEUTRAL_PAYLOAD_WORKLOAD
    for payload in payloads:
        assert "arm_binding_digest_sha256" not in payload[
            "descriptor_binding"
        ]
        assert payload["descriptor_binding"]["content_digest_sha256"]
    assert records[0]["arm_binding_digest_sha256"] != (
        records[1]["arm_binding_digest_sha256"]
    )

    on_payloads = []
    swapped_payloads = []
    for holdout, workload in (("H1", "rr80"), ("H2", "rr20")):
        for arm, destination in (
            ("on", on_payloads),
            ("swapped", swapped_payloads),
        ):
            resolved = A.s8c_arm_inputs.resolve_arm_input(
                arm=arm,
                holdout=holdout,
                repository_root=t325_registered_trial.repo,
                commit=commit,
            )
            descriptor, descriptor_record = (
                A._descriptor_from_resolved_arm_input(resolved)
            )
            destination.append(A._common_payload(
                workload=workload,
                generation=1,
                descriptor=descriptor,
                descriptor_record=descriptor_record,
                arm=arm,
            ))
    assert A._canonical_json_bytes(on_payloads[0]) != A._canonical_json_bytes(
        on_payloads[1]
    )
    assert A._canonical_json_bytes(swapped_payloads[0]) != (
        A._canonical_json_bytes(swapped_payloads[1])
    )


def test_off_invocation_id_is_holdout_invariant(t325_registered_trial) -> None:
    commit = _t325_git(t325_registered_trial.repo, "rev-parse", "HEAD")
    provider_ids = []
    audit_ids = []
    for holdout, workload in (("H1", "rr80"), ("H2", "rr20")):
        resolved = A.s8c_arm_inputs.resolve_arm_input(
            arm="off",
            holdout=holdout,
            repository_root=t325_registered_trial.repo,
            commit=commit,
        )
        _descriptor, descriptor_record = A._descriptor_from_resolved_arm_input(
            resolved
        )
        provider_id, audit_id = A._provider_and_audit_invocation_ids(
            arm="off",
            arm_binding_digest=descriptor_record[
                "arm_binding_digest_sha256"
            ],
            content_digest=descriptor_record["content_digest_sha256"],
            workload=workload,
            generation=1,
            role="planner",
        )
        provider_ids.append(provider_id)
        audit_ids.append(audit_id)
    assert provider_ids[0] == provider_ids[1]
    assert audit_ids[0] != audit_ids[1]
    assert A.OFF_NEUTRAL_PAYLOAD_WORKLOAD in provider_ids[0]
    assert "rr80" not in provider_ids[0]
    assert "rr20" not in provider_ids[0]
    assert audit_ids[0].endswith(".rr80.g1.planner")
    assert audit_ids[1].endswith(".rr20.g1.planner")


def test_off_payload_audit_digest_is_retained_outside_payload(
    tmp_path, t325_registered_trial,
) -> None:
    commit = _t325_git(t325_registered_trial.repo, "rev-parse", "HEAD")
    resolved = A.s8c_arm_inputs.resolve_arm_input(
        arm="off",
        holdout="H1",
        repository_root=t325_registered_trial.repo,
        commit=commit,
    )
    descriptor, descriptor_record = A._descriptor_from_resolved_arm_input(
        resolved
    )
    payload = A._common_payload(
        workload="rr80",
        generation=1,
        descriptor=descriptor,
        descriptor_record=descriptor_record,
        arm="off",
    )
    payload.update({
        "working_diff": "fixture diff",
        "diff_digest": hashlib.sha256(b"fixture diff").hexdigest(),
    })
    provider_id, audit_id = A._provider_and_audit_invocation_ids(
        arm="off",
        arm_binding_digest=descriptor_record[
            "arm_binding_digest_sha256"
        ],
        content_digest=descriptor_record["content_digest_sha256"],
        workload="rr80",
        generation=1,
        role="auditor",
    )
    provider = _ArtifactRecordingFixture("auditor", tmp_path / "provider")
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    journal = A.AttemptJournal(tmp_path / "attempts.jsonl")
    parsed, event = A._invoke(
        role="auditor",
        provider=provider,
        invocation_id=provider_id,
        audit_invocation_id=audit_id,
        audit_arm_binding_digest_sha256=descriptor_record[
            "arm_binding_digest_sha256"
        ],
        payload=payload,
        raw_root=raw_root,
        journal=journal,
        workload="rr80",
        generation=1,
    )
    assert parsed is not None
    assert provider.invocation_ids == [provider_id]
    received = provider.payloads[0]
    assert "arm_binding_digest_sha256" not in received[
        "descriptor_binding"
    ]
    assert event["invocation_id"] == audit_id
    assert event["arm_binding_digest_sha256"] == descriptor_record[
        "arm_binding_digest_sha256"
    ]
    assert event["provider_artifacts"]["arm_binding_digest_sha256"] == (
        descriptor_record["arm_binding_digest_sha256"]
    )
    assert Path(event["provider_artifacts"]["payload_path"]).name == (
        f"payload_{provider_id}.json"
    )
    assert descriptor_record["arm_binding_digest_sha256"] not in (
        Path(event["provider_artifacts"]["payload_path"]).name
    )


def test_off_pre_audit_skip_retains_audit_binding(
    tmp_path, t325_registered_trial,
) -> None:
    admission = A.trial_registry.admit_registered_launch(
        effective_preregistration=t325_registered_trial.capability,
        manifest_path=t325_registered_trial.manifest_path,
        trial_id="t325-h1-off",
        workloads=["rr80"],
        repository_root=t325_registered_trial.repo,
        registry_path=t325_registered_trial.registry_path,
    )
    arm_execution = A.trial_registry.bind_trial_arm(
        admission.binding,
        repository_root=t325_registered_trial.repo,
    )
    run_root = tmp_path / "off-pre-audit-skip"
    (run_root / "raw").mkdir(parents=True)
    (run_root / "proposals").mkdir()
    journal = A.AttemptJournal(run_root / "attempts.jsonl")

    def rejected_preview(coder, *, sub):
        result = _fake_preview(coder, sub=sub)
        result["passed"] = False
        result["forbidden_identifiers"] = ["fixture-forbidden-identifier"]
        return result

    def stop_after_first_generation(*args, **kwargs):
        outcome = _fake_drive(*args, **kwargs)
        outcome["stop_reason"] = "budget-iterations"
        return outcome

    scope = A._RunScopeBinding(
        admission,
        A._RUN_SCOPE_SEAL,
        None,
        arm_execution,
    )
    token = A._ACTIVE_TRIAL_BINDING.set(scope)
    try:
        cell = A._run_workload(
            workload="rr80",
            generations=2,
            providers={
                role: A.FixtureRoleProvider(role) for role in A.ROLE_FILES
            },
            journal=journal,
            run_root=run_root,
            sub="/unused",
            do_build=False,
            cache_root="",
            trial_id="t325-h1-off",
            started_monotonic=time.monotonic(),
            max_wall_s=3600,
            drive=stop_after_first_generation,
            preview=rejected_preview,
            build_context=_no_build_context(),
            gating_spec_snapshot=A.snapshot_gating_spec(A.GATING_SPEC),
        )
    finally:
        A._ACTIVE_TRIAL_BINDING.reset(token)

    event = cell["generations"][0]["roles"]["auditor"]
    assert event["status"] == "skipped"
    assert event["skip_reason"] == "machine-pre-audit-rejection"
    content_digest = cell["descriptor_binding"]["content_digest_sha256"]
    arm_digest = arm_execution.arm_binding_digest_sha256
    provider_id, audit_id = A._provider_and_audit_invocation_ids(
        arm="off",
        arm_binding_digest=arm_digest,
        content_digest=content_digest,
        workload="rr80",
        generation=1,
        role="auditor",
    )
    assert event["invocation_id"] == audit_id
    assert event["invocation_id"] != provider_id
    assert event["invocation_id"].endswith(".rr80.g1.auditor")
    assert f".exec-{arm_digest}." in event["invocation_id"]
    assert event["arm_binding_digest_sha256"] == arm_digest


def test_off_critic_payload_does_not_reintroduce_campaign_identity(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    commit = _t325_git(t325_registered_trial.repo, "rev-parse", "HEAD")
    resolved = A.s8c_arm_inputs.resolve_arm_input(
        arm="off",
        holdout="H1",
        repository_root=t325_registered_trial.repo,
        commit=commit,
    )
    descriptor, descriptor_record = A._descriptor_from_resolved_arm_input(
        resolved
    )
    arm_binding = A.trial_registry.load_launch_binding(
        manifest_path=t325_registered_trial.manifest_path,
        trial_id="t325-h1-off",
        workloads=["rr80"],
        repository_root=t325_registered_trial.repo,
        registry_path=t325_registered_trial.registry_path,
    )
    arm_execution = A.trial_registry.bind_trial_arm(
        arm_binding,
        repository_root=t325_registered_trial.repo,
    )
    monkeypatch.setattr(
        A, "_active_arm_execution", lambda *, workload: arm_execution,
    )

    def run_case(
        case_root: Path, *, digest_generated: bool, raw_variant: str | None,
    ):
        common = A._common_payload(
            workload="rr80",
            generation=1,
            descriptor=descriptor,
            descriptor_record=descriptor_record,
            arm="off",
        )
        run_root = case_root / "run"
        (run_root / "raw").mkdir(parents=True)
        campaign_root = run_root / "campaign"
        campaign_root.mkdir()
        actual_digest = "d" * 64
        if digest_generated:
            (campaign_root / A.trigger.DIGEST_BASENAME).write_text(
                actual_digest, encoding="utf-8",
            )
            monkeypatch.setattr(
                A, "require_admitted_campaign",
                lambda *args, **kwargs: object(),
            )
            monkeypatch.setattr(
                A.loop_core,
                "make_critic_identity_projection",
                lambda _view: SimpleNamespace(
                    project_variant=lambda _variant: "campaign-candidate",
                ),
            )
            monkeypatch.setattr(
                A.loop_core,
                "make_critic_digest",
                lambda *args, **kwargs: actual_digest,
            )
        journal = A.AttemptJournal(run_root / "attempts.jsonl")
        accounting = A._new_generation_accounting(
            workload="rr80",
            generation=1,
            journal=journal,
            generation_driver=dict(A._STANDARD_GENERATION_DRIVER),
            gating_spec_sha256="a" * 64,
            authority=A._AUTHORITATIVE_ACCOUNTING,
        )
        cell = {
            "workload": "rr80",
            "campaign_root": str(campaign_root),
            "generations": [{"generation": 1, "roles": {}}],
            "_pending_critics": [{
                "generation": 1,
                "common": common,
                "outcome": {
                    "outcome": "certified",
                    "verdict": "pass",
                    "stop_reason": "continue",
                },
                "metrics": {"throughput_tps": 1.0},
                "raw_variant": raw_variant,
                "critic_digest_generated": digest_generated,
                "critic_attempted": False,
                "accounting": accounting,
            }],
        }
        provider = _RecordingFixture("critic")
        critic = A._run_one_pending_critic(
            cell,
            providers={"critic": provider},
            journal=journal,
            run_root=run_root,
            transport_receipt=None,
            require_recomputed_digest=digest_generated,
        )
        return critic, provider.payloads[0]

    generated_critic, generated_payload = run_case(
        tmp_path / "generated",
        digest_generated=True,
        raw_variant="candidate-0001",
    )
    raw_critic, raw_payload = run_case(
        tmp_path / "raw",
        digest_generated=False,
        raw_variant="candidate-0001",
    )
    assert generated_critic is not None
    assert raw_critic is not None
    for payload in (generated_payload, raw_payload):
        assert payload["critic_digest"] is None
        assert payload["harness_result"]["candidate_label"] is None
        assert "arm_binding_digest_sha256" not in payload[
            "descriptor_binding"
        ]
    assert generated_payload["harness_result"]["metrics"] == {
        "throughput_tps": 1.0,
    }


def test_generation_one_never_uses_intermediate_critic_projection(
    tmp_path, monkeypatch,
) -> None:
    def forbidden_projection(*args, **kwargs):
        pytest.fail("generation=1 reached intermediate critic projection")

    monkeypatch.setattr(A, "apply_critic_feedback", forbidden_projection)
    report = A.run_trial(
        trial_id="generation-one-no-intermediate-critic",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "complete"


def test_role_payload_validators_are_immediately_before_provider_invoke_by_ast(
) -> None:
    tree = ast.parse(Path(A.__file__).read_text(encoding="utf-8"))
    run_workload = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_run_workload"
    )
    body = next(
        node.body
        for node in ast.walk(run_workload)
        if isinstance(node, ast.For)
        and isinstance(node.target, ast.Name)
        and node.target.id == "generation"
    )
    for role, validator in (
        ("planner", "validate_planner_payload"),
        ("coder", "validate_coder_payload"),
    ):
        invoke_index = next(
            index for index, statement in enumerate(body)
            if isinstance(statement, ast.Assign)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
            and statement.value.func.id == "_invoke"
            and any(
                keyword.arg == "role"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value == role
                for keyword in statement.value.keywords
            )
        )
        prior = body[invoke_index - 1]
        assert isinstance(prior, ast.Assign)
        assert isinstance(prior.value, ast.Call)
        assert isinstance(prior.value.func, ast.Name)
        assert prior.value.func.id == validator


def test_intermediate_critic_projection_failure_is_at_most_once(
    tmp_path, monkeypatch,
) -> None:
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }

    def fail_after_critic(*args, **kwargs):
        raise RuntimeError("fixture projection failure")

    monkeypatch.setattr(A, "apply_critic_feedback", fail_after_critic)
    report = A.run_trial(
        trial_id="critic-projection-at-most-once",
        workloads=["ycsb-a"],
        generations=2,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "partial"
    assert len(providers["critic"].payloads) == 1
    assert report["honest_accounting"]["role_query_count"] == 4


def test_pending_critic_reentry_is_blocked_by_attempt_flag_while_still_queued(
    tmp_path,
) -> None:
    run_root = tmp_path / "critic-reentry"
    (run_root / "raw").mkdir(parents=True)
    journal = A.AttemptJournal(run_root / "attempts.jsonl")
    accounting = A._new_generation_accounting(
        workload="ycsb-a",
        generation=1,
        journal=journal,
        generation_driver={
            "wrapper": "s8c-generation/v1",
            "delegate": "caller-injected-unsupported",
        },
        gating_spec_sha256=hashlib.sha256(
            A.GATING_SPEC.encode("utf-8")
        ).hexdigest(),
        authority="excluded-caller-injected-unsupported",
    )
    cell = {
        "workload": "ycsb-a",
        "campaign_root": str(run_root / "campaign"),
        "generations": [{"generation": 1, "roles": {}}],
        "stop_reason": "fixed-generation-budget",
        "_pending_critics": [{
            "generation": 1,
            "common": {
                "generation": 1,
                "descriptor_binding": {"output_sha256": "d" * 64},
            },
            "outcome": {
                "outcome": "dry-pass",
                "verdict": None,
                "stop_reason": "continue",
            },
            "metrics": dict(A._INITIAL_ROLE_METRICS),
            "raw_variant": None,
            "critic_digest_generated": False,
            "critic_attempted": False,
            "accounting": accounting,
        }],
    }

    class ReentrantCritic(A.FixtureRoleProvider):
        def __init__(self):
            super().__init__("critic")
            self.calls = 0
            self.reentry_error = None

        def invoke(self, *, invocation_id, payload):
            self.calls += 1
            assert cell["_pending_critics"]
            try:
                A._run_one_pending_critic(
                    cell,
                    providers={"critic": self},
                    journal=journal,
                    run_root=run_root,
                    transport_receipt=None,
                )
            except A.AutonomousTrialError as exc:
                self.reentry_error = str(exc)
            else:  # pragma: no cover - mutation must make this branch reachable
                pytest.fail("reentrant critic was not rejected")
            return super().invoke(invocation_id=invocation_id, payload=payload)

    provider = ReentrantCritic()
    critic = A._run_one_pending_critic(
        cell,
        providers={"critic": provider},
        journal=journal,
        run_root=run_root,
        transport_receipt=None,
    )
    assert critic is not None
    assert provider.calls == 1
    assert provider.reentry_error == "pending critic の二重 attempt を拒否"
    assert "_pending_critics" not in cell


def test_duplicate_records_contribute_zero_current_attempt_bench() -> None:
    assert A._bench_wall_seconds(
        {
            "outcome": "duplicate",
            "ran": True,
            "records": {"bench_done": {"bench_wall_s": 123.0}},
        },
        authoritative=True,
    ) == 0.0


def test_bench_accounting_uses_only_pipeline_bench_record() -> None:
    assert A._bench_wall_seconds(
        {
            "outcome": "certified",
            "ran": True,
            "bench_wall_s": 999.0,
            "records": {"bench_done": {"bench_wall_s": 7.5}},
        },
        authoritative=True,
    ) == 7.5


@pytest.mark.parametrize(
    ("outcome", "ran", "authoritative"),
    [
        ("certified", True, False),
        ("dry-pass", True, True),
        ("rejected", True, True),
        ("stopped-before", False, True),
    ],
)
def test_non_authoritative_and_prebench_branches_account_zero(
    outcome, ran, authoritative,
) -> None:
    assert A._bench_wall_seconds(
        {
            "outcome": outcome,
            "ran": ran,
            "records": {"bench_done": {"bench_wall_s": 7.5}},
        },
        authoritative=authoritative,
    ) == 0.0


def test_zero_work_wall_stop_accounts_before_terminal_event(
    tmp_path, monkeypatch,
) -> None:
    ticks = iter((0.0, 0.0, 61.0))
    monkeypatch.setattr(A.time, "monotonic", lambda: next(ticks, 61.0))
    report = A.run_trial(
        trial_id="zero-work-wall-accounting",
        workloads=["ycsb-a"],
        generations=2,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        max_wall_s=60,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    events = [
        json.loads(line)
        for line in (tmp_path / "run" / "attempts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert [event["event"] for event in events] == [
        "run-start",
        "supervisor-wall-budget",
        "run-finish",
    ]
    assert events[1]["generation"] == 1
    assert events[1]["zero_work"] is True
    assert events[1]["role_query_count"] == 0
    assert events[1]["bench_wall_seconds"] == 0.0
    assert report["honest_accounting"] == {
        "role_query_count": 0,
        "bench_wall_seconds": 0.0,
    }


def test_stale_digest_is_not_reused_when_generation_reports_no_digest(
    tmp_path,
) -> None:
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }

    def stale_drive(*args, layout, **kwargs):
        outcome = _fake_drive(*args, layout=layout, **kwargs)
        Path(layout.root, A.trigger.DIGEST_BASENAME).write_text(
            "stale-digest", encoding="utf-8",
        )
        return outcome

    report = A.run_trial(
        trial_id="stale-digest-not-reused",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=stale_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "complete"
    assert providers["critic"].payloads[0]["critic_digest"] is None


def test_intermediate_critic_digest_mismatch_fails_closed(tmp_path) -> None:
    providers = {
        role: (
            _WireRecordingFixture(role, wire="00000")
            if role == "coder"
            else _RecordingFixture(role)
        )
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="intermediate-critic-digest-mismatch",
        workloads=["ycsb-a"],
        generations=2,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_drive_with_raw_identity_digest,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    assert report["status"] == "partial"
    assert report["fatal_error"] == {
        "type": "AutonomousTrialError",
        "message": "critic digest が admitted campaign の再計算値と一致しない",
    }
    assert providers["critic"].payloads == []


def test_final_generation_critic_rebuilds_projected_digest(
    tmp_path, monkeypatch,
) -> None:
    calls = []
    original = A.loop_core.make_critic_digest

    def recording_digest(*args, **kwargs):
        calls.append(kwargs["identity_projection"])
        return original(*args, **kwargs)

    monkeypatch.setattr(A.loop_core, "make_critic_digest", recording_digest)
    providers = {
        role: (
            _WireRecordingFixture(role, wire="00000")
            if role == "coder"
            else _RecordingFixture(role)
        )
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="final-critic-rebuilt-projected-digest",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_drive_with_raw_identity_digest,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )

    persisted = Path(
        report["cells"][0]["campaign_root"], A.trigger.DIGEST_BASENAME,
    ).read_text(encoding="utf-8")
    critic_view = A.require_admitted_campaign(
        report["cells"][0]["campaign_root"],
        purpose=A.CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )
    identity_projection = A.loop_core.make_critic_identity_projection(
        critic_view,
    )
    cfg = A.trigger.default_cfg(reflux=True)
    rebuilt = original(
        critic_view,
        tag=A.trigger.CRITIC_TAG,
        reflux=(cfg.search_config.get("reflux") == "on"),
        identity_projection=identity_projection,
    )
    critic_payload = providers["critic"].payloads[0]
    assert report["status"] == "complete"
    assert len(calls) == 2
    assert calls[0] is A.loop_core.IdentityProjection.RAW
    assert critic_payload["harness_result"]["candidate_label"] == "candidate-0001"
    assert critic_payload["critic_digest"] == rebuilt
    assert critic_payload["critic_digest"] != persisted


def test_generated_digest_must_exist_before_critic(tmp_path) -> None:
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }

    def missing_digest_drive(*args, **kwargs):
        outcome = _fake_drive(*args, **kwargs)
        outcome["critic_digest_generated"] = True
        return outcome

    report = A.run_trial(
        trial_id="generated-digest-missing",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=missing_digest_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "partial"
    assert report["fatal_error"]["type"] == "AutonomousTrialError"
    assert providers["critic"].payloads == []
    events = [
        json.loads(line)
        for line in (tmp_path / "run" / "attempts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    accounting_index = next(
        index for index, event in enumerate(events)
        if event["event"] == "generation-accounting"
    )
    terminal_index = next(
        index for index, event in enumerate(events)
        if event["event"] == "supervisor-error"
    )
    assert accounting_index < terminal_index
    assert events[accounting_index]["state"] == "pending-pre-invoke-failure"
    assert events[accounting_index]["provider_invoke_count"] == 3


def test_all_workloads_share_one_gating_spec_snapshot(tmp_path, monkeypatch) -> None:
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    original = A.GATING_SPEC
    calls = 0

    def mutating_drive(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            monkeypatch.setattr(A, "GATING_SPEC", "mutated-after-run-snapshot")
        return _fake_drive(*args, **kwargs)

    report = A.run_trial(
        trial_id="run-scope-gating-snapshot",
        workloads=["ycsb-a", "ycsb-b"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=mutating_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert [payload["gating_spec"] for payload in providers["coder"].payloads] == [
        original,
        original,
    ]
    assert report["gating_spec_sha256"] == hashlib.sha256(
        original.encode("utf-8")
    ).hexdigest()


def test_internal_trial_entries_require_exact_gating_spec_snapshot() -> None:
    for entry in (A._finish_trial, A._run_workload):
        parameter = inspect.signature(entry).parameters["gating_spec_snapshot"]
        assert parameter.default is inspect.Parameter.empty
        assert parameter.annotation in {
            "GatingSpecSnapshot", A.GatingSpecSnapshot,
        }


def test_direct_run_workload_defers_critic_to_finish_trial(tmp_path) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    for child in ("raw", "proposals"):
        (run_root / child).mkdir()
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }

    result = _run_workload_with_scope(
        workload="ycsb-a",
        generations=1,
        providers=providers,
        journal=A.AttemptJournal(run_root / "attempts.jsonl"),
        run_root=run_root,
        sub="/unused",
        do_build=False,
        cache_root="",
        trial_id="direct-defers-critic",
        started_monotonic=time.monotonic(),
        max_wall_s=60,
        drive=_fake_drive,
        preview=_fake_preview,
        build_context=_no_build_context(),
    )

    assert providers["critic"].payloads == []
    assert len(result["_pending_critics"]) == 1
    pending = result["_pending_critics"][0]
    assert set(pending) == {
        "generation", "common", "outcome", "metrics", "raw_variant",
        "critic_digest_generated", "critic_attempted", "accounting",
    }
    assert pending == {
        "generation": 1,
        "common": {
            "schema_version": "p3-autonomous-workload-trial/v4",
            "pilot_scope": "exploratory-ycsb-abc",
            "scientific_claim": False,
            "workload": "ycsb-a",
            "generation": 1,
            "workload_descriptor": result["descriptor"],
            "descriptor_binding": result["descriptor_binding"],
            "attempt_policy": {
                "attempts_per_role_generation": 1,
                "retry": False,
            },
            "stop_policy": {
                "performance_early_stop": False,
                "generation_budget_is_fixed": True,
            },
        },
        "outcome": {
            "outcome": "dry-pass",
            "variant": None,
            "stop_reason": "continue",
            "iteration": 1,
            "ran": True,
            "trigger_gate_binding_commitment": "b" * 64,
            "critic_digest_generated": False,
        },
        "metrics": {
            "throughput_tps": None,
            "abort_rate": None,
            "latency_ns": None,
            "llc_miss_rate": None,
            "ipc": None,
        },
        "raw_variant": None,
        "critic_digest_generated": False,
        "critic_attempted": False,
        "accounting": {
            "workload": "ycsb-a",
            "generation": 1,
            "state": "partial-generation",
            "role_query_start": 0,
            "auditor_pre_audit_skipped": False,
            "bench_wall_seconds": 0.0,
            "generation_driver": {
                "wrapper": "s8c-generation/v1",
                "delegate": "caller-injected-unsupported",
            },
            "gating_spec_sha256": hashlib.sha256(
                A.GATING_SPEC.encode("utf-8")
            ).hexdigest(),
            "accounting_authority": "excluded-caller-injected-unsupported",
            "finalized": False,
        },
    }
    assert set(result["generations"][0]["roles"]) == {
        "planner", "coder", "auditor",
    }


def test_run_workload_no_build_stays_trial_local(tmp_path) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    for child in ("raw", "proposals"):
        (run_root / child).mkdir()
    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    result = _run_workload_with_scope(
        workload="ycsb-a",
        generations=1,
        providers=providers,
        journal=A.AttemptJournal(run_root / "attempts.jsonl"),
        run_root=run_root,
        sub="/unused",
        do_build=False,
        cache_root="",
        trial_id="no-build-trial-local",
        started_monotonic=time.monotonic(),
        max_wall_s=60,
        drive=_fake_drive,
        preview=_fake_preview,
        build_context=_no_build_context(),
    )

    assert Path(result["campaign_root"]) == (
        run_root / "campaigns" / result["campaign_id"]
    )


def test_freshness_wraps_malformed_json_with_cause(tmp_path) -> None:
    layout = A.CampaignLayout(str(tmp_path / "campaign"))
    layout.ensure()
    Path(A.loop_core.loop_state_path(layout)).write_text(
        "{broken", encoding="utf-8"
    )
    with pytest.raises(A.AutonomousTrialError) as caught:
        A._assert_fresh_campaign_state(layout)
    assert type(caught.value.__cause__) is json.JSONDecodeError


def test_freshness_wraps_delta_pct_leak_with_cause(tmp_path) -> None:
    layout = A.CampaignLayout(str(tmp_path / "campaign"))
    state = A.loop_core.LoopState(
        whiteboard=[
            A.loop_core.WhiteboardEntry(
                iteration=1,
                direction="increase",
                magnitude="small",
                result="fail",
                delta_pct=1.0,
            )
        ]
    )
    A.loop_core.save_loop_state(layout, state)
    with pytest.raises(A.AutonomousTrialError) as caught:
        A._assert_fresh_campaign_state(layout)
    assert type(caught.value.__cause__) is A.loop_core.WhiteboardLeakError


def test_freshness_does_not_reclassify_attribute_error(
    tmp_path, monkeypatch,
) -> None:
    layout = A.CampaignLayout(str(tmp_path / "campaign"))

    def broken_loader(_layout):
        raise AttributeError("loader programming error")

    monkeypatch.setattr(A.loop_core, "load_loop_state", broken_loader)
    with pytest.raises(AttributeError, match="loader programming error"):
        A._assert_fresh_campaign_state(layout)


def test_supervisor_error_still_writes_partial_terminal_report(tmp_path) -> None:
    def broken_preview(coder, *, sub):
        raise RuntimeError("preview fixture failure")

    run_root = tmp_path / "run"
    report = A.run_trial(
        trial_id="supervisor-error",
        workloads=["ycsb-a", "ycsb-b"],
        generations=1,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        drive=_fake_drive,
        preview=broken_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "partial"
    assert report["fatal_error"] == {
        "type": "RuntimeError",
        "message": "preview fixture failure",
    }
    assert report["cells"][0]["stop_reason"] == "supervisor-error"
    assert "lifecycle_terminal_status" not in report
    assert (run_root / "report.json").is_file()
    events = [
        json.loads(line)
        for line in (run_root / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [event["event"] for event in events][-2:] == [
        "supervisor-error",
        "run-finish",
    ]


def test_unknown_custom_drive_identity_uses_fixed_sentinel_and_stays_complete(
    tmp_path,
) -> None:
    """exploratory drive の非 WAL ID は raw でなく固定 label へ射影する。"""
    def unknown_drive(
        cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
        cache_root="", proposal_path="", extra_sources=(),
    ):
        assert do_build is False
        layout.ensure()
        return {
            "outcome": "certified",
            "variant": "custom-without-build-start",
            "fitness_tps": 1.0,
            "stop_reason": "continue",
            "iteration": 1,
            "ran": True,
            "trigger_gate_binding_commitment": "b" * 64,
            "critic_digest_generated": False,
        }

    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="unknown-custom-drive-identity",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=unknown_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "complete"
    assert "fatal_error" not in report
    assert len(providers["critic"].payloads) == 1
    critic_payload = providers["critic"].payloads[0]
    assert critic_payload["harness_result"]["candidate_label"] == (
        A.loop_core.UNREGISTERED_CANDIDATE_LABEL
    )
    assert "custom-without-build-start" not in json.dumps(
        critic_payload, sort_keys=True,
    )
    events = [
        json.loads(line)
        for line in (tmp_path / "run" / "attempts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert any(
        event.get("event") == "role-attempt" and event.get("role") == "critic"
        for event in events
    )
    assert events[-1]["event"] == "run-finish"


@pytest.mark.parametrize("outcome", ["success", "supervisor-error"])
def test_run_trial_closes_owned_providers_in_reverse_order(
    tmp_path, monkeypatch, outcome,
) -> None:
    close_order: list[str] = []
    owned = {
        role: _ClosableRecordingFixture(role, close_order)
        for role in ("planner", "coder", "auditor", "critic")
    }
    monkeypatch.setattr(A, "_provider_set", lambda **kwargs: owned)

    def preview(coder, *, sub):
        if outcome == "supervisor-error":
            raise RuntimeError("preview failure")
        return _fake_preview(coder, sub=sub)

    report = A.run_trial(
        trial_id=f"owned-{outcome}",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        drive=_fake_drive,
        preview=preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == ("complete" if outcome == "success" else "partial")
    assert close_order == ["critic", "auditor", "coder", "planner"]
    assert all(provider.close_calls == 1 for provider in owned.values())


def test_run_trial_does_not_close_injected_providers(tmp_path) -> None:
    providers = {
        role: _ClosableRecordingFixture(role)
        for role in ("planner", "coder", "auditor", "critic")
    }
    report = A.run_trial(
        trial_id="injected-ownership",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "run",
        sub="/unused",
        do_build=False,
        providers=providers,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "complete"
    assert all(provider.close_calls == 0 for provider in providers.values())
    assert providers["coder"].payloads[0]["workload"] == "ycsb-a"


def test_provider_set_closes_partial_projected_provider_set_in_reverse_order(
    tmp_path, monkeypatch,
) -> None:
    close_order: list[str] = []
    constructed: list[str] = []

    class _PartialProvider:
        def __init__(self, role):
            self.role = role

        def close(self):
            close_order.append(self.role)

    def provider_factory(**kwargs):
        role = tuple(A.ROLE_FILES)[len(constructed)]
        constructed.append(role)
        if role == "auditor":
            raise RuntimeError("partial construction failure")
        return _PartialProvider(role)

    monkeypatch.setattr(A, "ClaudeProjectedRoleProvider", provider_factory)
    with pytest.raises(RuntimeError, match="partial construction failure"):
        A._provider_set(
            kind="claude-headless",
            run_root=tmp_path / "run",
            executable="unused",
        )
    assert constructed == ["planner", "coder", "auditor"]
    assert close_order == ["coder", "planner"]


def test_main_rejects_fixture_build_before_build_preparation(
    tmp_path, monkeypatch,
) -> None:
    def unexpected_build_preparation(*args, **kwargs):
        pytest.fail("fixture build rejection reached build preparation")

    monkeypatch.setattr(
        calibrator_runner, "competing_bench_pids", unexpected_build_preparation
    )
    monkeypatch.setattr(A, "checkout", unexpected_build_preparation)
    run_root = tmp_path / "run"
    ccbench_dir = tmp_path / "ccbench"

    with pytest.raises(A.AutonomousTrialError):
        A.main([
            "--trial-id", "fixture-build-rejected",
            "--provider", "fixture",
            "--ccbench-dir", str(ccbench_dir),
            "--run-root", str(run_root),
        ])

    assert not run_root.exists()
    assert not ccbench_dir.exists()


def test_main_rejects_unapproved_budget_before_build_preparation(
    tmp_path, monkeypatch,
) -> None:
    def unexpected_build_preparation(*args, **kwargs):
        pytest.fail("budget rejection reached build preparation")

    monkeypatch.setattr(A, "assert_pinned_clean", unexpected_build_preparation)
    monkeypatch.setattr(A, "checkout", unexpected_build_preparation)
    monkeypatch.setattr(
        calibrator_runner, "competing_bench_pids", unexpected_build_preparation
    )
    run_root = tmp_path / "run"
    ccbench_dir = tmp_path / "ccbench"
    with pytest.raises(A.AutonomousTrialError, match="承認済み上限"):
        A.main([
            "--trial-id", "unapproved-cli-budget",
            "--provider", "claude-headless",
            "--max-generations", "3",
            "--ccbench-dir", str(ccbench_dir),
            "--run-root", str(run_root),
        ])
    assert not run_root.exists()
    assert not ccbench_dir.exists()


def test_main_default_generation_budget_is_one(tmp_path, monkeypatch) -> None:
    def stop_after_cli_gate(*args, **kwargs):
        raise _CliGateReached

    monkeypatch.setattr(A, "assert_pinned_clean", stop_after_cli_gate)
    with pytest.raises(_CliGateReached):
        A.main([
            "--trial-id", "fixture-no-build-accepted",
            "--provider", "fixture",
            "--no-build",
            "--allow-unregistered-exploratory",
            "--ccbench-dir", str(tmp_path / "ccbench"),
            "--run-root", str(tmp_path / "run"),
        ])


def test_main_rejects_claude_headless_build_outside_other_before_preparation(
    tmp_path, monkeypatch,
) -> None:
    monkeypatch.setattr(
        A.trigger, "_current_site",
        lambda: A.trigger.site_policy.PEGASUS_COMPUTE,
    )

    def unexpected_preparation():
        pytest.fail("8c compute rejection reached measurement preparation")

    monkeypatch.setattr(calibrator_runner, "competing_bench_pids", unexpected_preparation)
    run_root = tmp_path / "run"
    with pytest.raises(A.AutonomousTrialError, match="T-276"):
        A.main([
            "--trial-id", "claude-build-accepted",
            "--provider", "claude-headless",
            "--ccbench-dir", str(tmp_path / "ccbench"),
            "--run-root", str(run_root),
        ])
    assert not run_root.exists()


def test_main_accepts_claude_headless_no_build_at_cli_gate(
    tmp_path, monkeypatch,
) -> None:
    def stop_after_cli_gate(*args, **kwargs):
        raise _CliGateReached

    monkeypatch.setattr(A, "assert_pinned_clean", stop_after_cli_gate)
    with pytest.raises(_CliGateReached):
        A.main([
            "--trial-id", "claude-no-build-accepted",
            "--provider", "claude-headless",
            "--no-build",
            "--allow-unregistered-exploratory",
            "--ccbench-dir", str(tmp_path / "ccbench"),
            "--run-root", str(tmp_path / "run"),
        ])


def test_main_default_run_root_is_exploration_autonomous_trials(
    tmp_path, monkeypatch,
) -> None:
    captured = {}
    monkeypatch.setattr(A, "assert_pinned_clean", lambda *args, **kwargs: None)

    def capture_run_trial(**kwargs):
        captured.update(kwargs)
        return {"status": "complete", "cells": []}

    monkeypatch.setattr(A, "run_trial", capture_run_trial)
    assert A.main([
        "--trial-id", "default-exploration-root",
        "--provider", "fixture",
        "--no-build",
        "--allow-unregistered-exploratory",
        "--ccbench-dir", str(tmp_path / "ccbench"),
    ]) == 0
    assert captured["run_root"] == (
        A.ROOT
        / "output"
        / "exploration"
        / "autonomous-trials"
        / "default-exploration-root"
    )


def test_main_explicit_run_root_still_wins(tmp_path, monkeypatch) -> None:
    captured = {}
    explicit = tmp_path / "explicit-run-root"
    monkeypatch.setattr(A, "assert_pinned_clean", lambda *args, **kwargs: None)

    def capture_run_trial(**kwargs):
        captured.update(kwargs)
        return {"status": "complete", "cells": []}

    monkeypatch.setattr(A, "run_trial", capture_run_trial)
    assert A.main([
        "--trial-id", "explicit-root",
        "--provider", "fixture",
        "--no-build",
        "--allow-unregistered-exploratory",
        "--ccbench-dir", str(tmp_path / "ccbench"),
        "--run-root", str(explicit),
    ]) == 0
    assert captured["run_root"] == explicit


def test_main_help_names_exploration_autonomous_trials(capsys) -> None:
    with pytest.raises(SystemExit) as caught:
        A.main(["--help"])
    assert caught.value.code == 0
    help_text = capsys.readouterr().out
    assert "output/exploration/autonomous-trials/<trial-id>" in help_text
    assert "output/autonomous-trials/<trial-id>" not in help_text


def _role_file(path: Path) -> Path:
    path.write_text(
        """---
name: fixture-auditor
description: "fixture role"
tools: ["Read", "Grep"]
model: opus
effort: high
---

Return the requested JSON.
""",
        encoding="utf-8",
    )
    return path


def _executable(path: Path) -> Path:
    executable = path / "claude"
    executable.write_bytes(b"#!/bin/sh\nexit 99\n")
    executable.chmod(0o755)
    return executable


def _envelope(*, server_calls: int = 0) -> dict:
    return {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 1,
        "permission_denials": [],
        "result": '{"verdict":"pass"}',
        "session_id": "fresh-session-1",
        "modelUsage": {
            "claude-opus-4-6": {"inputTokens": 10, "outputTokens": 5},
        },
        "usage": {"server_tool_use": {"web_search_requests": server_calls}},
    }


class _Runner:
    def __init__(self, envelope):
        self.envelope = envelope
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(self.envelope, separators=(",", ":")).encode(),
            stderr=b"",
        )


_T1354_TRANSPORT_MODES = ("opt-out", "opt-in")
_T1354_TRANSPORT_SNAPSHOT_KEYS = frozenset({
    "argv",
    "input",
    "cwd",
    "env",
    "timeout",
    "check",
    "stdout",
    "stderr",
})
_T1354_TRANSPORT_EXCLUSIONS = frozenset({
    "argv.mcp_config_path",
    "kwargs.cwd",
})
_T1354_EXCLUDED_VALUE = "<t1354-transport-metadata>"
_T1712_MCP_PATH_SENTINEL = b"<t1712-excluded-mcp-config-path>"
_T1712_CWD_SENTINEL = b"<t1712-excluded-neutral-cwd>"
_T1712_CONTROL_PARENT_CANARY = (
    "t1712-control-parent-canary-7c195e2f88c04f64"
)
_T1712_CONTROL_ROOT_CANARY = (
    "t1712-control-root-canary-2631fd7fa9db4b31"
)
_T1712_CONTROL_CWD_CANARY = (
    "t1712-control-cwd-canary-1d78e0c5b4a24f9e"
)
_T1712_TREATMENT_PARENT_CANARY = (
    "t1712-treatment-parent-canary-94a0b38dcebf42a1"
)
_T1712_TREATMENT_ROOT_CANARY = (
    "t1712-treatment-root-canary-b84e159236704cfd"
)
_T1712_TREATMENT_CWD_CANARY = (
    "t1712-treatment-cwd-canary-60fd3ecbcf0347a29e71"
)
_T1712_SHARED_INVOCATION_ID = "t1712.shared-launch-contract"


def _t1354_role_envelope(role: str, *, session_id: str) -> dict:
    if role == "planner":
        result = {
            "proposal": {
                "axis": A.trigger.MARKER_ID,
                "direction": "explore_both",
                "magnitude": "small",
                "justification": "fixture planner direction",
                "uncertainty": "fixture only",
            },
        }
    elif role == "coder":
        result = {
            "proposal": {
                "axis": A.trigger.MARKER_ID,
                "wire": "11111",
                "justification": "fixture coder proposal",
                "confidence": "low",
            },
        }
    elif role == "auditor":
        result = {
            "verdict": "pass",
            "diff_digest": hashlib.sha256(b"fixture diff").hexdigest(),
            "violations": [],
            "nits": [],
            "proposed_tests": [],
            "uncertainty": "fixture only",
        }
    else:  # pragma: no cover - caller is closed over three generation-1 roles
        raise AssertionError(f"unexpected T-1354 role: {role}")
    envelope = _envelope()
    envelope["result"] = A._canonical_json_bytes(result).decode("utf-8")
    envelope["session_id"] = session_id
    return envelope


def _t1354_runner_snapshot(runner: _Runner) -> dict[str, Any]:
    assert len(runner.calls) == 1
    argv, kwargs = runner.calls[0]
    assert type(argv) is list
    assert len(argv) == 19
    assert argv.count("--mcp-config") == 1
    assert argv.index("--mcp-config") == 16
    assert argv[-1] == "--no-session-persistence"
    assert set(kwargs) == {
        "input", "cwd", "env", "timeout", "check", "stdout", "stderr",
    }
    assert type(kwargs["input"]) is bytes
    assert type(kwargs["cwd"]) is str
    assert type(kwargs["env"]) is dict
    return {
        "argv": tuple(argv),
        "input": kwargs["input"],
        "cwd": kwargs["cwd"],
        "env": tuple(kwargs["env"].items()),
        "timeout": kwargs["timeout"],
        "check": kwargs["check"],
        "stdout": kwargs["stdout"],
        "stderr": kwargs["stderr"],
    }


def _t1354_normalize_transport_snapshot(
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    assert set(snapshot) == _T1354_TRANSPORT_SNAPSHOT_KEYS
    assert P.PROJECTED_PROVIDER_TRANSPORT_METADATA_EXCLUSIONS == (
        _T1354_TRANSPORT_EXCLUSIONS
    )
    assert set(P.PROJECTED_PROVIDER_TRANSPORT_METADATA_EXCLUSION_REASONS) == (
        _T1354_TRANSPORT_EXCLUSIONS
    )
    normalized = copy.deepcopy(snapshot)
    argv = list(normalized["argv"])
    assert len(argv) == 19
    assert argv.count("--mcp-config") == 1
    assert argv.index("--mcp-config") == 16
    assert type(normalized["input"]) is bytes
    assert type(normalized["cwd"]) is str
    assert type(normalized["env"]) is tuple
    assert all(
        type(item) is tuple
        and len(item) == 2
        and type(item[0]) is str
        and type(item[1]) is str
        for item in normalized["env"]
    )
    for field in sorted(P.PROJECTED_PROVIDER_TRANSPORT_METADATA_EXCLUSIONS):
        if field == "argv.mcp_config_path":
            argv[17] = _T1354_EXCLUDED_VALUE
        elif field == "kwargs.cwd":
            normalized["cwd"] = _T1354_EXCLUDED_VALUE
        else:  # pragma: no cover - exact production/test pins reject this first
            raise AssertionError(f"unknown transport exclusion: {field}")
    normalized["argv"] = tuple(argv)
    return normalized


def _t1712_launch_contract_observation(
    snapshot: dict[str, Any],
    *,
    validate_cli_layout: bool = True,
) -> dict[str, Any]:
    assert set(snapshot) == _T1354_TRANSPORT_SNAPSHOT_KEYS
    argv = snapshot["argv"]
    assert type(argv) is tuple
    assert len(argv) == 19
    assert all(type(value) is str for value in argv)
    if validate_cli_layout:
        assert argv.count("--mcp-config") == 1
        assert argv.index("--mcp-config") + 1 == 17
        assert argv.count("--agents") == 1
        assert argv.index("--agents") + 1 == 5
    assert type(snapshot["input"]) is bytes
    assert type(snapshot["cwd"]) is str
    assert type(snapshot["env"]) is tuple
    assert all(
        type(item) is tuple
        and len(item) == 2
        and type(item[0]) is str
        and type(item[1]) is str
        for item in snapshot["env"]
    )

    inline_agents = json.loads(argv[5])
    assert type(inline_agents) is dict
    assert len(inline_agents) == 1
    inline_agent_name = next(iter(inline_agents))
    if validate_cli_layout:
        assert inline_agent_name == argv[3]
    inline_agent = inline_agents[inline_agent_name]
    assert type(inline_agent) is dict
    effective_prompt = inline_agent.get("prompt")
    assert type(effective_prompt) is str

    argv_bytes = tuple(os.fsencode(value) for value in argv)
    env_bytes = tuple(
        (os.fsencode(key), os.fsencode(value))
        for key, value in snapshot["env"]
    )
    raw_call_arguments = {
        "argv": argv_bytes,
        "input": snapshot["input"],
        "cwd": os.fsencode(snapshot["cwd"]),
        "env": env_bytes,
        "timeout": snapshot["timeout"],
        "check": snapshot["check"],
        "stdout": snapshot["stdout"],
        "stderr": snapshot["stderr"],
    }
    projected_argv = list(argv_bytes)
    projected_argv[17] = _T1712_MCP_PATH_SENTINEL
    projected_call_arguments = {
        **raw_call_arguments,
        "argv": tuple(projected_argv),
        "cwd": _T1712_CWD_SENTINEL,
    }
    role_explicit_inputs = (
        ("agents-inline-json", argv_bytes[5]),
        ("effective-prompt", effective_prompt.encode("utf-8")),
        ("stdin-payload", snapshot["input"]),
    )
    launch_remainder_bytes = tuple(
        (f"argv[{index}]", value)
        for index, value in enumerate(argv_bytes)
        if index not in {5, 17}
    ) + tuple(
        item
        for index, (key, value) in enumerate(env_bytes)
        for item in (
            (f"env[{index}].key", key),
            (f"env[{index}].value", value),
        )
    )
    return {
        "raw_call_arguments": raw_call_arguments,
        "projected_call_arguments": projected_call_arguments,
        "role_explicit_inputs": role_explicit_inputs,
        "launch_remainder_bytes": launch_remainder_bytes,
    }


def _t1712_assert_no_path_token_hits(
    snapshot: dict[str, Any],
    *,
    tokens: tuple[tuple[str, bytes], ...],
    assert_no_hits: bool = True,
) -> dict[str, list[tuple[str, str]]]:
    observation = _t1712_launch_contract_observation(snapshot)
    role_hits = [
        (token_label, surface_label)
        for token_label, token in tokens
        for surface_label, value in observation["role_explicit_inputs"]
        if token in value
    ]
    if assert_no_hits:
        assert not role_hits, f"role explicit-input hit group: {role_hits}"
    launch_remainder_hits = [
        (token_label, surface_label)
        for token_label, token in tokens
        for surface_label, value in observation["launch_remainder_bytes"]
        if token in value
    ]
    if assert_no_hits:
        assert not launch_remainder_hits, (
            "env/non-excluded-argv hit group: "
            f"{launch_remainder_hits}"
        )
    return {
        "role-explicit-inputs": role_hits,
        "env/non-excluded-argv": launch_remainder_hits,
    }


def _t1354_assert_actual_transport_metadata(
    snapshot: dict[str, Any],
    *,
    holdout: str,
    workload: str,
    arm_binding_digest_sha256: str,
    repositories: tuple[Path, ...],
) -> None:
    argv = snapshot["argv"]
    mcp_config_path = Path(argv[17])
    neutral_root = mcp_config_path.parent
    cwd = Path(snapshot["cwd"])
    temp_parent = Path(P.tempfile.gettempdir()).resolve()
    assert neutral_root.parent == temp_parent
    assert neutral_root.name.startswith("izanagi-projected-")
    assert mcp_config_path.name == "empty-mcp-config.json"
    assert mcp_config_path.read_bytes() == b'{"mcpServers":{}}'
    assert cwd.parent == neutral_root
    assert cwd.name.startswith("cwd-")
    assert cwd.is_dir() and not any(cwd.iterdir())
    for repository in repositories:
        assert not neutral_root.is_relative_to(repository.resolve())
        assert not cwd.is_relative_to(repository.resolve())
    for actual_value in (str(mcp_config_path), str(cwd)):
        assert holdout not in actual_value
        assert workload not in actual_value
        assert arm_binding_digest_sha256 not in actual_value


def _projected_provider_call(tmp_path: Path) -> ClaudeProjectedRoleProvider:
    provider = ClaudeProjectedRoleProvider(
        artifact_root=tmp_path / "artifacts",
        role_file=_role_file(tmp_path / "role.md"),
        role_name="fixture-auditor",
        mediated_contract="Return one JSON object only.",
        repository_root=Path(__file__).resolve().parents[2],
        executable=_executable(tmp_path),
        runner=_Runner(_envelope()),
        environ={"HOME": "/fixture/home"},
    )
    provider.invoke(invocation_id="ycsb-a.g1.auditor", payload={"x": 1})
    return provider


def _assert_projected_cleanup_guard(
    *,
    neutral_root: Path,
    neutral_cwd: Path,
    cleanup_target: Path,
    artifact_root: Path,
    artifact_bytes: dict[Path, bytes],
    outside_marker: Path,
) -> None:
    """Projected provider の cleanup 静止境界を検査する。

    周辺 test を含む gate は明示 close の正常/異常、cleanup error 後の再試行、
    参照破棄後の fallback、静止した削除境界、owner close まで到達する。未到達
    なのは interpreter shutdown 中の live object、fork child の atexit、並行
    invoke/close、close 後の再 invoke、scope 外 callsite である。
    """
    assert not neutral_root.exists() and not neutral_root.is_symlink(), "root 消滅"
    assert not neutral_cwd.exists() and not neutral_cwd.is_symlink(), "cwd 消滅"
    assert artifact_root.is_dir() and not artifact_root.is_symlink(), "artifact_root 存続"
    artifact_bytes_unchanged = all(
        path.read_bytes() == expected for path, expected in artifact_bytes.items()
    )
    assert artifact_bytes_unchanged, "artifact bytes 不変"
    assert outside_marker.is_file(), "外部 marker 存続"
    resolved_artifact_root = artifact_root.resolve(strict=True)
    resolved_cleanup_target = cleanup_target.resolve(strict=False)
    artifact_inside_cleanup_target = (
        resolved_artifact_root == resolved_cleanup_target
        or resolved_artifact_root.is_relative_to(resolved_cleanup_target)
    )
    assert not artifact_inside_cleanup_target, "非交差"


@pytest.mark.parametrize(
    "predicate",
    ["root", "cwd", "artifact", "bytes", "marker", "nonintersection"],
)
def test_projected_cleanup_guard_rejects_each_predicate_independently(
    tmp_path, predicate,
) -> None:
    """各入力では指定 predicate だけを偽にし、projected guard の歯を固定する。"""
    neutral_root = tmp_path / "neutral-missing"
    neutral_cwd = tmp_path / "cwd-missing"
    cleanup_target = tmp_path / "cleanup-missing"
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    artifact_path = artifact_root / "payload.json"
    artifact_path.write_bytes(b"proof-chain")
    artifact_bytes = {artifact_path: artifact_path.read_bytes()}
    outside_marker = tmp_path / "outside.marker"
    outside_marker.write_bytes(b"outside")

    expected_message = {
        "root": "root 消滅",
        "cwd": "cwd 消滅",
        "artifact": "artifact_root 存続",
        "bytes": "artifact bytes 不変",
        "marker": "外部 marker 存続",
        "nonintersection": "非交差",
    }[predicate]
    if predicate == "root":
        neutral_root.mkdir()
    elif predicate == "cwd":
        neutral_cwd.mkdir()
    elif predicate == "artifact":
        real_artifact_root = tmp_path / "artifact-target"
        artifact_root.rename(real_artifact_root)
        artifact_root.symlink_to(real_artifact_root, target_is_directory=True)
    elif predicate == "bytes":
        artifact_path.write_bytes(b"mutated")
    elif predicate == "marker":
        outside_marker.unlink()
    elif predicate == "nonintersection":
        cleanup_target = artifact_root

    with pytest.raises(AssertionError, match=expected_message):
        _assert_projected_cleanup_guard(
            neutral_root=neutral_root,
            neutral_cwd=neutral_cwd,
            cleanup_target=cleanup_target,
            artifact_root=artifact_root,
            artifact_bytes=artifact_bytes,
            outside_marker=outside_marker,
        )


def _projected_cleanup_inputs(provider, tmp_path: Path) -> dict:
    outside_marker = tmp_path / "outside" / "marker"
    outside_marker.parent.mkdir(exist_ok=True)
    outside_marker.write_bytes(b"outside")
    (provider.neutral_root / "outside-link").symlink_to(outside_marker)
    return {
        "neutral_root": provider.neutral_root,
        "neutral_cwd": provider.neutral_cwd,
        "artifact_root": provider.artifact_root,
        "artifact_bytes": {
            path: path.read_bytes()
            for path in provider.artifact_root.iterdir()
            if path.is_file()
        },
        "outside_marker": outside_marker,
    }


def _rescue_projected_neutral_root(identity: Path) -> None:
    """Mutation failure 後も、記録済みの生 identity だけを best-effort 削除する。"""
    if not identity.is_symlink():
        shutil.rmtree(identity, ignore_errors=True)


def test_projected_provider_close_removes_only_neutral_tree(
    tmp_path, monkeypatch,
) -> None:
    provider = _projected_provider_call(tmp_path)
    recorded_identity = provider._neutral_root_identity
    try:
        guard_inputs = _projected_cleanup_inputs(provider, tmp_path)
        actual_cleanup_targets: list[Path] = []
        original_remove = P._remove_neutral_root

        def recording_remove(neutral_root_identity, artifact_root):
            actual_cleanup_targets.append(Path(neutral_root_identity))
            # M16 の危険 target は記録だけし、fixture の既知 identity を安全に削除する。
            return original_remove(recorded_identity, artifact_root)

        monkeypatch.setattr(P, "_remove_neutral_root", recording_remove)
        provider.close()
        provider.close()
        assert provider.cleanup_error is None
        assert not provider._neutral_root_finalizer.alive
        assert len(actual_cleanup_targets) == 1
        _assert_projected_cleanup_guard(
            cleanup_target=actual_cleanup_targets[0], **guard_inputs,
        )
    finally:
        _rescue_projected_neutral_root(recorded_identity)


def test_projected_provider_finalize_fallback_removes_only_neutral_tree(
    tmp_path, monkeypatch,
) -> None:
    provider = _projected_provider_call(tmp_path)
    recorded_identity = provider._neutral_root_identity
    try:
        guard_inputs = _projected_cleanup_inputs(provider, tmp_path)
        actual_cleanup_targets: list[Path] = []
        original_remove = S._remove_neutral_root
        provider_ref = weakref.ref(provider)

        def recording_remove(neutral_root_identity, artifact_root):
            actual_cleanup_targets.append(Path(neutral_root_identity))
            return original_remove(neutral_root_identity, artifact_root)

        monkeypatch.setattr(S, "_remove_neutral_root", recording_remove)
        del provider
        gc.collect()
        assert provider_ref() is None
        assert len(actual_cleanup_targets) == 1
        _assert_projected_cleanup_guard(
            cleanup_target=actual_cleanup_targets[0], **guard_inputs,
        )
    finally:
        _rescue_projected_neutral_root(recorded_identity)


def test_projected_provider_close_never_raises_and_retries_before_detach(
    tmp_path, monkeypatch,
) -> None:
    provider = _projected_provider_call(tmp_path)
    recorded_identity = provider._neutral_root_identity
    try:
        guard_inputs = _projected_cleanup_inputs(provider, tmp_path)
        original_remove = P._remove_neutral_root
        actual_cleanup_targets: list[Path] = []

        def fail_once(neutral_root_identity, artifact_root):
            actual_cleanup_targets.append(Path(neutral_root_identity))
            if len(actual_cleanup_targets) == 1:
                raise OSError("simulated cleanup failure")
            return original_remove(neutral_root_identity, artifact_root)

        monkeypatch.setattr(P, "_remove_neutral_root", fail_once)
        provider.close()
        assert isinstance(provider.cleanup_error, OSError)
        assert provider._neutral_root_finalizer.alive
        provider.close()
        assert len(actual_cleanup_targets) == 2
        assert not provider._neutral_root_finalizer.alive
        _assert_projected_cleanup_guard(
            cleanup_target=actual_cleanup_targets[-1], **guard_inputs,
        )
    finally:
        _rescue_projected_neutral_root(recorded_identity)


@pytest.mark.parametrize("failure", ["mcp-config", "home-missing", "environment-baseexception"])
def test_projected_provider_init_failure_removes_neutral_root(
    tmp_path, monkeypatch, failure,
) -> None:
    created_identities: list[Path] = []
    fallback_attempts: list[Path] = []
    original_create = P._create_neutral_root

    def recording_create(*args, **kwargs):
        result = original_create(*args, **kwargs)
        created_identities.append(result[1])
        return result

    def recording_fallback(neutral_root_identity, artifact_root):
        fallback_attempts.append(Path(neutral_root_identity))

    monkeypatch.setattr(P, "_create_neutral_root", recording_create)
    monkeypatch.setattr(S, "_finalize_neutral_root", recording_fallback)
    environ: dict[str, str] = {"HOME": "/fixture/home"}
    expected_error: type[BaseException] = PredictionRunnerError
    if failure == "mcp-config":
        def fail_write(*args, **kwargs):
            raise OSError("mcp write failure")

        monkeypatch.setattr(P, "_write_bytes_bound", fail_write)
        expected_error = OSError
    elif failure == "home-missing":
        environ = {}
    else:
        class _ExplodingEnvironment(dict):
            def __contains__(self, key):
                raise KeyboardInterrupt("environment mapping failure")

        environ = _ExplodingEnvironment(HOME="/fixture/home")
        expected_error = KeyboardInterrupt

    try:
        with pytest.raises(expected_error):
            ClaudeProjectedRoleProvider(
                artifact_root=tmp_path / "artifacts",
                role_file=_role_file(tmp_path / "role.md"),
                role_name="fixture-auditor",
                mediated_contract="Return JSON only.",
                repository_root=Path(__file__).resolve().parents[2],
                executable=_executable(tmp_path),
                environ=environ,
            )
        assert len(created_identities) == 1
        assert not created_identities[0].exists()
        assert fallback_attempts == []
    finally:
        for identity in created_identities:
            _rescue_projected_neutral_root(identity)


def test_projected_provider_lowers_source_tools_and_binds_effective_prompt(tmp_path) -> None:
    runner = _Runner(_envelope())
    provider = ClaudeProjectedRoleProvider(
        artifact_root=tmp_path / "artifacts",
        role_file=_role_file(tmp_path / "role.md"),
        role_name="fixture-auditor",
        mediated_contract="Return one JSON object only.",
        repository_root=Path(__file__).resolve().parents[2],
        executable=_executable(tmp_path),
        runner=runner,
        environ={"HOME": "/fixture/home", "SECRET": "not-forwarded"},
    )
    response = provider.invoke(invocation_id="ycsb-a.g1.auditor", payload={"x": 1})
    inline = json.loads(provider.inline_agents_json)[provider.inline_agent_name]
    assert inline["tools"] == []
    assert provider.source_declared_tools == ["Read", "Grep"]
    assert "Return one JSON object only." in inline["prompt"]
    assert response.provenance["source_declared_tools"] == ["Read", "Grep"]
    assert response.provenance["declared_tools"] == []
    assert response.provenance["capability_lowering"] == "projection-only-tools-empty"
    assert response.provenance["effective_prompt_sha256"] == provider.effective_prompt_sha256
    assert set(runner.calls[0][1]["env"]) == {"HOME"}
    assert runner.calls[0][1]["cwd"] != str(Path(__file__).resolve().parents[2])


def test_projected_provider_rejects_server_tool_use(tmp_path) -> None:
    provider = ClaudeProjectedRoleProvider(
        artifact_root=tmp_path / "artifacts",
        role_file=_role_file(tmp_path / "role.md"),
        role_name="fixture-auditor",
        mediated_contract="Return JSON only.",
        repository_root=Path(__file__).resolve().parents[2],
        executable=_executable(tmp_path),
        runner=_Runner(_envelope(server_calls=1)),
        environ={"HOME": "/fixture/home"},
    )
    with pytest.raises(PredictionRunnerError, match="server tool use"):
        provider.invoke(invocation_id="ycsb-a.g1.auditor", payload={"x": 1})


def test_t1311_provider_payload_and_envelope_are_bound_to_arm_digest(
    tmp_path,
) -> None:
    digest = "a" * 64
    invocation_id = A._invocation_id(
        arm="on",
        digest=digest,
        workload="rr80",
        generation=1,
        role="auditor",
    )
    envelope = _envelope()
    envelope["result"] = json.dumps({
        "verdict": "pass",
        "diff_digest": "b" * 64,
        "violations": [],
        "nits": [],
        "proposed_tests": [],
        "uncertainty": "",
    }, separators=(",", ":"))
    provider = ClaudeProjectedRoleProvider(
        artifact_root=tmp_path / "provider",
        role_file=_role_file(tmp_path / "role.md"),
        role_name="fixture-auditor",
        mediated_contract="Return one JSON object only.",
        repository_root=Path(__file__).resolve().parents[2],
        executable=_executable(tmp_path),
        runner=_Runner(envelope),
        environ={"HOME": "/fixture/home"},
    )
    payload = {
        "descriptor_binding": {
            "output_sha256": "c" * 64,
            "arm_binding_digest_sha256": digest,
        },
        "working_diff": "fixture diff",
        "diff_digest": "b" * 64,
    }
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    journal = A.AttemptJournal(tmp_path / "attempts.jsonl")
    try:
        parsed, event = A._invoke(
            role="auditor",
            provider=provider,
            invocation_id=invocation_id,
            payload=payload,
            raw_root=raw_root,
            journal=journal,
            workload="rr80",
            generation=1,
        )
    finally:
        provider.close()
    assert parsed is not None
    payload_path = Path(event["provider_artifacts"]["payload_path"])
    envelope_path = Path(event["provider_artifacts"]["envelope_path"])
    assert event["arm_binding_digest_sha256"] == digest
    assert event["provider_artifacts"]["arm_binding_digest_sha256"] == digest
    assert digest in payload_path.name
    assert digest in envelope_path.name
    assert json.loads(payload_path.read_text("utf-8"))[
        "descriptor_binding"
    ]["arm_binding_digest_sha256"] == digest
    assert hashlib.sha256(payload_path.read_bytes()).hexdigest() == (
        event["provider_payload_sha256"]
    )
    assert hashlib.sha256(envelope_path.read_bytes()).hexdigest() == (
        event["provider_envelope_sha256"]
    )


# T-325 supervisor/registry integration.  The formal entries now come from the
# shared holdout authority; the registry gate remains the reason under test.
def _t325_git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        env=A.trial_registry._git_env(),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def _t325_prepare_effective_binding(repo: Path, manifest_path: Path) -> str:
    manifest = A.trial_registry.load_trial_manifest(manifest_path)
    slots = []
    for trial in manifest.trials:
        identity = {
            "trial_id": trial.trial_id,
            "arm": trial.arm,
            "holdout": trial.holdout,
            "campaign_id": trial.campaign_id,
            "prereg_generation": 13,
            "replicate_index": 0,
            "attempt_index": 0,
        }
        slots.append({
            "slot_id": f"{trial.trial_id}-r0-a0",
            **identity,
            "schedule_row_sha256": hashlib.sha256(
                A.trial_registry._canonical_json_bytes(identity)
            ).hexdigest(),
        })
    attempt_path = A.trial_registry.create_attempt_registry_genesis(
        repository_root=repo,
        manifest_path=manifest_path,
        manifest_sha256=manifest.sha256,
        freeze_id=f"freeze-{manifest.sha256[:16]}",
        prereg_generation=13,
        slots=slots,
    )
    _t325_git(repo, "add", "--", str(attempt_path.relative_to(repo)))
    _t325_git(repo, "commit", "-m", "attempt registry genesis")
    content_commit = _t325_git(repo, "rev-parse", "HEAD")
    genesis = json.loads(attempt_path.read_bytes().splitlines()[0])
    binding_path = repo / A.trial_registry.DEFAULT_EFFECTIVE_BINDING_PATH
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    binding_path.write_bytes(A.trial_registry._canonical_json_bytes({
        "schema_version": A.trial_registry.EFFECTIVE_BINDING_SCHEMA_VERSION,
        "prereg_content_commit": content_commit,
        "manifest_path": manifest_path.relative_to(repo).as_posix(),
        "manifest_sha256": manifest.sha256,
        "freeze_id": genesis["freeze_id"],
        "attempt_registry_path": A.trial_registry.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(),
        "attempt_registry_initial_sha256": hashlib.sha256(
            attempt_path.read_bytes()
        ).hexdigest(),
    }))
    _t325_git(repo, "add", "--", str(binding_path.relative_to(repo)))
    _t325_git(repo, "commit", "-m", "effective binding")
    return _t325_git(repo, "rev-parse", "HEAD")


@pytest.fixture
def t325_registered_trial(tmp_path, monkeypatch):
    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    repo = tmp_path / "registry-repo"
    repo.mkdir()
    _t325_git(repo, "init")
    _t325_git(repo, "config", "user.name", "T325 Fixture")
    _t325_git(repo, "config", "user.email", "t325@example.invalid")
    (repo / "anchor.txt").write_text("preregistered\n", encoding="utf-8")
    _t325_git(repo, "add", "anchor.txt")
    _t325_git(repo, "commit", "-m", "prereg anchor")
    prereg_commit = _t325_git(repo, "rev-parse", "HEAD")
    A.s8c_arm_inputs.generate_off_neutral_artifacts(repository_root=repo)
    _t325_git(
        repo,
        "add",
        "--",
        A.s8c_arm_inputs.OFF_DESCRIPTOR_RELATIVE_PATH.as_posix(),
        A.s8c_arm_inputs.OFF_FREEZE_RELATIVE_PATH.as_posix(),
    )
    _t325_git(repo, "commit", "-m", "add arm input authority")
    arm_input_commit = _t325_git(repo, "rev-parse", "HEAD")

    monkeypatch.setattr(A, "ROOT", repo)
    for name, formal_entry in A.FORMAL_WORKLOADS.items():
        monkeypatch.setitem(
            A.WORKLOADS,
            name,
            A.WorkloadEntry(copy.deepcopy(formal_entry)),
        )

    trials = []
    for holdout, workload in (("H1", "rr80"), ("H2", "rr20")):
        for arm in ("on", "off", "swapped"):
            trial_id = f"t325-{holdout.lower()}-{arm}"
            resolved = A.s8c_arm_inputs.resolve_arm_input(
                arm=arm,
                holdout=holdout,
                repository_root=repo,
                commit=arm_input_commit,
            )
            prepared = A._prepare_manifest_campaign_identity(
                workload=workload,
                trial_id=trial_id,
                generations=2,
                site=A.trigger.site_policy.OTHER,
                contract=_T530_CONTRACT,
                build_context=_no_build_context(),
                resolved_arm_input=resolved,
            )
            trials.append({
                "trial_id": trial_id,
                "arm": arm,
                "holdout": holdout,
                "campaign_id": prepared.campaign_id,
                "generations": 2,
                "n": 2,
            })
    manifest_path = repo / "manifests" / "trial.json"
    manifest_path.parent.mkdir()
    manifest_path.write_text(
        json.dumps({
            "schema_version": A.trial_registry.MANIFEST_SCHEMA_VERSION,
            "prereg_commit": prereg_commit,
            "trials": trials,
        }, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    _t325_git(repo, "add", "manifests/trial.json")
    _t325_git(repo, "commit", "-m", "add trial manifest")
    registry_path = repo / A.trial_registry.DEFAULT_REGISTRY_PATH
    effective_commit = _t325_prepare_effective_binding(repo, manifest_path)
    A.trial_registry.append_trial_registration(
        manifest_path=manifest_path,
        repository_root=repo,
        registry_path=registry_path,
        prereg_effective_commit=effective_commit,
    )
    _t325_git(repo, "add", str(A.trial_registry.DEFAULT_REGISTRY_PATH))
    _t325_git(repo, "commit", "-m", "register trial manifest")
    trial_id = "t325-h1-on"
    prereg_report = A.s8c_preregistration.ActivationReport(
        commit=prereg_commit,
        condition_freeze_valid=True,
        freeze_generation=1,
        protected_sha256="1" * 64,
        freeze_reason_code="valid",
        decider_version=A.s8c_preregistration.DECIDER_VERSION,
        decider_version_matches=True,
        decider_version_reason_code="decider-version-match",
        section5_findings=(),
        predicates=(),
        core_module_blob_sha256="2" * 64,
        evaluator_module_blob_sha256="3" * 64,
        projection_module_blob_sha256="4" * 64,
        effective=True,
    )
    capability = A.s8c_preregistration._construct_effective(prereg_report)
    monkeypatch.setattr(
        A.s8c_preregistration,
        "activation_report_at",
        lambda repo_root, commit: prereg_report,
    )
    monkeypatch.setattr(
        A.s8c_preregistration,
        "effective_at",
        lambda repo_root, commit: capability,
    )
    binding = A.trial_registry.load_launch_binding(
        manifest_path=manifest_path,
        trial_id=trial_id,
        workloads=["rr80"],
        repository_root=repo,
        registry_path=registry_path,
    )
    admission = A.trial_registry.admit_registered_launch(
        effective_preregistration=capability,
        manifest_path=manifest_path,
        trial_id=trial_id,
        workloads=["rr80"],
        repository_root=repo,
        registry_path=registry_path,
    )
    return SimpleNamespace(
        repo=repo,
        manifest_path=manifest_path,
        registry_path=registry_path,
        trial_id=trial_id,
        binding=binding,
        capability=capability,
        admission=admission,
    )


def test_generation1_off_arm_supervisor_to_claude_cli_launch_contract_is_holdout_invariant(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    """正式 H1 / H2 の `off` arm に限る。

    `on` / `swapped` は不一致を要求する正の対照である。Generation 1 の
    supervisor から Claude CLI への launch contract だけを検査する。

    実 CLI の outbound request bytes、除外 2 field の role 不可視性、実走時の
    cross-cell env 同一性、generation 2 以降は含意しない。
    """
    roles = ("planner", "coder", "auditor")
    holdouts = {"H1": "rr80", "H2": "rr20"}
    arms = ("on", "off", "swapped")
    expected_snapshot_keys = {
        (holdout, arm, role)
        for holdout in holdouts
        for arm in arms
        for role in roles
    }
    snapshots: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = {}
    arm_binding_digests: dict[tuple[str, str], str] = {}
    executable = _executable(tmp_path)
    base_env = {
        "TERM": "t1354-term",
        "PATH": "/t1354/bin",
        "LC_ALL": "C",
        "LANG": "C.UTF-8",
        "HOME": "/t1354/home",
    }
    expected_base_env = tuple(
        (key, base_env[key]) for key in sorted(S.CLAUDE_ENV_ALLOWLIST)
    )
    transport_admission, transport_receipt = _pegasus_transport_fixture()
    transport_env = transport_admission.env_dict()

    def stop_after_first_generation(*args, **kwargs):
        outcome = _fake_drive(*args, **kwargs)
        outcome["stop_reason"] = "budget-iterations"
        return outcome

    for transport_mode in _T1354_TRANSPORT_MODES:
        if transport_mode == "opt-out":
            source_env = base_env
            admission_for_provider = None
            receipt_for_run = None
        else:
            source_env = {
                **base_env,
                "PBS_JOBID": transport_receipt["pbs_jobid"],
                **transport_env,
            }
            admission_for_provider = transport_admission
            receipt_for_run = transport_receipt
        expected_env = expected_base_env + (
            tuple(transport_env.items()) if admission_for_provider is not None else ()
        )

        for holdout, workload in holdouts.items():
            for arm in arms:
                trial_id = f"t325-{holdout.lower()}-{arm}"
                launch_admission = A.trial_registry.admit_registered_launch(
                    effective_preregistration=t325_registered_trial.capability,
                    manifest_path=t325_registered_trial.manifest_path,
                    trial_id=trial_id,
                    workloads=[workload],
                    repository_root=t325_registered_trial.repo,
                    registry_path=t325_registered_trial.registry_path,
                )
                arm_execution = A.trial_registry.bind_trial_arm(
                    launch_admission.binding,
                    repository_root=t325_registered_trial.repo,
                )
                arm_digest = arm_execution.arm_binding_digest_sha256
                arm_binding_digests[(holdout, arm)] = arm_digest
                run_root = (
                    tmp_path
                    / "t1354-matrix"
                    / transport_mode
                    / holdout
                    / arm
                )
                (run_root / "raw").mkdir(parents=True)
                (run_root / "proposals").mkdir()
                journal = A.AttemptJournal(run_root / "attempts.jsonl")
                providers = {}
                runners = {}
                try:
                    for role in roles:
                        runner = _Runner(_t1354_role_envelope(
                            role,
                            session_id=(
                                f"t1354-{transport_mode}-{holdout.lower()}-{arm}-{role}"
                            ),
                        ))
                        runners[role] = runner
                        role_file, role_name = A.ROLE_FILES[role]
                        provider_kwargs = {
                            "artifact_root": run_root / "provider" / role,
                            "role_file": role_file,
                            "role_name": role_name,
                            "mediated_contract": A.ROLE_CONTRACTS[role],
                            "repository_root": _ROOT,
                            "executable": executable,
                            "runner": runner,
                            "allow_pegasus_compute_transport": (
                                admission_for_provider is not None
                            ),
                            "transport_admission": admission_for_provider,
                        }
                        if admission_for_provider is None:
                            with monkeypatch.context() as env_patch:
                                env_patch.setattr(P.os, "environ", source_env)
                                providers[role] = ClaudeProjectedRoleProvider(
                                    **provider_kwargs
                                )
                        else:
                            providers[role] = ClaudeProjectedRoleProvider(
                                environ=source_env,
                                **provider_kwargs,
                            )

                    scope = A._RunScopeBinding(
                        launch_admission,
                        A._RUN_SCOPE_SEAL,
                        None,
                        arm_execution,
                    )
                    token = A._ACTIVE_TRIAL_BINDING.set(scope)
                    try:
                        cell = A._run_workload(
                            workload=workload,
                            generations=2,
                            providers=providers,
                            journal=journal,
                            run_root=run_root,
                            sub="/unused",
                            do_build=False,
                            cache_root="",
                            trial_id=trial_id,
                            started_monotonic=time.monotonic(),
                            max_wall_s=3600,
                            drive=stop_after_first_generation,
                            preview=_fake_preview,
                            transport_receipt=receipt_for_run,
                            transport_admission=admission_for_provider,
                            build_context=_no_build_context(),
                            gating_spec_snapshot=A.snapshot_gating_spec(A.GATING_SPEC),
                        )
                    finally:
                        A._ACTIVE_TRIAL_BINDING.reset(token)

                    assert len(cell["generations"]) == 1
                    assert cell["generations"][0]["generation"] == 1
                    journal_role_event_list = [
                        event
                        for event in (
                            json.loads(line)
                            for line in journal.path.read_text(
                                encoding="utf-8"
                            ).splitlines()
                        )
                        if event["event"] == "role-attempt"
                    ]
                    assert len(journal_role_event_list) == 3
                    assert {
                        role: sum(
                            event["role"] == role
                            for event in journal_role_event_list
                        )
                        for role in roles
                    } == {role: 1 for role in roles}
                    journal_role_events = {
                        event["role"]: event
                        for event in journal_role_event_list
                    }
                    assert set(journal_role_events) == set(roles)
                    for role in roles:
                        snapshot = _t1354_runner_snapshot(runners[role])
                        assert snapshot["env"] == expected_env
                        assert "PBS_JOBID" not in dict(snapshot["env"])
                        _t1354_assert_actual_transport_metadata(
                            snapshot,
                            holdout=holdout,
                            workload=workload,
                            arm_binding_digest_sha256=arm_digest,
                            repositories=(_ROOT, t325_registered_trial.repo),
                        )
                        payload = json.loads(snapshot["input"])
                        assert payload["generation"] == 1
                        payload_shape = (
                            "planner-generation-1" if role == "planner" else role
                        )
                        assert set(payload) == set(
                            A.ROLE_PAYLOAD_KEY_SPEC[payload_shape]
                        )
                        audit_id = (
                            f"arm-{arm}.exec-{arm_digest}."
                            f"{workload}.g1.{role}"
                        )
                        journal_event = journal_role_events[role]
                        assert journal_event["arm_binding_digest_sha256"] == (
                            arm_digest
                        )
                        assert journal_event["invocation_id"] == audit_id
                        key = (holdout, arm, role)
                        per_transport = snapshots.setdefault(key, {})
                        assert transport_mode not in per_transport
                        per_transport[transport_mode] = snapshot
                finally:
                    A._close_owned_providers(providers)

    assert len(snapshots) == 18
    assert set(snapshots) == expected_snapshot_keys
    assert all(
        set(per_transport) == set(_T1354_TRANSPORT_MODES)
        for per_transport in snapshots.values()
    )
    sensitive_tokens = {
        *holdouts,
        *holdouts.values(),
        *arm_binding_digests.values(),
    }
    for per_transport in snapshots.values():
        for snapshot in per_transport.values():
            actual_metadata = (snapshot["argv"][17], snapshot["cwd"])
            assert all(
                token not in actual_value
                for actual_value in actual_metadata
                for token in sensitive_tokens
            )

    for arm in ("on", "swapped"):
        assert arm_binding_digests[("H1", arm)] != arm_binding_digests[("H2", arm)]

    for transport_mode in _T1354_TRANSPORT_MODES:
        for role in roles:
            off_h1 = snapshots[("H1", "off", role)][transport_mode]
            off_h2 = snapshots[("H2", "off", role)][transport_mode]
            assert off_h1["input"] == off_h2["input"]
            assert off_h1["env"] == off_h2["env"]
            assert _t1354_normalize_transport_snapshot(off_h1) == (
                _t1354_normalize_transport_snapshot(off_h2)
            )

            for arm in ("on", "swapped"):
                positive_h1 = snapshots[("H1", arm, role)][transport_mode]
                positive_h2 = snapshots[("H2", arm, role)][transport_mode]
                normalized_h1 = _t1354_normalize_transport_snapshot(positive_h1)
                normalized_h2 = _t1354_normalize_transport_snapshot(positive_h2)
                assert normalized_h1 != normalized_h2
                assert positive_h1["input"] != positive_h2["input"]
                normalized_h1["input"] = b"<t1354-positive-control-input>"
                normalized_h2["input"] = b"<t1354-positive-control-input>"
                assert normalized_h1 == normalized_h2


def test_generation1_supervisor_to_claude_cli_launch_contract_oracle_rejects_unexcluded_mutations(
    tmp_path, monkeypatch,
) -> None:
    """Generation 1 の supervisor から Claude CLI への launch contract に限る。

    実 CLI の outbound request bytes、除外 2 field の role 不可視性、実走時の
    cross-cell env 同一性、generation 2 以降は含意しない。
    """
    baseline = {
        "argv": (
            "/fixture/claude",
            "-p",
            "--agent",
            "izanagi-projected-inline",
            "--agents",
            "{}",
            "--output-format",
            "json",
            "--input-format",
            "text",
            "--effort",
            "high",
            "--setting-sources",
            "",
            "--disable-slash-commands",
            "--strict-mcp-config",
            "--mcp-config",
            "/tmp/izanagi-projected-alpha/empty-mcp-config.json",
            "--no-session-persistence",
        ),
        "input": b'{"generation":1,"workload":"off-neutral"}',
        "cwd": "/tmp/izanagi-projected-alpha/cwd-alpha",
        "env": (("HOME", "/fixture/home"), ("PATH", "/fixture/bin")),
        "timeout": S.CLAUDE_TIMEOUT_S,
        "check": False,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
    }
    normalized_baseline = _t1354_normalize_transport_snapshot(baseline)

    excluded_mutations = {}
    mcp_mutation = copy.deepcopy(baseline)
    mcp_argv = list(mcp_mutation["argv"])
    mcp_argv[17] = "/tmp/izanagi-projected-beta/empty-mcp-config.json"
    mcp_mutation["argv"] = tuple(mcp_argv)
    excluded_mutations["argv.mcp_config_path"] = mcp_mutation
    cwd_mutation = copy.deepcopy(baseline)
    cwd_mutation["cwd"] = "/tmp/izanagi-projected-alpha/cwd-beta"
    excluded_mutations["kwargs.cwd"] = cwd_mutation
    assert set(excluded_mutations) == _T1354_TRANSPORT_EXCLUSIONS
    assert len(excluded_mutations) == 2
    for mutation in excluded_mutations.values():
        assert _t1354_normalize_transport_snapshot(mutation) == normalized_baseline

    mutations = {}
    argv_mutation = copy.deepcopy(baseline)
    argv_values = list(argv_mutation["argv"])
    argv_values[0] = "/fixture/other-claude"
    argv_mutation["argv"] = tuple(argv_values)
    mutations["argv.non_mcp"] = argv_mutation
    input_mutation = copy.deepcopy(baseline)
    input_mutation["input"] = b'{"generation":1,"workload":"leaked"}'
    mutations["kwargs.input"] = input_mutation
    env_value_mutation = copy.deepcopy(baseline)
    env_value_mutation["env"] = (
        ("HOME", "/fixture/other-home"),
        ("PATH", "/fixture/bin"),
    )
    mutations["kwargs.env.value"] = env_value_mutation
    env_order_mutation = copy.deepcopy(baseline)
    env_order_mutation["env"] = tuple(reversed(env_order_mutation["env"]))
    mutations["kwargs.env.order"] = env_order_mutation
    for field, replacement in (
        ("timeout", S.CLAUDE_TIMEOUT_S + 1),
        ("check", True),
        ("stdout", None),
        ("stderr", None),
    ):
        mutation = copy.deepcopy(baseline)
        mutation[field] = replacement
        mutations[f"kwargs.{field}"] = mutation
    unknown_field_mutation = copy.deepcopy(baseline)
    unknown_field_mutation["unknown"] = "rejected"
    mutations["kwargs.unknown"] = unknown_field_mutation
    missing_field_mutation = copy.deepcopy(baseline)
    del missing_field_mutation["stderr"]
    mutations["shape.missing"] = missing_field_mutation

    assert set(mutations) == {
        "argv.non_mcp",
        "kwargs.input",
        "kwargs.env.value",
        "kwargs.env.order",
        "kwargs.timeout",
        "kwargs.check",
        "kwargs.stdout",
        "kwargs.stderr",
        "kwargs.unknown",
        "shape.missing",
    }
    assert len(mutations) == 10
    for label, mutation in mutations.items():
        try:
            normalized_mutation = _t1354_normalize_transport_snapshot(mutation)
        except AssertionError:
            continue
        assert normalized_mutation != normalized_baseline, label

    deliberately_unordered_allowlist = tuple(
        reversed(sorted(S.CLAUDE_ENV_ALLOWLIST))
    )
    monkeypatch.setattr(
        P, "CLAUDE_ENV_ALLOWLIST", deliberately_unordered_allowlist,
    )
    provider = ClaudeProjectedRoleProvider(
        artifact_root=tmp_path / "env-order-provider",
        role_file=_role_file(tmp_path / "env-order-role.md"),
        role_name="fixture-auditor",
        mediated_contract="Return JSON only.",
        repository_root=_ROOT,
        executable=_executable(tmp_path),
        environ={key: f"value-{key}" for key in deliberately_unordered_allowlist},
    )
    try:
        assert tuple(provider.env) == tuple(sorted(deliberately_unordered_allowlist))
        assert tuple(provider.env) != deliberately_unordered_allowlist
    finally:
        provider.close()


def test_projected_provider_excluded_paths_preserve_supervisor_to_claude_cli_explicit_launch_call_arguments(
    tmp_path, monkeypatch,
) -> None:
    """除外 path だけを操作して launch contract の明示 call arguments を比較する。

    実 CLI の request bytes、role からの不可視性、provider 応答からの不可視性は含意しない。
    """
    assert P.tempfile is S.tempfile
    canaries = (
        _T1712_CONTROL_PARENT_CANARY,
        _T1712_CONTROL_ROOT_CANARY,
        _T1712_CONTROL_CWD_CANARY,
        _T1712_TREATMENT_PARENT_CANARY,
        _T1712_TREATMENT_ROOT_CANARY,
        _T1712_TREATMENT_CWD_CANARY,
    )
    assert len(set(canaries)) == len(canaries)
    assert all(value.isascii() and len(value) >= 32 for value in canaries)

    control_root = (
        tmp_path
        / _T1712_CONTROL_PARENT_CANARY
        / _T1712_CONTROL_ROOT_CANARY
    )
    treatment_root = (
        tmp_path
        / _T1712_TREATMENT_PARENT_CANARY
        / "t1712-treatment-extra-depth-a"
        / "t1712-treatment-extra-depth-b"
        / _T1712_TREATMENT_ROOT_CANARY
    )
    control_cwd = control_root / _T1712_CONTROL_CWD_CANARY
    treatment_cwd = treatment_root / _T1712_TREATMENT_CWD_CANARY
    assert control_root.parent != treatment_root.parent
    assert control_root.name != treatment_root.name
    assert len(treatment_root.parts) > len(control_root.parts)
    assert len(os.fsencode(treatment_root)) != len(os.fsencode(control_root))
    assert control_cwd.name != treatment_cwd.name
    assert len(os.fsencode(control_cwd.name)) != len(os.fsencode(treatment_cwd.name))

    role_file = _role_file(tmp_path / "t1712-role.md")
    executable = _executable(tmp_path)
    artifact_roots = {
        "control-one": tmp_path / "t1712-artifacts-control-one",
        "control-two": tmp_path / "t1712-artifacts-control-two",
        "treatment": tmp_path / "t1712-artifacts-treatment",
    }
    assert len(set(artifact_roots.values())) == 3
    capture_invocation_ids: list[str] = []

    def capture(
        *, label: str, neutral_root: Path, neutral_cwd: Path,
    ) -> dict[str, Any]:
        mkdtemp_calls: list[tuple[str | None, str | None, str | None]] = []

        def deterministic_mkdtemp(
            suffix=None, prefix=None, dir=None,
        ) -> str:
            directory = os.fspath(dir) if dir is not None else None
            mkdtemp_calls.append((suffix, prefix, directory))
            assert suffix is None
            if prefix == "izanagi-projected-" and dir is None:
                target = neutral_root
                target.parent.mkdir(parents=True, exist_ok=True)
            else:
                assert prefix == "cwd-"
                assert dir is not None
                assert Path(dir).resolve(strict=True) == neutral_root.resolve(strict=True)
                target = neutral_cwd
            target.mkdir(exist_ok=False)
            return str(target)

        assert not neutral_root.exists()
        runner = _Runner(_envelope())
        provider = None
        with monkeypatch.context() as path_patch:
            path_patch.setattr(P.tempfile, "mkdtemp", deterministic_mkdtemp)
            try:
                provider = ClaudeProjectedRoleProvider(
                    artifact_root=artifact_roots[label],
                    role_file=role_file,
                    role_name="fixture-auditor",
                    mediated_contract="Return one JSON object only.",
                    repository_root=_ROOT,
                    executable=executable,
                    runner=runner,
                    environ={
                        "HOME": "/t1712/fixture/home",
                        "PATH": "/t1712/fixture/bin",
                    },
                )
                capture_invocation_ids.append(_T1712_SHARED_INVOCATION_ID)
                provider.invoke(
                    invocation_id=_T1712_SHARED_INVOCATION_ID,
                    payload={"fixture": "t1712-fixed-payload"},
                )
                snapshot = _t1354_runner_snapshot(runner)
                observation = _t1712_launch_contract_observation(snapshot)
                role_inputs = dict(observation["role_explicit_inputs"])
                assert snapshot["argv"][5] == provider.inline_agents_json
                assert role_inputs["effective-prompt"] == (
                    provider.effective_prompt.encode("utf-8")
                )
                assert Path(snapshot["argv"][17]) == (
                    neutral_root / "empty-mcp-config.json"
                )
                assert Path(snapshot["argv"][17]).read_bytes() == (
                    b'{"mcpServers":{}}'
                )
                assert Path(snapshot["cwd"]) == neutral_cwd
                assert neutral_cwd.is_dir() and not any(neutral_cwd.iterdir())
                assert mkdtemp_calls == [
                    (None, "izanagi-projected-", None),
                    (None, "cwd-", str(neutral_root.resolve(strict=True))),
                ]
            finally:
                if provider is not None:
                    provider.close()
        assert not neutral_root.exists()
        return snapshot

    control_one = capture(
        label="control-one",
        neutral_root=control_root,
        neutral_cwd=control_cwd,
    )
    control_two = capture(
        label="control-two",
        neutral_root=control_root,
        neutral_cwd=control_cwd,
    )
    treatment = capture(
        label="treatment",
        neutral_root=treatment_root,
        neutral_cwd=treatment_cwd,
    )
    assert capture_invocation_ids == [
        _T1712_SHARED_INVOCATION_ID,
        _T1712_SHARED_INVOCATION_ID,
        _T1712_SHARED_INVOCATION_ID,
    ]
    observations = {
        "control-one": _t1712_launch_contract_observation(control_one),
        "control-two": _t1712_launch_contract_observation(control_two),
        "treatment": _t1712_launch_contract_observation(treatment),
    }

    assert control_one["argv"][17] == control_two["argv"][17]
    assert control_one["cwd"] == control_two["cwd"]
    assert control_one["argv"][17] != treatment["argv"][17]
    assert control_one["cwd"] != treatment["cwd"]
    assert _T1712_CONTROL_PARENT_CANARY in control_one["argv"][17]
    assert _T1712_CONTROL_ROOT_CANARY in control_one["argv"][17]
    assert _T1712_CONTROL_CWD_CANARY in control_one["cwd"]
    assert _T1712_TREATMENT_PARENT_CANARY in treatment["argv"][17]
    assert _T1712_TREATMENT_ROOT_CANARY in treatment["argv"][17]
    assert _T1712_TREATMENT_CWD_CANARY in treatment["cwd"]

    raw_differences = {
        *(
            f"argv[{index}]"
            for index, (control_value, treatment_value) in enumerate(zip(
                observations["control-one"]["raw_call_arguments"]["argv"],
                observations["treatment"]["raw_call_arguments"]["argv"],
                strict=True,
            ))
            if control_value != treatment_value
        ),
        *(
            f"kwargs.{key}"
            for key in (
                "input", "cwd", "env", "timeout", "check", "stdout", "stderr",
            )
            if observations["control-one"]["raw_call_arguments"][key]
            != observations["treatment"]["raw_call_arguments"][key]
        ),
    }
    # Env canonical ordering has its dedicated oracle in
    # test_generation1_supervisor_to_claude_cli_launch_contract_oracle_rejects_unexcluded_mutations.
    all_probe_tokens = (
        ("control-mcp-path", os.fsencode(control_one["argv"][17])),
        ("control-cwd-path", os.fsencode(control_one["cwd"])),
        ("treatment-mcp-path", os.fsencode(treatment["argv"][17])),
        ("treatment-cwd-path", os.fsencode(treatment["cwd"])),
        *((value, value.encode("ascii")) for value in canaries),
    )
    token_hits = {}
    for label, snapshot in (
        ("control-one", control_one),
        ("control-two", control_two),
        ("treatment", treatment),
    ):
        hits = _t1712_assert_no_path_token_hits(
            snapshot,
            tokens=all_probe_tokens,
            assert_no_hits=False,
        )
        if any(hits.values()):
            token_hits[label] = hits

    comparison_results = {
        "control-between-capture agreement": {
            "matches": (
                observations["control-one"]["raw_call_arguments"]
                == observations["control-two"]["raw_call_arguments"]
            ),
            "expected": "equal raw_call_arguments",
            "actual": {
                "control-one": observations["control-one"][
                    "raw_call_arguments"
                ],
                "control-two": observations["control-two"][
                    "raw_call_arguments"
                ],
            },
        },
        "raw difference labels": {
            "matches": raw_differences == {"argv[17]", "kwargs.cwd"},
            "expected": {"argv[17]", "kwargs.cwd"},
            "actual": raw_differences,
        },
        "role-oriented candidate surfaces": {
            "matches": (
                observations["control-one"]["role_explicit_inputs"]
                == observations["treatment"]["role_explicit_inputs"]
            ),
            "expected": "equal role_explicit_inputs",
            "actual": {
                "control-one": observations["control-one"][
                    "role_explicit_inputs"
                ],
                "treatment": observations["treatment"][
                    "role_explicit_inputs"
                ],
            },
        },
        "projected call arguments": {
            "matches": (
                observations["control-one"]["projected_call_arguments"]
                == observations["treatment"]["projected_call_arguments"]
            ),
            "expected": "equal projected_call_arguments",
            "actual": {
                "control-one": observations["control-one"][
                    "projected_call_arguments"
                ],
                "treatment": observations["treatment"][
                    "projected_call_arguments"
                ],
            },
        },
        "path token hits": {
            "matches": not token_hits,
            "expected": {},
            "actual": token_hits,
        },
    }
    unexpected_comparisons = {
        label: {
            "expected": result["expected"],
            "actual": result["actual"],
        }
        for label, result in comparison_results.items()
        if not result["matches"]
    }
    assert not unexpected_comparisons, (
        "launch-contract comparison results: "
        f"{comparison_results!r}"
    )

    captured_before_synthetic_oracle = copy.deepcopy(control_one)
    baseline_observation = observations["control-one"]
    raw_call_arguments = baseline_observation["raw_call_arguments"]
    assert set(raw_call_arguments) == _T1354_TRANSPORT_SNAPSHOT_KEYS
    assert len(raw_call_arguments["argv"]) == 19
    projected_call_arguments = baseline_observation[
        "projected_call_arguments"
    ]
    assert set(projected_call_arguments) == _T1354_TRANSPORT_SNAPSHOT_KEYS
    assert len(projected_call_arguments["argv"]) == 19
    role_labels = tuple(
        label for label, _value in baseline_observation["role_explicit_inputs"]
    )
    assert len(role_labels) == 3
    assert set(role_labels) == {
        "agents-inline-json",
        "effective-prompt",
        "stdin-payload",
    }
    role_explicit_input_values = dict(
        baseline_observation["role_explicit_inputs"]
    )
    inline_agents = json.loads(control_one["argv"][5])
    inline_agent = inline_agents[next(iter(inline_agents))]
    assert role_explicit_input_values["agents-inline-json"] == os.fsencode(
        control_one["argv"][5]
    )
    assert role_explicit_input_values["stdin-payload"] == control_one["input"]
    assert role_explicit_input_values["effective-prompt"] == inline_agent[
        "prompt"
    ].encode("utf-8")
    assert all(
        type(value) is bytes and value
        for value in role_explicit_input_values.values()
    )
    remainder_labels = tuple(
        label
        for label, _value in baseline_observation["launch_remainder_bytes"]
    )
    expected_remainder_labels = {
        *(f"argv[{index}]" for index in range(19) if index not in {5, 17}),
        *(
            f"env[{index}].{component}"
            for index in range(len(control_one["env"]))
            for component in ("key", "value")
        ),
    }
    assert len(remainder_labels) == len(expected_remainder_labels)
    assert set(remainder_labels) == expected_remainder_labels

    synthetic_snapshots: list[tuple[str, dict[str, Any]]] = []
    for index in range(len(control_one["argv"])):
        synthetic = copy.deepcopy(control_one)
        argv_values = list(synthetic["argv"])
        marker = f":t1712-argv-surface-{index}"
        if index == 5:
            inline_agents = json.loads(argv_values[index])
            assert type(inline_agents) is dict and len(inline_agents) == 1
            inline_agent = inline_agents[next(iter(inline_agents))]
            inline_agent["prompt"] += marker
            argv_values[index] = json.dumps(
                inline_agents,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        else:
            argv_values[index] += marker
        synthetic["argv"] = tuple(argv_values)
        assert {
            changed_index
            for changed_index, (baseline_value, synthetic_value) in enumerate(
                zip(control_one["argv"], synthetic["argv"], strict=True)
            )
            if baseline_value != synthetic_value
        } == {index}
        synthetic_snapshots.append((f"argv[{index}]", synthetic))

    non_argv_mutations = {
        "input": control_one["input"] + b":t1712-input-surface",
        "cwd": control_one["cwd"] + ":t1712-cwd-surface",
        "env": (
            (
                control_one["env"][0][0],
                control_one["env"][0][1] + ":t1712-env-surface",
            ),
            *control_one["env"][1:],
        ),
        "timeout": control_one["timeout"] + 1,
        "check": not control_one["check"],
        "stdout": control_one["stdout"] - 1,
        "stderr": control_one["stderr"] - 2,
    }
    assert set(non_argv_mutations) == (
        _T1354_TRANSPORT_SNAPSHOT_KEYS - {"argv"}
    )
    for key, replacement in non_argv_mutations.items():
        assert type(replacement) is type(control_one[key])
        synthetic = copy.deepcopy(control_one)
        synthetic[key] = replacement
        assert {
            snapshot_key
            for snapshot_key in _T1354_TRANSPORT_SNAPSHOT_KEYS
            if control_one[snapshot_key] != synthetic[snapshot_key]
        } == {key}
        synthetic_snapshots.append((f"kwargs.{key}", synthetic))

    assert {label for label, _snapshot in synthetic_snapshots} == {
        *(f"argv[{index}]" for index in range(19)),
        *(
            f"kwargs.{key}"
            for key in _T1354_TRANSPORT_SNAPSHOT_KEYS
            if key != "argv"
        ),
    }
    for expected_difference, synthetic in synthetic_snapshots:
        synthetic_observation = _t1712_launch_contract_observation(
            synthetic,
            validate_cli_layout=False,
        )
        synthetic_raw = synthetic_observation["raw_call_arguments"]
        assert set(synthetic_raw) == _T1354_TRANSPORT_SNAPSHOT_KEYS
        assert len(synthetic_raw["argv"]) == 19
        detected_differences = {
            *(
                f"argv[{index}]"
                for index, (baseline_value, synthetic_value) in enumerate(zip(
                    raw_call_arguments["argv"],
                    synthetic_raw["argv"],
                    strict=True,
                ))
                if baseline_value != synthetic_value
            ),
            *(
                f"kwargs.{key}"
                for key in (
                    "input", "cwd", "env", "timeout", "check", "stdout", "stderr",
                )
                if raw_call_arguments[key] != synthetic_raw[key]
            ),
        }
        assert detected_differences == {expected_difference}, (
            expected_difference,
            detected_differences,
        )
    assert control_one == captured_before_synthetic_oracle

    treatment_canary = _T1712_TREATMENT_ROOT_CANARY.encode("ascii")
    stdin_leak = copy.deepcopy(treatment)
    stdin_leak["input"] += b":" + treatment_canary
    with pytest.raises(AssertionError, match="role explicit-input hit group"):
        _t1712_assert_no_path_token_hits(
            stdin_leak,
            tokens=(("treatment-root-canary", treatment_canary),),
        )

    argv_leak = copy.deepcopy(treatment)
    argv_values = list(argv_leak["argv"])
    argv_values[0] += ":" + _T1712_TREATMENT_ROOT_CANARY
    argv_leak["argv"] = tuple(argv_values)
    with pytest.raises(AssertionError, match="env/non-excluded-argv hit group"):
        _t1712_assert_no_path_token_hits(
            argv_leak,
            tokens=(("treatment-root-canary", treatment_canary),),
        )

    env_leak = copy.deepcopy(treatment)
    env_values = list(env_leak["env"])
    env_key, env_value = env_values[0]
    env_values[0] = (
        env_key,
        env_value + ":" + _T1712_TREATMENT_ROOT_CANARY,
    )
    env_leak["env"] = tuple(env_values)
    with pytest.raises(AssertionError, match="env/non-excluded-argv hit group"):
        _t1712_assert_no_path_token_hits(
            env_leak,
            tokens=(("treatment-root-canary", treatment_canary),),
        )


def _t325_run(fixture, run_root: Path, **overrides):
    arguments = {
        "trial_id": fixture.trial_id,
        "workloads": ["rr80"],
        "generations": 2,
        "provider_kind": "fixture",
        "run_root": run_root,
        "sub": "/unused",
        "do_build": False,
        "drive": _fake_drive,
        "preview": _fake_preview,
        "trial_manifest": fixture.manifest_path,
        "effective_preregistration": fixture.capability,
    }
    arguments.update(overrides)
    return A.run_trial(**arguments)


def _install_t325_legacy_freeze(fixture) -> None:
    relative = Path(A.s8b_ratified_freeze.V1_FREEZE_PATH)
    destination = fixture.repo / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes((_ROOT / relative).read_bytes())


def test_formal_profile_accepts_registered_effective_binding_via_formal_resolver(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    _install_t325_legacy_freeze(t325_registered_trial)
    monkeypatch.delitem(A.WORKLOADS, "rr80")
    calls = []
    load_launch_binding = A.trial_registry.load_launch_binding

    def observe_binding(**kwargs):
        calls.append(kwargs["trial_id"])
        return load_launch_binding(**kwargs)

    monkeypatch.setattr(
        A.trial_registry,
        "load_launch_binding",
        observe_binding,
    )
    report = _t325_run(
        t325_registered_trial,
        tmp_path / "formal-registered-effective",
        workload_profile=A.FORMAL_LEGACY_WORKLOAD_PROFILE,
    )

    assert report["status"] == "complete"
    assert report["launch_admission"]["mode"] == "registered-effective"
    assert A.resolve_workload_entry("rr80") is A.FORMAL_WORKLOADS["rr80"]
    assert calls
    assert set(calls) == {t325_registered_trial.trial_id}


def test_formal_profile_rejects_noncertifying_before_launch_admission_and_run_root(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    _install_t325_legacy_freeze(t325_registered_trial)

    def unexpected_launch_admission(**_kwargs):
        pytest.fail("formal non-certifying profile reached launch admission")

    monkeypatch.setattr(A, "_trial_launch_admission", unexpected_launch_admission)
    run_root = tmp_path / "formal-noncertifying-profile"
    with pytest.raises(
        A.AutonomousTrialError,
        match=(
            r"^formal workload profile is incompatible with "
            r"non-certifying launch admission$"
        ),
    ):
        _t325_run(
            t325_registered_trial,
            run_root,
            workload_profile=A.FORMAL_LEGACY_WORKLOAD_PROFILE,
            effective_preregistration=None,
            allow_formal_noncertifying=True,
        )
    assert not run_root.exists()


def test_formal_profile_effective_none_rejects_before_binding_and_run_root(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    _install_t325_legacy_freeze(t325_registered_trial)
    monkeypatch.setattr(
        A.s8c_preregistration,
        "effective_at",
        lambda *_args, **_kwargs: None,
    )

    def unexpected_binding(**_kwargs):
        pytest.fail("formal profile reached the P/C/H binding loader")

    monkeypatch.setattr(
        A.trial_registry,
        "load_launch_binding",
        unexpected_binding,
    )
    run_root = tmp_path / "formal-not-effective"
    with pytest.raises(
        A.AutonomousTrialError,
        match=(
            r"^formal launch is not admissible: effective "
            r"preregistration unavailable$"
        ),
    ):
        _t325_run(
            t325_registered_trial,
            run_root,
            workload_profile=A.FORMAL_LEGACY_WORKLOAD_PROFILE,
        )
    assert not run_root.exists()


def _t325_binding_fields(binding) -> dict[str, str]:
    return {
        "prereg_commit": binding.prereg_commit,
        "measurement_head": binding.measurement_head,
        "manifest_sha256": binding.manifest_sha256,
    }


def _t325_run_start(run_root: Path) -> dict:
    events = [
        json.loads(line)
        for line in (run_root / "attempts.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    starts = [event for event in events if event["event"] == "run-start"]
    assert len(starts) == 1
    return starts[0]


def test_prepare_campaign_identity_exactly_matches_existing_derivation(
    t325_registered_trial, monkeypatch,
) -> None:
    monkeypatch.setattr(A.trigger, "_lookup", lambda _tag: _T530_CONTRACT)
    context = _no_build_context()
    flags = A.WORKLOADS["rr80"]
    descriptor, descriptor_record = A._descriptor_for(flags)
    legacy_campaign = A._campaign_for(
        workload="rr80",
        entry=flags,
        descriptor=descriptor,
        descriptor_record=descriptor_record,
        trial_id=t325_registered_trial.trial_id,
        generations=2,
        contract=_T530_CONTRACT,
        build_context=context,
    )
    prepared = A._prepare_campaign_identity(
        workload="rr80",
        trial_id=t325_registered_trial.trial_id,
        generations=2,
        site=A.trigger.site_policy.OTHER,
        contract=_T530_CONTRACT,
        build_context=context,
    )
    assert prepared.descriptor == descriptor
    assert prepared.descriptor_record == descriptor_record
    assert prepared.campaign == legacy_campaign
    assert prepared.campaign_id == str(A.ident.campaign_id(legacy_campaign))
    run_root = Path("sentinel-run-root")
    assert run_root / "campaigns" / prepared.campaign_id == (
        run_root / "campaigns" / str(A.ident.campaign_id(legacy_campaign))
    )


def test_manifest_identity_preflight_does_not_consume_coder_authority(
    t325_registered_trial,
) -> None:
    authority = _coder_authority()
    admission = A._trial_launch_admission(
        trial_manifest=t325_registered_trial.manifest_path,
        trial_id=t325_registered_trial.trial_id,
        workloads=["rr80"],
        generations=2,
        allow_unregistered_exploratory=False,
        effective_preregistration=t325_registered_trial.capability,
    )
    assert admission.binding == t325_registered_trial.binding
    context = A.build_run_context(
        generator_id=A.GeneratorId.S8A_TRIGGER_SWEEP,
        coder_authority=authority,
    )
    arm_execution = A.trial_registry.bind_trial_arm(
        admission.binding,
        repository_root=t325_registered_trial.repo,
    )
    prepared = A._prepare_campaign_identity(
        workload="rr80",
        trial_id=t325_registered_trial.trial_id,
        generations=2,
        site=A.trigger.site_policy.OTHER,
        contract=_T530_CONTRACT,
        build_context=context,
        arm_execution=arm_execution,
    )
    assert prepared.campaign_id == admission.binding.campaign_id
    with pytest.raises(A.BuildAdmissionError, match="既に使用済み"):
        A.build_run_context(
            generator_id=A.GeneratorId.S8A_TRIGGER_SWEEP,
            coder_authority=authority,
        )


def test_t1333_manifest_identity_reuses_the_formal_entry_scale(
    t325_registered_trial,
) -> None:
    arm_execution = A.trial_registry.bind_trial_arm(
        t325_registered_trial.binding,
        repository_root=t325_registered_trial.repo,
    )
    prepared = A._prepare_manifest_campaign_identity(
        workload="rr80",
        trial_id=t325_registered_trial.trial_id,
        generations=2,
        site=A.trigger.site_policy.OTHER,
        contract=_T530_CONTRACT,
        build_context=_no_build_context(),
        resolved_arm_input=arm_execution.resolved_input,
    )
    entry = A.FORMAL_WORKLOADS["rr80"]
    assert prepared.campaign.search_config["records"] == entry["records"]
    assert prepared.campaign.search_config["threads"] == entry["threads"]
    assert prepared.campaign.search_config["ycsb"] == entry["ycsb"]
    assert prepared.perf.records == entry["records"]
    assert prepared.perf.threads == entry["threads"]
    assert prepared.perf.workload == entry["ycsb"]


def test_t1311_registered_identity_consumes_issued_arm_bytes(
    t325_registered_trial,
) -> None:
    arm_execution = A.trial_registry.bind_trial_arm(
        t325_registered_trial.binding,
        repository_root=t325_registered_trial.repo,
    )
    prepared = A._prepare_campaign_identity(
        workload="rr80",
        trial_id=t325_registered_trial.trial_id,
        generations=2,
        site=A.trigger.site_policy.OTHER,
        contract=_T530_CONTRACT,
        build_context=_no_build_context(),
        arm_execution=arm_execution,
    )
    record = A.trial_registry.arm_execution_record(arm_execution)
    assert set(record) == {
        "input_schema_version",
        "content_digest_sha256",
        "arm_binding_digest_sha256",
    }
    assert "arm" not in record
    assert prepared.descriptor == json.loads(
        arm_execution.canonical_input_bytes.decode("utf-8")
    )
    assert prepared.descriptor_record["output_sha256"] == (
        record["content_digest_sha256"]
    )
    assert prepared.descriptor_record["arm_binding_digest_sha256"] == (
        record["arm_binding_digest_sha256"]
    )
    assert prepared.campaign.search_config["arm_binding_digest_sha256"] == (
        record["arm_binding_digest_sha256"]
    )
    assert prepared.campaign.search_config["ycsb"] == (
        A.FORMAL_WORKLOADS["rr80"]["ycsb"]
    )
    assert prepared.campaign_id == t325_registered_trial.binding.campaign_id


def test_t1311_invocation_id_enforces_provider_limit() -> None:
    digest = "a" * 64
    invocation_id = A._invocation_id(
        arm="swapped",
        digest=digest,
        workload="rr80",
        generation=2,
        role="auditor",
    )
    assert invocation_id == (
        f"arm-swapped.exec-{digest}.rr80.g2.auditor"
    )
    assert len(invocation_id) <= 128
    with pytest.raises(A.AutonomousTrialError, match="provider 制約外"):
        A._invocation_id(
            arm="swapped",
            digest=digest,
            workload="w" * 60,
            generation=2,
            role="auditor",
        )


def test_t1311_registered_workload_binds_proposal_and_all_invocations(
    tmp_path, t325_registered_trial,
) -> None:
    admission = t325_registered_trial.admission
    arm_execution = A.trial_registry.bind_trial_arm(
        admission.binding,
        repository_root=t325_registered_trial.repo,
    )
    run_root = tmp_path / "registered-workload"
    run_root.mkdir()
    (run_root / "raw").mkdir()
    (run_root / "proposals").mkdir()
    journal = A.AttemptJournal(run_root / "attempts.jsonl")
    scope = A._RunScopeBinding(
        admission,
        A._RUN_SCOPE_SEAL,
        None,
        arm_execution,
    )
    token = A._ACTIVE_TRIAL_BINDING.set(scope)
    try:
        cell = A._run_workload(
            workload="rr80",
            generations=2,
            providers={
                role: A.FixtureRoleProvider(role) for role in A.ROLE_FILES
            },
            journal=journal,
            run_root=run_root,
            sub="/unused",
            do_build=False,
            cache_root="",
            trial_id=t325_registered_trial.trial_id,
            started_monotonic=time.monotonic(),
            max_wall_s=3600,
            drive=_fake_drive,
            preview=_fake_preview,
            build_context=_no_build_context(),
            gating_spec_snapshot=A.snapshot_gating_spec(A.GATING_SPEC),
        )
    finally:
        A._ACTIVE_TRIAL_BINDING.reset(token)
    digest = arm_execution.arm_binding_digest_sha256
    assert cell["descriptor_binding"]["arm_binding_digest_sha256"] == digest
    assert cell["workload_flags"] == A.FORMAL_WORKLOADS["rr80"]["ycsb"]
    assert cell["perf_config_scale"] == {
        "records": A.FORMAL_WORKLOADS["rr80"]["records"],
        "threads": A.FORMAL_WORKLOADS["rr80"]["threads"],
    }
    for generation in cell["generations"]:
        for role, event in generation["roles"].items():
            assert event["invocation_id"] == A._invocation_id(
                arm="on",
                digest=digest,
                workload="rr80",
                generation=generation["generation"],
                role=role,
            )
            assert event["arm_binding_digest_sha256"] == digest
        proposal = generation["proposal"]
        assert set(proposal) == {"path", "sha256", "digest"}
        assert proposal["digest"] == digest
        proposal_value = json.loads(Path(proposal["path"]).read_text("utf-8"))
        assert proposal_value["arm_binding_digest_sha256"] == digest
        assert hashlib.sha256(Path(proposal["path"]).read_bytes()).hexdigest() == (
            proposal["sha256"]
        )


def test_formal_registered_launch_requires_explicit_test_injection(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    monkeypatch.delitem(A.WORKLOADS, "rr80")
    run_root = tmp_path / "formal-default-selector-denied"
    with pytest.raises(
        A.AutonomousTrialError,
        match=r"^unknown workloads: \['rr80'\]$",
    ):
        _t325_run(t325_registered_trial, run_root)
    assert "rr80" in A.FORMAL_WORKLOADS
    assert not run_root.exists()


def test_formal_noncertifying_launch_requires_manifest_and_excludes_exploratory(
) -> None:
    common = {
        "trial_id": "formal-opt-in-boundary",
        "workloads": ["ycsb-a"],
        "generations": 1,
        "allow_unregistered_exploratory": False,
        "effective_preregistration": None,
    }
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=r"\[launch-admission\] formal non-certifying launch requires a registered manifest",
    ):
        A._trial_launch_admission(
            trial_manifest=None,
            allow_formal_noncertifying=True,
            **common,
        )

    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=r"\[launch-admission\].*mutually exclusive",
    ):
        A._trial_launch_admission(
            trial_manifest=None,
            allow_unregistered_exploratory=True,
            allow_formal_noncertifying=True,
            **{
                key: value
                for key, value in common.items()
                if key != "allow_unregistered_exploratory"
            },
        )


def test_formal_noncertifying_registered_workload_consumes_shared_slot(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    monkeypatch.delitem(A.WORKLOADS, "rr80")
    monkeypatch.setattr(
        A.s8c_preregistration,
        "validate_condition_freeze_at",
        lambda *_args: None,
    )

    run_root = tmp_path / "formal-noncertifying-run"
    report = _t325_run(
        t325_registered_trial,
        run_root,
        effective_preregistration=None,
        allow_formal_noncertifying=True,
    )

    assert report["status"] == "complete"
    assert report["launch_admission"]["mode"] == (
        "registered-formal-non-certifying"
    )
    assert report["launch_admission"]["certifying"] is False
    assert report["slot_id"] == _t325_run_start(run_root)["slot_id"]
    lifecycle_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_LIFECYCLE_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    assert lifecycle_rows[0]["mode"] == "registered-formal-non-certifying"
    assert lifecycle_rows[0]["activation_report_digest_sha256"] is None
    attempt_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_ATTEMPT_REGISTRY_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    assert [
        row["slot_id"]
        for row in attempt_rows
        if row.get("event") == "start"
    ] == [report["slot_id"]]


@pytest.mark.parametrize(
    "formal_noncertifying",
    [False, True],
    ids=["registered-effective", "registered-formal-non-certifying"],
)
def test_registered_modes_route_reserve_and_terminal_only_through_formal_facades(
    formal_noncertifying,
    tmp_path,
    monkeypatch,
    t325_registered_trial,
) -> None:
    if formal_noncertifying:
        monkeypatch.delitem(A.WORKLOADS, "rr80")
        monkeypatch.setattr(
            A.s8c_preregistration,
            "validate_condition_freeze_at",
            lambda *_args: None,
        )
    original_reserve = A.trial_registry.reserve_formal_attempt_slot
    original_terminal = A.trial_registry.record_formal_attempt_terminal
    calls = {"reserve": 0, "terminal": 0}

    def observe_reserve(**kwargs):
        calls["reserve"] += 1
        return original_reserve(**kwargs)

    def observe_terminal(*args, **kwargs):
        calls["terminal"] += 1
        return original_terminal(*args, **kwargs)

    def reject_compat(*_args, **_kwargs):
        pytest.fail("registered production reached a compatibility attempt facade")

    monkeypatch.setattr(
        A.trial_registry, "reserve_formal_attempt_slot", observe_reserve,
    )
    monkeypatch.setattr(
        A.trial_registry, "record_formal_attempt_terminal", observe_terminal,
    )
    monkeypatch.setattr(A.trial_registry, "reserve_attempt_slot", reject_compat)
    monkeypatch.setattr(A.trial_registry, "record_attempt_terminal", reject_compat)

    run_kwargs = {}
    if formal_noncertifying:
        run_kwargs.update({
            "effective_preregistration": None,
            "allow_formal_noncertifying": True,
        })
    report = _t325_run(
        t325_registered_trial,
        tmp_path / f"strict-route-{formal_noncertifying}",
        **run_kwargs,
    )

    assert report["status"] == "complete"
    assert calls == {"reserve": 1, "terminal": 1}


def test_run_trial_routes_exactly_five_terminal_sites_through_formal_helper(
) -> None:
    tree = ast.parse(Path(A.__file__).read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    run_trial = functions["run_trial"]
    helper = functions["_record_attempt_terminal_for_run"]
    helper_calls = [
        call
        for call in ast.walk(run_trial)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "_record_attempt_terminal_for_run"
    ]
    assert len(helper_calls) == 5

    facade_names = {
        "record_attempt_terminal",
        "record_formal_attempt_terminal",
    }

    def qualified_facade_calls(function: ast.FunctionDef) -> list[ast.Call]:
        return [
            call
            for call in ast.walk(function)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "trial_registry"
            and call.func.attr in facade_names
        ]

    helper_facades = qualified_facade_calls(helper)
    assert len(helper_facades) == 1
    assert helper_facades[0].func.attr == "record_formal_attempt_terminal"
    assert all(
        not qualified_facade_calls(function)
        for name, function in functions.items()
        if name != "_record_attempt_terminal_for_run"
    )


def test_exploratory_run_does_not_reach_any_attempt_facade(
    tmp_path, monkeypatch,
) -> None:
    def reject_attempt(*_args, **_kwargs):
        pytest.fail("exploratory execution reached an attempt facade")

    for name in (
        "reserve_attempt_slot",
        "reserve_formal_attempt_slot",
        "record_attempt_terminal",
        "record_formal_attempt_terminal",
    ):
        monkeypatch.setattr(A.trial_registry, name, reject_attempt)

    report = A.run_trial(
        trial_id="t1611-exploratory-routing",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "t1611-exploratory-routing",
        sub="/unused",
        do_build=False,
        providers={role: A.FixtureRoleProvider(role) for role in A.ROLE_FILES},
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "complete"
    assert report["launch_admission"]["mode"] == (
        "explicit-unregistered-exploratory"
    )


def test_registered_partial_producer_failure_is_fail_closed_without_terminal(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    run_root = tmp_path / "t1611-partial-fail-closed"
    original_forbid = A.trial_registry.forbid_trial_restart
    forbid_calls: list[str] = []

    def observe_forbid(token):
        forbid_calls.append(token.trial_id)
        return original_forbid(token)

    def partial_report(**_kwargs):
        return {
            "status": "partial",
            "attempt_journal": str(run_root / "attempts.jsonl"),
            "cells": [],
        }

    monkeypatch.setattr(
        A.trial_registry, "forbid_trial_restart", observe_forbid,
    )
    monkeypatch.setattr(A, "_finish_trial", partial_report)
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=r"terminal failure reason differs from classification",
    ) as captured:
        _t325_run(t325_registered_trial, run_root)
    assert any(
        "terminal-record=TrialRegistryError" in note
        for note in getattr(captured.value, "__notes__", ())
    )
    assert forbid_calls == [t325_registered_trial.trial_id]

    attempt_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_ATTEMPT_REGISTRY_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    assert not any(row.get("event") == "terminal" for row in attempt_rows)
    lifecycle_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_LIFECYCLE_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    assert [row["event"] for row in lifecycle_rows] == ["start"]
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=r"\[lifecycle-start-once\] ",
    ):
        _t325_run(
            t325_registered_trial,
            tmp_path / "t1611-partial-fail-closed-rerun",
        )


def test_registered_formal_noncertifying_build_crash_is_indeterminate(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    monkeypatch.setattr(
        A.s8c_preregistration,
        "validate_condition_freeze_at",
        lambda *_args: None,
    )
    monkeypatch.setattr(
        A,
        "assert_autonomous_trial_completeness",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        A,
        "assert_autonomous_trial_execution_digest_chain",
        lambda **_kwargs: None,
    )
    factory = A.exploration_campaign_layout
    monkeypatch.setattr(
        A,
        "exploration_campaign_layout",
        lambda campaign_id: factory(campaign_id, str(tmp_path)),
    )

    def fake_render(campaign_root, persisted, *, output_root):
        assert persisted == campaign_root / "reports" / "layer3_report.json"
        assert output_root == campaign_root.parent.parent
        return {
            "admission_decision": {
                "schema_version": "campaign-artifact-admission-decision/v1",
                "admission_status": "admitted",
                "classification": "admitted-new-schema",
            },
        }

    monkeypatch.setattr(A.layer3_report, "render", fake_render)
    monkeypatch.setattr(A, "assert_campaign_layer3_chain", lambda **_kwargs: None)

    def drive_build(
        cfg, perf, planner, coder, auditor, prior, sub, do_build, *, layout,
        **_kwargs,
    ):
        assert do_build is True
        (Path(layout.root) / "reports").mkdir(parents=True, exist_ok=True)
        return {
            "outcome": "dry-pass",
            "variant": None,
            "stop_reason": "converged",
            "iteration": 1,
            "ran": True,
            "critic_digest_generated": False,
            "trigger_gate_binding_commitment": "b" * 64,
        }

    providers = {
        role: _RecordingFixture(role)
        for role in ("planner", "coder", "auditor")
    }
    run_root = tmp_path / "formal-noncertifying-build-crash"
    report = _t325_run(
        t325_registered_trial,
        run_root,
        effective_preregistration=None,
        allow_formal_noncertifying=True,
        do_build=True,
        coder_authority=_coder_authority(),
        providers=providers,
        drive=drive_build,
    )

    assert report["status"] == "partial"
    assert report["do_build"] is True
    assert report["launch_admission"]["mode"] == (
        "registered-formal-non-certifying"
    )
    assert report["cells"][0]["stop_reason"] == "supervisor-error"
    assert report["lifecycle_terminal_status"] == "indeterminate"
    attempt_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_ATTEMPT_REGISTRY_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    attempt_terminal = next(
        row for row in attempt_rows if row.get("event") == "terminal"
    )
    assert attempt_terminal["terminal_status"] == "not-consumed"
    assert attempt_terminal["report_sha256"] is None
    assert attempt_terminal["observation_sha256"] is None
    assert attempt_terminal["primary_value"] is None
    lifecycle_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_LIFECYCLE_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    assert lifecycle_rows[-1]["terminal_status"] == "indeterminate"


def test_formal_noncertifying_cli_skips_effective_derivation_and_forwards_opt_in(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    captured: dict[str, dict[str, Any]] = {}
    monkeypatch.setattr(A, "assert_pinned_clean", lambda *_args, **_kwargs: None)

    def capture_admission(**kwargs):
        captured["admission"] = kwargs
        return t325_registered_trial.admission

    def capture_run_trial(**kwargs):
        captured["run_trial"] = kwargs
        return {"status": "complete", "cells": []}

    def forbidden_effective_at(*_args, **_kwargs):
        pytest.fail("formal non-certifying CLI derived effective preregistration")

    monkeypatch.setattr(A, "_trial_launch_admission", capture_admission)
    monkeypatch.setattr(A, "run_trial", capture_run_trial)
    monkeypatch.setattr(
        A.s8c_preregistration,
        "effective_at",
        forbidden_effective_at,
    )

    assert A.main([
        "--trial-id", t325_registered_trial.trial_id,
        "--trial-manifest", str(t325_registered_trial.manifest_path),
        "--provider", "fixture",
        "--workloads", "rr80",
        "--max-generations", "2",
        "--no-build",
        "--allow-formal-noncertifying",
        "--ccbench-dir", str(tmp_path / "ccbench"),
        "--run-root", str(tmp_path / "run"),
    ]) == 0
    assert captured["admission"]["allow_formal_noncertifying"] is True
    assert captured["admission"]["effective_preregistration"] is None
    assert captured["run_trial"]["allow_formal_noncertifying"] is True
    assert captured["run_trial"]["effective_preregistration"] is None


def test_p8_m25_manifest_run_burns_exact_binding_without_arm_fields(
    tmp_path, t325_registered_trial,
) -> None:
    run_root = tmp_path / "manifest-run"
    report = _t325_run(t325_registered_trial, run_root)
    expected = _t325_binding_fields(t325_registered_trial.binding)
    assert report["status"] == "complete"
    assert {field: report[field] for field in expected} == expected
    assert {field: _t325_run_start(run_root)[field] for field in expected} == expected
    assert report["launch_admission"] == _t325_run_start(run_root)["launch_admission"]
    assert report["launch_admission"]["certifying"] is False
    arm_execution = A.trial_registry.bind_trial_arm(
        t325_registered_trial.binding,
        repository_root=t325_registered_trial.repo,
    )
    expected_arm_execution = A.trial_registry.arm_execution_record(
        arm_execution
    )
    assert report["arm_execution"] == expected_arm_execution
    assert _t325_run_start(run_root)["arm_execution"] == expected_arm_execution
    assert "arm" not in report["arm_execution"]
    assert "arm" not in report
    assert "holdout" not in report


def test_registered_producer_self_check_runs_execution_digest_chain(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    observed: list[dict[str, object]] = []

    def observe_chain(**kwargs) -> None:
        observed.append(kwargs)

    monkeypatch.setattr(
        A,
        "assert_autonomous_trial_execution_digest_chain",
        observe_chain,
    )
    run_root = tmp_path / "registered-chain-self-check"
    report = _t325_run(t325_registered_trial, run_root)
    assert observed == [{
        "report": report,
        "attempt_journal": run_root / "attempts.jsonl",
    }]


def test_exploratory_producer_self_check_skips_execution_digest_chain(
    tmp_path, monkeypatch,
) -> None:
    def forbidden_chain(**_kwargs) -> None:
        pytest.fail("exploratory producer invoked registered digest chain")

    monkeypatch.setattr(
        A,
        "assert_autonomous_trial_execution_digest_chain",
        forbidden_chain,
    )
    report = A.run_trial(
        trial_id="exploratory-chain-self-check",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "exploratory-chain-self-check",
        sub="/unused",
        do_build=False,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "complete"


def test_formal_start_is_recorded_before_run_root_and_blocks_other_root(
    tmp_path,
    monkeypatch,
    t325_registered_trial,
) -> None:
    first_root = tmp_path / "formal-first-root"
    original_reject = A.trial_registry.reject_started_trial
    original = A.trial_registry.record_trial_start_once
    current_root: list[Path | None] = [None]
    reject_observations: list[bool] = []
    observations: list[bool] = []

    def observe_reject(**kwargs):
        assert current_root[0] is not None
        reject_observations.append(current_root[0].exists())
        return original_reject(**kwargs)

    def observe_start(**kwargs):
        observations.append(Path(kwargs["run_root"]).exists())
        return original(**kwargs)

    monkeypatch.setattr(
        A.trial_registry,
        "reject_started_trial",
        observe_reject,
    )
    monkeypatch.setattr(
        A.trial_registry,
        "record_trial_start_once",
        observe_start,
    )
    current_root[0] = first_root
    first = _t325_run(t325_registered_trial, first_root)
    assert first["status"] == "complete"
    assert reject_observations == [False]
    assert observations == [False]

    second_root = tmp_path / "formal-second-root"
    current_root[0] = second_root
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=r"\[lifecycle-start-once\] ",
    ):
        _t325_run(t325_registered_trial, second_root)
    assert reject_observations == [False, False]
    assert observations == [False]
    assert not second_root.exists()


def test_registered_slot_is_reserved_before_first_performance_observation(
    tmp_path,
    monkeypatch,
    t325_registered_trial,
) -> None:
    origin_request, origin_producer = _origin_public_inputs(
        tmp_path, monkeypatch, t325_registered_trial
    )
    events: list[str] = []
    original_reserve = A._reserve_registered_attempt_slot
    original_classify = A.trial_registry.classify_attempt
    original_observation_start = A.trial_registry.begin_attempt_observation
    original_read = reflux_origin_client.OriginLedgerClient.read_origin
    original_derive = A._derive_origin_campaign_runs
    original_build_envelope = A._build_origin_recovery_envelope
    original_write_envelope = (
        A.reflux_origin_topology.write_recovery_envelope_create_only
    )
    original_lifecycle_start = A.trial_registry.record_trial_start_once

    def observe_reservation(**kwargs):
        events.append("slot-reservation")
        return original_reserve(**kwargs)

    def observe_classification(*args, **kwargs):
        events.append("classification")
        return original_classify(*args, **kwargs)

    def observe_observation_start(*args, **kwargs):
        events.append("observation-start")
        return original_observation_start(*args, **kwargs)

    def observe_origin_read(self, capability):
        events.append("origin-read")
        return original_read(self, capability)

    def observe_derivation(*args, **kwargs):
        events.append("identity-derivation")
        return original_derive(*args, **kwargs)

    def observe_envelope_build(**kwargs):
        events.append("envelope-build")
        return original_build_envelope(**kwargs)

    def observe_envelope_write(**kwargs):
        events.append("envelope-write")
        return original_write_envelope(**kwargs)

    def observe_lifecycle_start(**kwargs):
        events.append("lifecycle-start")
        envelope_path = Path(kwargs["run_root"]) / "origin" / (
            "recovery-envelope.json"
        )
        assert kwargs["origin_run_plan_sha256"] == hashlib.sha256(
            envelope_path.read_bytes()
        ).hexdigest()
        if "origin_run_plan_sha256" not in inspect.signature(
            original_lifecycle_start
        ).parameters:
            kwargs.pop("origin_run_plan_sha256")
        return original_lifecycle_start(**kwargs)

    def observe_performance(*args, **kwargs):
        events.append("performance-observation")
        return _fake_drive(*args, **kwargs)

    monkeypatch.setattr(A, "_reserve_registered_attempt_slot", observe_reservation)
    monkeypatch.setattr(
        A.trial_registry, "classify_attempt", observe_classification,
    )
    monkeypatch.setattr(
        A.trial_registry,
        "begin_attempt_observation",
        observe_observation_start,
    )
    monkeypatch.setattr(
        reflux_origin_client.OriginLedgerClient,
        "read_origin",
        observe_origin_read,
    )
    monkeypatch.setattr(A, "_derive_origin_campaign_runs", observe_derivation)
    monkeypatch.setattr(
        A, "_build_origin_recovery_envelope", observe_envelope_build,
    )
    monkeypatch.setattr(
        A.reflux_origin_topology,
        "write_recovery_envelope_create_only",
        observe_envelope_write,
    )
    monkeypatch.setattr(
        A.trial_registry, "record_trial_start_once", observe_lifecycle_start,
    )
    report = _t325_run(
        t325_registered_trial,
        tmp_path / "reservation-before-performance",
        drive=observe_performance,
        origin_binding_request=origin_request,
        origin_producer_inputs=origin_producer,
    )
    assert report["status"] == "complete"
    assert events[0] == "slot-reservation"
    assert events.index("classification") > events.index("slot-reservation")
    assert events.index("origin-read") > events.index("classification")
    assert events.index("identity-derivation") > events.index("origin-read")
    assert events.index("envelope-build") > events.index("identity-derivation")
    assert events.index("envelope-write") > events.index("envelope-build")
    assert events.index("lifecycle-start") > events.index("envelope-write")
    assert events.index("observation-start") > events.index("classification")
    assert events.index("observation-start") > events.index("lifecycle-start")
    assert events.index("performance-observation") > events.index(
        "observation-start"
    )


def _s8c_budget_test_setup(tmp_path, monkeypatch, scheduled_holdouts):
    manifest_sha256 = "a" * 64
    manifest_path = tmp_path / "manifest.json"
    monkeypatch.setattr(
        A.trial_registry,
        "load_trial_manifest",
        lambda _path: SimpleNamespace(sha256=manifest_sha256),
    )
    cells = tuple(
        A.ReservationCell(
            cell_id=f"{holdout}-on",
            holdout=holdout,
            arm="on",
            reserved_bench_s=1.0,
        )
        for holdout in scheduled_holdouts
    )
    schedule = {
        "ledger_path": tmp_path / "budget-ledger.json",
        "schedule_sha256": "b" * 64,
        "cells": cells,
        "limits": A.BudgetLimits(
            total_bench_s=2.0,
            per_arm_bench_s={"on": 2.0, "off": 2.0, "swapped": 2.0},
            per_holdout_bench_s={"H1": 1.0, "H2": 1.0},
        ),
    }
    monkeypatch.setattr(
        A,
        "_load_s8c_schedule_authority",
        lambda *, root: schedule,
    )
    ratified_freeze = A.s8b_ratified_freeze.RatifiedFreeze(
        document={
            "freeze_sha256": "c" * 64,
            "holdouts": {
                "rr80": {"candidate_id": "H1"},
                "rr20": {"candidate_id": "H2"},
            },
        },
        sha256="d" * 64,
        generation_number=1,
        activation_head="e" * 40,
        generation_commit="f" * 40,
    )
    admission = SimpleNamespace(
        mode="registered-effective",
        binding=SimpleNamespace(manifest_sha256=manifest_sha256),
    )
    return admission, manifest_path, ratified_freeze, schedule


def test_prepare_s8c_budget_inputs_accepts_matching_ratified_holdout_ids(
    tmp_path, monkeypatch,
) -> None:
    admission, manifest_path, ratified_freeze, schedule = _s8c_budget_test_setup(
        tmp_path, monkeypatch, ("H1", "H2"),
    )

    inputs = A._prepare_s8c_budget_inputs(
        admission=admission,
        trial_manifest=manifest_path,
        ratified_freeze=ratified_freeze,
    )

    assert inputs.cells == schedule["cells"]
    assert {cell.holdout for cell in inputs.cells} == {"H1", "H2"}


def test_prepare_s8c_budget_inputs_rejects_mismatched_holdout_id_set(
    tmp_path, monkeypatch,
) -> None:
    admission, manifest_path, ratified_freeze, _schedule = _s8c_budget_test_setup(
        tmp_path, monkeypatch, ("H1",),
    )

    with pytest.raises(
        A.AutonomousTrialError,
        match="8c schedule holdout set does not match the ratified freeze holdout set",
    ):
        A._prepare_s8c_budget_inputs(
            admission=admission,
            trial_manifest=manifest_path,
            ratified_freeze=ratified_freeze,
        )


def test_registered_budget_insufficient_closes_as_not_consumed(
    tmp_path,
    monkeypatch,
    t325_registered_trial,
) -> None:
    ledger = SimpleNamespace(
        manifest_sha256="a" * 64,
        freeze_sha256="b" * 64,
        schedule_sha256="c" * 64,
        ratified_generation_sha256="d" * 64,
        reservation=SimpleNamespace(state="insufficient"),
    )
    budget_inputs = SimpleNamespace(
        ledger_path=tmp_path / "budget-ledger.json",
        manifest_sha256=ledger.manifest_sha256,
        freeze_sha256=ledger.freeze_sha256,
        schedule_sha256=ledger.schedule_sha256,
        ratified_generation_sha256=ledger.ratified_generation_sha256,
        cells=(),
        limits=object(),
    )
    monkeypatch.setattr(A, "load_ratified_freeze", lambda _root: object())
    monkeypatch.setattr(
        A,
        "_prepare_s8c_budget_inputs",
        lambda **_kwargs: budget_inputs,
    )
    monkeypatch.setattr(A, "reserve_all_cells", lambda *_args, **_kwargs: ledger)
    monkeypatch.setattr(
        A,
        "symmetric_indeterminate",
        lambda _ledger: frozenset({"fixture-cell"}),
    )
    report = _t325_run(
        t325_registered_trial,
        tmp_path / "budget-insufficient",
        do_build=True,
        drive=A.trigger.drive_iteration,
        coder_authority=_coder_authority(),
    )
    assert report["status"] == "partial"
    assert report["lifecycle_terminal_status"] == "indeterminate"
    attempt_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_ATTEMPT_REGISTRY_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    attempt_terminal = next(
        row for row in attempt_rows if row.get("event") == "terminal"
    )
    assert attempt_terminal["terminal_status"] == "not-consumed"
    assert attempt_terminal["report_sha256"] is None
    assert attempt_terminal["observation_sha256"] is None
    assert attempt_terminal["primary_value"] is None
    lifecycle_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_LIFECYCLE_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    assert lifecycle_rows[-1]["terminal_status"] == "indeterminate"


def test_formal_post_start_io_failure_records_indeterminate_and_stays_consumed(
    tmp_path,
    monkeypatch,
    t325_registered_trial,
) -> None:
    run_root = tmp_path / "formal-post-start-failure"
    original_forbid = A.trial_registry.forbid_trial_restart
    forbid_calls: list[str] = []

    def observe_forbid(token):
        forbid_calls.append(token.trial_id)
        return original_forbid(token)

    monkeypatch.setattr(
        A.trial_registry,
        "forbid_trial_restart",
        observe_forbid,
    )

    def fail_namespace(_path: str) -> None:
        raise OSError("fixture namespace I/O failure")

    monkeypatch.setattr(A, "ensure_exploration_namespace", fail_namespace)
    with pytest.raises(OSError, match="fixture namespace I/O failure"):
        _t325_run(t325_registered_trial, run_root)

    lifecycle = t325_registered_trial.repo / A.trial_registry.DEFAULT_LIFECYCLE_PATH
    rows = [json.loads(line) for line in lifecycle.read_text().splitlines()]
    assert [row["event"] for row in rows] == ["start", "terminal"]
    attempt_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_ATTEMPT_REGISTRY_PATH
        ).read_text().splitlines()
    ]
    attempt_terminal = next(
        row for row in attempt_rows if row.get("event") == "terminal"
    )
    assert rows[-1] == {
        "schema_version": A.trial_registry.LIFECYCLE_SCHEMA_VERSION,
        "event": "terminal",
        "trial_id": t325_registered_trial.trial_id,
        "terminal_status": "indeterminate",
        "report_sha256": None,
        "attempt_journal_sha256": None,
        "prereg_commit": attempt_terminal["prereg_content_commit"],
        "prereg_content_commit": attempt_terminal["prereg_content_commit"],
        "prereg_effective_commit": attempt_terminal["prereg_effective_commit"],
        "slot_id": attempt_terminal["slot_id"],
        "classification_receipt_sha256": attempt_terminal[
            "classification_receipt_sha256"
        ],
        "raw_output_sha256": attempt_terminal["raw_output_sha256"],
    }
    assert forbid_calls == [t325_registered_trial.trial_id]
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=r"\[lifecycle-start-once\] ",
    ):
        _t325_run(t325_registered_trial, tmp_path / "formal-rerun-denied")


def test_formal_terminal_write_failure_is_explicit_and_does_not_allow_rerun(
    tmp_path,
    monkeypatch,
    t325_registered_trial,
) -> None:
    monkeypatch.setattr(
        A,
        "ensure_exploration_namespace",
        lambda _path: (_ for _ in ()).throw(OSError("original I/O failure")),
    )
    original_forbid = A.trial_registry.forbid_trial_restart
    forbid_calls: list[str] = []

    def observe_forbid(token):
        forbid_calls.append(token.trial_id)
        return original_forbid(token)

    monkeypatch.setattr(
        A.trial_registry,
        "forbid_trial_restart",
        observe_forbid,
    )
    original_terminal = A.trial_registry.record_trial_terminal
    monkeypatch.setattr(
        A.trial_registry,
        "record_trial_terminal",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("terminal I/O failure")
        ),
    )
    with pytest.raises(OSError, match="original I/O failure") as captured:
        _t325_run(t325_registered_trial, tmp_path / "terminal-write-failure")
    assert any(
        "terminal-record=OSError" in note
        for note in getattr(captured.value, "__notes__", ())
    )
    assert forbid_calls == [t325_registered_trial.trial_id]

    monkeypatch.setattr(A.trial_registry, "record_trial_terminal", original_terminal)
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=r"\[lifecycle-start-once\] ",
    ):
        _t325_run(t325_registered_trial, tmp_path / "terminal-write-rerun")


def test_formal_forbid_failure_still_records_indeterminate_terminal(
    tmp_path,
    monkeypatch,
    t325_registered_trial,
) -> None:
    monkeypatch.setattr(
        A,
        "ensure_exploration_namespace",
        lambda _path: (_ for _ in ()).throw(OSError("original crash")),
    )
    monkeypatch.setattr(
        A.trial_registry,
        "forbid_trial_restart",
        lambda _token: (_ for _ in ()).throw(
            OSError("restart bookkeeping failure")
        ),
    )

    with pytest.raises(OSError, match="original crash") as captured:
        _t325_run(t325_registered_trial, tmp_path / "forbid-write-failure")
    assert any(
        "restart-forbid=OSError" in note
        for note in getattr(captured.value, "__notes__", ())
    )

    lifecycle = t325_registered_trial.repo / A.trial_registry.DEFAULT_LIFECYCLE_PATH
    rows = [json.loads(line) for line in lifecycle.read_text().splitlines()]
    assert [row["event"] for row in rows] == ["start", "terminal"]
    assert rows[-1]["terminal_status"] == "indeterminate"


def test_indeterminate_note_fallback_replaces_non_list_and_reraises_original(
    monkeypatch,
) -> None:
    class PathologicalCrash(BaseException):
        add_note = None

    cause = PathologicalCrash("original crash")
    cause.__notes__ = "not-a-list"
    monkeypatch.setattr(
        A.trial_registry,
        "forbid_trial_restart",
        lambda _token: (_ for _ in ()).throw(OSError("restart failure")),
    )
    monkeypatch.setattr(
        A.trial_registry,
        "record_trial_terminal",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("terminal failure")
        ),
    )

    with pytest.raises(PathologicalCrash) as captured:
        A.mark_experiment_indeterminate(
            object(),
            cause=cause,
            experiment_status="indeterminate",
            remaining_cells=("ycsb-a",),
        )

    assert captured.value is cause
    assert isinstance(cause.__notes__, list)
    assert any(
        "restart-forbid=OSError" in note for note in cause.__notes__
    )
    assert any(
        "terminal-record=OSError" in note for note in cause.__notes__
    )


def test_p9_exploratory_run_with_absent_registry_preserves_report_shape(
    tmp_path, monkeypatch,
) -> None:
    repo = tmp_path / "repo-without-registry"
    repo.mkdir()
    _t325_git(repo, "init")
    _t325_git(repo, "config", "user.name", "Exploratory Fixture")
    _t325_git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    _t325_git(repo, "add", "seed.txt")
    _t325_git(repo, "commit", "-m", "seed")
    monkeypatch.setattr(A, "ROOT", repo)

    def manifest_gate_must_not_run(*args, **kwargs):
        pytest.fail("manifest gate ran for an exploratory launch")

    monkeypatch.setattr(
        A.trial_registry, "load_launch_binding", manifest_gate_must_not_run
    )
    run_root = tmp_path / "exploratory-run"
    report = A.run_trial(
        trial_id="unregistered-exploratory",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert set(report) == {
        "schema_version", "trial_id", "status", "started_at", "finished_at",
        "provider", "do_build", "workloads_requested",
        "generation_budget_per_workload", "stop_policy", "claim_scope",
        "attempt_journal", "launch_admission", "cells",
        "attempt_journal_sha256",
        "honest_accounting", "honest_accounting_authority",
        "generation_driver", "gating_spec_sha256",
    }
    assert report["launch_admission"]["certifying"] is False
    assert _t325_run_start(run_root)["launch_admission"] == report["launch_admission"]
    assert not ({"prereg_commit", "measurement_head", "manifest_sha256"} & report.keys())


def test_p9_prime_m27_prime_existing_registry_unregistered_exploratory_passes(
    tmp_path, t325_registered_trial,
) -> None:
    run_root = tmp_path / "unregistered-with-registry"
    report = A.run_trial(
        trial_id="another-exploratory-id",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "complete"
    binding_fields = {"prereg_commit", "measurement_head", "manifest_sha256"}
    assert not (binding_fields & report.keys())
    assert not (binding_fields & _t325_run_start(run_root).keys())


def test_manifestless_launch_is_rejected_by_default_before_run_root(
    tmp_path,
) -> None:
    run_root = tmp_path / "default-denied"
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=r"\[u4-exploratory-opt-in\] ",
    ):
        A.run_trial(
            trial_id="default-denied-before-artifacts",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="fixture",
            run_root=run_root,
            sub="/unused",
            do_build=False,
        )
    assert not run_root.exists()


def test_public_cli_holdout_opt_in_reaches_u4_gate_without_workload_patch(
    tmp_path,
    monkeypatch,
) -> None:
    repo = tmp_path / "holdout-cli-repo"
    repo.mkdir()
    _t325_git(repo, "init")
    _t325_git(repo, "config", "user.name", "Holdout CLI Fixture")
    _t325_git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    _t325_git(repo, "add", "seed.txt")
    _t325_git(repo, "commit", "-m", "seed")
    monkeypatch.setattr(A, "ROOT", repo)
    run_root = tmp_path / "holdout-cli-run"
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=r"\[u4-holdout-workload\] ",
    ):
        A.main([
            "--trial-id", "holdout-cli-denied",
            "--provider", "fixture",
            "--workloads", "rr80",
            "--no-build",
            "--allow-unregistered-exploratory",
            "--ccbench-dir", str(tmp_path / "ccbench"),
            "--run-root", str(run_root),
        ])
    assert "rr80" not in A.WORKLOADS
    assert not run_root.exists()


def test_m04_programmatic_holdout_reaches_u4_gate_before_unknown_workload(
    tmp_path,
    monkeypatch,
) -> None:
    repo = tmp_path / "holdout-programmatic-repo"
    repo.mkdir()
    _t325_git(repo, "init")
    _t325_git(repo, "config", "user.name", "Holdout Programmatic Fixture")
    _t325_git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    _t325_git(repo, "add", "seed.txt")
    _t325_git(repo, "commit", "-m", "seed")
    monkeypatch.setattr(A, "ROOT", repo)
    run_root = tmp_path / "holdout-programmatic-run"
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=(r"\[u4-holdout-workload\] holdout workloads cannot use "
               r"exploratory admission: \['rr80'\]$"),
    ):
        A.run_trial(
            trial_id="holdout-programmatic-denied",
            workloads=["rr80"],
            generations=1,
            provider_kind="fixture",
            run_root=run_root,
            sub="/unused",
            do_build=False,
            allow_unregistered_exploratory=True,
        )
    assert "rr80" not in A.WORKLOADS
    assert not run_root.exists()


def test_p10_cli_manifest_gate_precedes_build_preparation_and_forwards_manifest(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    sequence = []
    original_load = A.trial_registry.load_launch_binding
    original_campaign = A.trial_registry.assert_campaign_binding

    def observed_load(**kwargs):
        sequence.append("registry-gate")
        return original_load(**kwargs)

    def observed_campaign(binding, *, arm_execution, actual_campaign_id):
        sequence.append("campaign-gate")
        return original_campaign(
            binding,
            arm_execution=arm_execution,
            actual_campaign_id=actual_campaign_id,
        )

    def observed_preparation(*args, **kwargs):
        sequence.append("build-preparation")

    captured = {}

    def capture_run_trial(**kwargs):
        sequence.append("run-trial")
        captured.update(kwargs)
        return {"status": "complete", "cells": []}

    monkeypatch.setattr(A.trial_registry, "load_launch_binding", observed_load)
    monkeypatch.setattr(A.trial_registry, "assert_campaign_binding", observed_campaign)
    monkeypatch.setattr(A, "assert_pinned_clean", observed_preparation)
    monkeypatch.setattr(A, "run_trial", capture_run_trial)
    assert A.main([
        "--trial-id", t325_registered_trial.trial_id,
        "--trial-manifest", str(t325_registered_trial.manifest_path),
        "--provider", "fixture",
        "--workloads", "rr80",
        "--max-generations", "2",
        "--no-build",
        "--ccbench-dir", str(tmp_path / "ccbench"),
        "--run-root", str(tmp_path / "run"),
    ]) == 0
    assert sequence == [
        "registry-gate", "campaign-gate", "build-preparation", "run-trial",
    ]
    assert captured["trial_manifest"] == t325_registered_trial.manifest_path
    assert captured["trial_admission"].binding == t325_registered_trial.binding
    assert captured["effective_preregistration"] is t325_registered_trial.capability


def test_cli_rejects_simultaneous_exploratory_and_formal_noncertifying_opt_ins(
    tmp_path, t325_registered_trial,
) -> None:
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=r"\[launch-admission\].*mutually exclusive",
    ):
        A.main([
            "--trial-id", t325_registered_trial.trial_id,
            "--trial-manifest", str(t325_registered_trial.manifest_path),
            "--provider", "fixture",
            "--workloads", "rr80",
            "--max-generations", "2",
            "--no-build",
            "--allow-unregistered-exploratory",
            "--allow-formal-noncertifying",
            "--ccbench-dir", str(tmp_path / "ccbench"),
            "--run-root", str(tmp_path / "run"),
        ])


def test_t1185_m5_cli_default_generation_is_rejected_before_identity_or_run_root(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    def downstream(*args, **kwargs):
        pytest.fail("generation mismatch reached campaign identity or artifact work")

    monkeypatch.setattr(A, "build_run_context", downstream)
    monkeypatch.setattr(A, "_prepare_campaign_identity", downstream)
    monkeypatch.setattr(A, "assert_pinned_clean", downstream)
    monkeypatch.setattr(A, "run_trial", downstream)
    run_root = tmp_path / "t1185-m5-run"
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=r"\[generation-binding\] runtime generations differs",
    ):
        A.main([
            "--trial-id", t325_registered_trial.trial_id,
            "--trial-manifest", str(t325_registered_trial.manifest_path),
            "--provider", "fixture",
            "--workloads", "rr80",
            "--no-build",
            "--ccbench-dir", str(tmp_path / "ccbench"),
            "--run-root", str(run_root),
        ])
    assert not run_root.exists()


def test_t1185_pc_exploratory_generation_one_still_passes(
    tmp_path, t325_registered_trial,
) -> None:
    run_root = tmp_path / "t1185-pc-run"
    report = A.run_trial(
        trial_id="t1185-pc-exploratory",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        drive=_fake_drive,
        preview=_fake_preview,
        allow_unregistered_exploratory=True,
    )
    assert report["status"] == "complete"
    assert report["generation_budget_per_workload"] == 1
    assert len(report["cells"][0]["generations"]) == 1


def test_m23_prime_run_trial_registry_gate_rejects_before_run_root(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    reached = []
    original_load = A.trial_registry.load_launch_binding

    def observed_load(**kwargs):
        reached.append("registry-gate")
        return original_load(**kwargs)

    def artifact_creation(*args, **kwargs):
        pytest.fail("registry rejection reached artifact creation")

    monkeypatch.setattr(A.trial_registry, "load_launch_binding", observed_load)
    monkeypatch.setattr(A, "ensure_exploration_namespace", artifact_creation)
    run_root = tmp_path / "rejected-run"
    with pytest.raises(A.trial_registry.TrialRegistryError, match="workload-binding"):
        _t325_run(
            t325_registered_trial,
            run_root,
            workloads=["rr20"],
        )
    assert reached == ["registry-gate"]
    assert not run_root.exists()


@pytest.mark.parametrize("no_build", [True, False], ids=["no-build", "build"])
def test_m24_cli_registry_gate_rejects_before_build_preparation(
    tmp_path, monkeypatch, t325_registered_trial, no_build,
) -> None:
    reached = []
    original_load = A.trial_registry.load_launch_binding

    def observed_load(**kwargs):
        reached.append("registry-gate")
        return original_load(**kwargs)

    def build_preparation(*args, **kwargs):
        pytest.fail("registry rejection reached build preparation")

    monkeypatch.setattr(A.trial_registry, "load_launch_binding", observed_load)
    monkeypatch.setattr(A, "assert_pinned_clean", build_preparation)
    monkeypatch.setattr(A, "checkout", build_preparation)
    monkeypatch.setattr(calibrator_runner, "competing_bench_pids", build_preparation)
    monkeypatch.setattr(
        A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER,
    )
    run_root = tmp_path / "cli-rejected-run"
    arguments = [
        "--trial-id", t325_registered_trial.trial_id,
        "--trial-manifest", str(t325_registered_trial.manifest_path),
        "--provider", "fixture" if no_build else "claude-headless",
        "--workloads", "rr20",
        "--ccbench-dir", str(tmp_path / "ccbench"),
        "--run-root", str(run_root),
    ]
    if no_build:
        arguments.append("--no-build")
    else:
        arguments.append("--allow-coder-derived-build")
    with pytest.raises(A.trial_registry.TrialRegistryError, match="workload-binding"):
        A.main(arguments)
    assert reached == ["registry-gate"]
    assert not run_root.exists()


def test_m26_manifest_binding_survives_provider_init_and_supervisor_failures(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    expected = _t325_binding_fields(t325_registered_trial.binding)

    with monkeypatch.context() as scoped:
        def fail_provider_init(**kwargs):
            raise RuntimeError("provider init failed")

        scoped.setattr(A, "_provider_set", fail_provider_init)
        provider_root = tmp_path / "provider-init-failure"
        provider_report = _t325_run(t325_registered_trial, provider_root)
    assert provider_report["status"] == "partial"
    assert provider_report["cells"] == []
    assert {field: provider_report[field] for field in expected} == expected
    assert provider_report["lifecycle_terminal_status"] == "indeterminate"
    assert {
        field: _t325_run_start(provider_root)[field] for field in expected
    } == expected

    def broken_preview(coder, *, sub):
        raise RuntimeError("supervisor failed")

    second_trial_id = "t325-h1-off"
    second_binding = A.trial_registry.load_launch_binding(
        manifest_path=t325_registered_trial.manifest_path,
        trial_id=second_trial_id,
        workloads=["rr80"],
        repository_root=t325_registered_trial.repo,
        registry_path=t325_registered_trial.registry_path,
    )
    second_expected = _t325_binding_fields(second_binding)
    supervisor_root = tmp_path / "supervisor-failure"
    supervisor_report = _t325_run(
        t325_registered_trial,
        supervisor_root,
        trial_id=second_trial_id,
        providers={
            role: A.FixtureRoleProvider(role)
            for role in ("planner", "coder", "auditor", "critic")
        },
        preview=broken_preview,
    )
    assert supervisor_report["status"] == "partial"
    assert supervisor_report["cells"][0]["stop_reason"] == "supervisor-error"
    assert {
        field: supervisor_report[field] for field in second_expected
    } == second_expected
    assert {
        field: _t325_run_start(supervisor_root)[field] for field in second_expected
    } == second_expected
    assert supervisor_report["lifecycle_terminal_status"] == "indeterminate"

    attempt_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_ATTEMPT_REGISTRY_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    provider_slot_id = _t325_run_start(provider_root)["slot_id"]
    provider_attempt_terminal = next(
        row
        for row in attempt_rows
        if row.get("event") == "terminal"
        and row.get("slot_id") == provider_slot_id
    )
    assert provider_attempt_terminal["terminal_status"] == "not-consumed"
    assert provider_attempt_terminal["report_sha256"] is None
    assert provider_attempt_terminal["observation_sha256"] is None
    assert provider_attempt_terminal["primary_value"] is None
    supervisor_slot_id = _t325_run_start(supervisor_root)["slot_id"]
    attempt_terminal = next(
        row
        for row in attempt_rows
        if row.get("event") == "terminal"
        and row.get("slot_id") == supervisor_slot_id
    )
    assert attempt_terminal["terminal_status"] == "not-consumed"
    assert attempt_terminal["report_sha256"] is None
    assert attempt_terminal["observation_sha256"] is None
    assert attempt_terminal["primary_value"] is None

    lifecycle = (
        t325_registered_trial.repo
        / A.trial_registry.DEFAULT_LIFECYCLE_PATH
    )
    lifecycle_rows = [
        json.loads(line)
        for line in lifecycle.read_text(encoding="utf-8").splitlines()
    ]
    supervisor_lifecycle_rows = [
        row for row in lifecycle_rows
        if row.get("trial_id") == second_trial_id
    ]
    assert [row["event"] for row in supervisor_lifecycle_rows] == [
        "start", "terminal",
    ]
    assert supervisor_lifecycle_rows[-1]["terminal_status"] == "indeterminate"
    provider_lifecycle_rows = [
        row for row in lifecycle_rows
        if row.get("trial_id") == t325_registered_trial.trial_id
    ]
    assert [row["event"] for row in provider_lifecycle_rows] == [
        "start", "terminal",
    ]
    assert provider_lifecycle_rows[-1]["terminal_status"] == "indeterminate"


def test_registered_transport_admission_failure_is_indeterminate(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    class FixtureTransportAdmissionError(RuntimeError):
        pass

    admission_calls = []

    def reject_transport_admission(**kwargs):
        admission_calls.append(kwargs)
        raise FixtureTransportAdmissionError("fixture transport admission failed")

    monkeypatch.setattr(A, "admit_claude_transport", reject_transport_admission)
    run_root = tmp_path / "registered-transport-admission-failure"
    report = A.run_trial(
        trial_id=t325_registered_trial.trial_id,
        workloads=["rr80"],
        generations=2,
        provider_kind="claude-headless",
        run_root=run_root,
        sub="/unused",
        do_build=False,
        allow_pegasus_compute_transport=True,
        trial_manifest=t325_registered_trial.manifest_path,
        effective_preregistration=t325_registered_trial.capability,
    )

    assert len(admission_calls) == 1
    assert report["launch_admission"]["mode"] == "registered-effective"
    assert report["status"] == "partial"
    assert report["cells"] == []
    assert report["lifecycle_terminal_status"] == "indeterminate"
    attempt_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_ATTEMPT_REGISTRY_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    slot_id = _t325_run_start(run_root)["slot_id"]
    attempt_terminal = next(
        row
        for row in attempt_rows
        if row.get("event") == "terminal"
        and row.get("slot_id") == slot_id
    )
    assert attempt_terminal["terminal_status"] == "not-consumed"
    assert attempt_terminal["report_sha256"] is None
    assert attempt_terminal["observation_sha256"] is None
    assert attempt_terminal["primary_value"] is None
    lifecycle_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_LIFECYCLE_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    trial_lifecycle_rows = [
        row
        for row in lifecycle_rows
        if row.get("trial_id") == t325_registered_trial.trial_id
    ]
    assert [row["event"] for row in trial_lifecycle_rows] == [
        "start", "terminal",
    ]
    assert trial_lifecycle_rows[-1]["terminal_status"] == "indeterminate"


def test_registered_budget_provider_init_failure_raises_indeterminate_terminal(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    ledger = SimpleNamespace(
        manifest_sha256="a" * 64,
        freeze_sha256="b" * 64,
        schedule_sha256="c" * 64,
        ratified_generation_sha256="d" * 64,
        reservation=SimpleNamespace(state="held"),
    )
    budget_inputs = SimpleNamespace(
        ledger_path=tmp_path / "budget-ledger.json",
        manifest_sha256=ledger.manifest_sha256,
        freeze_sha256=ledger.freeze_sha256,
        schedule_sha256=ledger.schedule_sha256,
        ratified_generation_sha256=ledger.ratified_generation_sha256,
        cells=(),
        limits=object(),
    )
    monkeypatch.setattr(A, "load_ratified_freeze", lambda _root: object())
    monkeypatch.setattr(
        A,
        "_prepare_s8c_budget_inputs",
        lambda **_kwargs: budget_inputs,
    )
    monkeypatch.setattr(A, "reserve_all_cells", lambda *_args, **_kwargs: ledger)
    provider_calls = []

    def fail_provider_init(**kwargs):
        provider_calls.append(kwargs)
        raise RuntimeError("provider init failed")

    monkeypatch.setattr(A, "_provider_set", fail_provider_init)
    run_root = tmp_path / "registered-budget-provider-init-failure"
    with pytest.raises(A.AutonomousTrialError) as excinfo:
        _t325_run(
            t325_registered_trial,
            run_root,
            do_build=True,
            drive=A.trigger.drive_iteration,
            coder_authority=_coder_authority(),
        )
    assert str(excinfo.value) == (
        "budget cell terminal is indeterminate after provider "
        "initialization or transport admission error"
    )
    assert len(provider_calls) == 1
    attempt_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_ATTEMPT_REGISTRY_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    slot_id = _t325_run_start(run_root)["slot_id"]
    attempt_terminal = next(
        row
        for row in attempt_rows
        if row.get("event") == "terminal"
        and row.get("slot_id") == slot_id
    )
    assert attempt_terminal["terminal_status"] == "not-consumed"
    assert attempt_terminal["report_sha256"] is None
    assert attempt_terminal["observation_sha256"] is None
    assert attempt_terminal["primary_value"] is None
    lifecycle_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_LIFECYCLE_PATH
        ).read_text(encoding="utf-8").splitlines()
    ]
    trial_lifecycle_rows = [
        row
        for row in lifecycle_rows
        if row.get("trial_id") == t325_registered_trial.trial_id
    ]
    assert [row["event"] for row in trial_lifecycle_rows] == [
        "start", "terminal",
    ]
    assert trial_lifecycle_rows[-1]["terminal_status"] == "indeterminate"


def test_exploratory_provider_init_failure_stays_without_lifecycle_status(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    def fail_provider_init(**kwargs):
        raise RuntimeError("provider init failed")

    monkeypatch.setattr(A, "_provider_set", fail_provider_init)
    report = A.run_trial(
        trial_id="exploratory-provider-init-failure",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=tmp_path / "exploratory-provider-init-failure",
        sub="/unused",
        do_build=False,
        drive=_fake_drive,
        preview=_fake_preview,
        trial_manifest=None,
        effective_preregistration=None,
        allow_unregistered_exploratory=True,
    )

    assert report["launch_admission"]["mode"] == (
        "explicit-unregistered-exploratory"
    )
    assert report["status"] == "partial"
    assert "lifecycle_terminal_status" not in report


def test_m30_registered_trial_id_without_manifest_is_rejected(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    def artifact_creation(*args, **kwargs):
        pytest.fail("registered exploratory rejection reached artifact creation")

    monkeypatch.setattr(A, "ensure_exploration_namespace", artifact_creation)
    run_root = tmp_path / "registered-without-manifest"
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match="registered trial_id cannot run without its manifest",
    ):
        A.run_trial(
            trial_id=t325_registered_trial.trial_id,
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="fixture",
            run_root=run_root,
            sub="/unused",
            do_build=False,
            drive=_fake_drive,
            preview=_fake_preview,
            allow_unregistered_exploratory=True,
        )
    assert not run_root.exists()


def test_registered_trial_id_direct_run_workload_requires_run_scope(
    tmp_path, t325_registered_trial,
) -> None:
    run_root = tmp_path / "direct-workload-rejected"
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=r"\[run-scope\] workload requires a sealed launch admission",
    ):
        A._run_workload(
            workload="rr80",
            generations=1,
            providers={},
            journal=SimpleNamespace(),
            run_root=run_root,
            sub="/unused",
            do_build=False,
            cache_root="",
            trial_id=t325_registered_trial.trial_id,
            started_monotonic=time.monotonic(),
            max_wall_s=60,
            build_context=_no_build_context(),
            gating_spec_snapshot=A.snapshot_gating_spec(A.GATING_SPEC),
        )
    assert not run_root.exists()


def test_direct_workload_rejects_registry_binding_without_run_scope(
    tmp_path, t325_registered_trial,
) -> None:
    token = A._ACTIVE_TRIAL_BINDING.set(t325_registered_trial.binding)
    try:
        with pytest.raises(
            A.trial_registry.TrialRegistryError,
            match=r"\[run-scope\] active workload scope was not issued by run_trial",
        ):
            A._run_workload(
                workload="rr80",
                generations=1,
                providers={},
                journal=SimpleNamespace(),
                run_root=tmp_path / "forged-direct-workload",
                sub="/unused",
                do_build=False,
                cache_root="",
                trial_id=t325_registered_trial.trial_id,
                started_monotonic=time.monotonic(),
                max_wall_s=60,
                build_context=_no_build_context(),
                gating_spec_snapshot=A.snapshot_gating_spec(A.GATING_SPEC),
            )
    finally:
        A._ACTIVE_TRIAL_BINDING.reset(token)


@pytest.mark.parametrize(
    ("field", "forged_value", "error"),
    [
        ("manifest_sha256", "0" * 64, "manifest_sha256"),
        ("prereg_commit", "0" * 40, "prereg_commit"),
        ("measurement_head", "0" * 40, "measurement-head-moved"),
        ("trial_id", "forged-trial-id", "trial_id"),
        ("arm", "forged-arm", "arm"),
        ("holdout", "H2", "holdout"),
        ("campaign_id", "forged-campaign-id", "campaign_id"),
        ("workload", "rr20", "workload"),
        ("ycsb_rratio", "20", "ycsb_rratio"),
        ("_seal", object(), "binding was not issued"),
    ],
)
def test_run_trial_rejects_every_dataclass_replace_binding_field(
    tmp_path, t325_registered_trial, field, forged_value, error,
) -> None:
    forged = dataclasses.replace(
        t325_registered_trial.binding,
        **{field: forged_value},
    )
    forged_admission = dataclasses.replace(
        t325_registered_trial.admission,
        binding=forged,
    )
    run_root = tmp_path / f"forged-binding-{field}"
    with pytest.raises(A.trial_registry.TrialRegistryError, match=error):
        A.run_trial(
            trial_id=t325_registered_trial.trial_id,
            workloads=["rr80"],
            generations=2,
            provider_kind="fixture",
            run_root=run_root,
            sub="/unused",
            do_build=False,
            trial_manifest=t325_registered_trial.manifest_path,
            effective_preregistration=t325_registered_trial.capability,
            trial_admission=forged_admission,
        )
    assert not run_root.exists()


def test_run_trial_rejects_head_move_after_cli_binding(
    tmp_path, t325_registered_trial,
) -> None:
    marker = t325_registered_trial.repo / "head-moved.txt"
    marker.write_text("moved\n", encoding="utf-8")
    _t325_git(t325_registered_trial.repo, "add", "--", marker.name)
    _t325_git(t325_registered_trial.repo, "commit", "-m", "move head")
    run_root = tmp_path / "head-moved-run"
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match=r"\[measurement-head-moved\] ",
    ):
        A.run_trial(
            trial_id=t325_registered_trial.trial_id,
            workloads=["rr80"],
            generations=2,
            provider_kind="fixture",
            run_root=run_root,
            sub="/unused",
            do_build=False,
            trial_manifest=t325_registered_trial.manifest_path,
            effective_preregistration=t325_registered_trial.capability,
            trial_admission=t325_registered_trial.admission,
        )
    assert not run_root.exists()


def test_m32_cli_manifestless_gate_is_not_masked_by_run_trial(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    monkeypatch.setattr(A, "assert_pinned_clean", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        A,
        "run_trial",
        lambda **kwargs: {"status": "complete", "cells": []},
    )
    with pytest.raises(
        A.trial_registry.TrialRegistryError,
        match="registered trial_id cannot run without its manifest",
    ):
        A.main([
            "--trial-id", t325_registered_trial.trial_id,
            "--provider", "fixture",
            "--workloads", "ycsb-a",
            "--no-build",
            "--allow-unregistered-exploratory",
            "--ccbench-dir", str(tmp_path / "ccbench"),
            "--run-root", str(tmp_path / "m32-run"),
        ])


def test_m13_prime_public_launcher_rejects_producer_campaign_derivation_bypass(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    original_branch = _t325_git(
        t325_registered_trial.repo, "branch", "--show-current",
    )
    prereg_commit = t325_registered_trial.binding.prereg_commit
    _t325_git(
        t325_registered_trial.repo, "checkout", "-q", "-b", "m13-prime",
        prereg_commit,
    )
    _t325_git(t325_registered_trial.repo, "branch", "-D", original_branch)
    A.s8c_arm_inputs.generate_off_neutral_artifacts(
        repository_root=t325_registered_trial.repo,
    )
    _t325_git(
        t325_registered_trial.repo,
        "add",
        "--",
        A.s8c_arm_inputs.OFF_DESCRIPTOR_RELATIVE_PATH.as_posix(),
        A.s8c_arm_inputs.OFF_FREEZE_RELATIVE_PATH.as_posix(),
    )
    _t325_git(t325_registered_trial.repo, "commit", "-m", "m13 arm input authority")
    trials = []
    target_trial_id = "m13-prime-h1-on"
    measurement_head = _t325_git(
        t325_registered_trial.repo, "rev-parse", "HEAD"
    )
    for holdout, workload in (("H1", "rr80"), ("H2", "rr20")):
        for arm in ("on", "off", "swapped"):
            trial_id = f"m13-prime-{holdout.lower()}-{arm}"
            resolved = A.s8c_arm_inputs.resolve_arm_input(
                arm=arm,
                holdout=holdout,
                repository_root=t325_registered_trial.repo,
                commit=measurement_head,
            )
            prepared = A._prepare_manifest_campaign_identity(
                workload=workload,
                trial_id=trial_id,
                generations=2,
                site=A.trigger.site_policy.OTHER,
                contract=_T530_CONTRACT,
                build_context=_no_build_context(),
                resolved_arm_input=resolved,
            )
            campaign_id = prepared.campaign_id
            if trial_id == target_trial_id:
                campaign_id += "-declared"
            trials.append({
                "trial_id": trial_id,
                "arm": arm,
                "holdout": holdout,
                "campaign_id": campaign_id,
                "generations": 2,
                "n": 2,
            })
    manifest_path = t325_registered_trial.repo / "manifests" / "m13-prime.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps({
            "schema_version": A.trial_registry.MANIFEST_SCHEMA_VERSION,
            "prereg_commit": prereg_commit,
            "trials": trials,
        }, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    _t325_git(
        t325_registered_trial.repo,
        "add",
        "--",
        str(manifest_path.relative_to(t325_registered_trial.repo)),
    )
    _t325_git(t325_registered_trial.repo, "commit", "-m", "m13 prime manifest")
    effective_commit = _t325_prepare_effective_binding(
        t325_registered_trial.repo, manifest_path,
    )
    A.trial_registry.append_trial_registration(
        manifest_path=manifest_path,
        repository_root=t325_registered_trial.repo,
        registry_path=t325_registered_trial.registry_path,
        prereg_effective_commit=effective_commit,
    )
    _t325_git(
        t325_registered_trial.repo,
        "add",
        "--",
        str(t325_registered_trial.registry_path.relative_to(t325_registered_trial.repo)),
    )
    _t325_git(t325_registered_trial.repo, "commit", "-m", "m13 prime registry")

    def artifact_creation(*args, **kwargs):
        pytest.fail("campaign binding bypass reached artifact creation")

    monkeypatch.setattr(A, "ensure_exploration_namespace", artifact_creation)
    run_root = tmp_path / "m13-prime-run"
    with pytest.raises(A.trial_registry.TrialRegistryError, match="campaign-binding"):
        A.run_trial(
            trial_id=target_trial_id,
            workloads=["rr80"],
            generations=2,
            provider_kind="fixture",
            run_root=run_root,
            sub="/unused",
            do_build=False,
            trial_manifest=manifest_path,
            effective_preregistration=t325_registered_trial.capability,
        )
    assert not run_root.exists()


def _canonical_origin_test_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _origin_run_plan_input():
    raw = origin_fixtures.build_recovery_envelope_inputs()
    materials = tuple(
        A.OriginMemberPlanInput(
            candidate_salt=item["candidate_salt"],
            result_evidence_salt=item["result_evidence_salt"],
            constraint_salt=item["constraint_salt"],
        )
        for item in raw["members"]
    )
    return A.OriginRunPlanInput(
        hypothesis_sha256=raw["hypothesis_sha256"],
        validation_plan_sha256=raw["validation_plan_sha256"],
        attempt_0_batch_id=raw["reserve_attempts"][0]["batch_id"],
        retry_1_batch_id=raw["reserve_attempts"][1]["batch_id"],
        event_operation_ids=reflux_origin_topology.EventOperationIds(
            **raw["event_operation_ids"]
        ),
        source_mask=7,
        member_materials=materials,
    )


def _origin_logical_campaign() -> A.CampaignConfig:
    context = _no_build_context()
    return A.ident.bind_admission_policy(
        A.CampaignConfig(
            spec_slug="origin-identity-test",
            search_tag="logical",
            spec_content="origin physical identity test",
            ccbench_commit="1" * 40,
            search_config={"logical": True},
            trial="origin-logical-trial",
        ),
        context.policy,
    )


def test_origin_campaign_runs_are_deterministic_distinct_and_structured() -> None:
    logical = _origin_logical_campaign()
    digest = "a" * 64
    first = A._derive_origin_campaign_runs(
        logical, attempt_capability_sha256=digest,
    )
    second = A._derive_origin_campaign_runs(
        logical, attempt_capability_sha256=digest,
    )
    assert first == second
    assert tuple(run.query_ordinal for run in first) == tuple(range(33))
    assert len({run.identity_preimage for run in first}) == 33
    assert len({run.campaign_run_identity for run in first}) == 33
    assert logical.trial == first[0].campaign.trial
    assert "origin_campaign_run" not in logical.search_config
    for query_ordinal, run in enumerate(first):
        assert run.campaign.search_config["origin_campaign_run"] == {
            "attempt_capability_sha256": digest,
            "query_ordinal": query_ordinal,
        }
        assert run.identity_preimage == A.ident.canonical_preimage(run.campaign)
        assert run.campaign_run_identity == str(A.ident.campaign_id(run.campaign))


def test_origin_campaign_runs_change_with_attempt_slot_digest() -> None:
    logical = _origin_logical_campaign()
    first = A._derive_origin_campaign_runs(
        logical, attempt_capability_sha256="a" * 64,
    )
    second = A._derive_origin_campaign_runs(
        logical, attempt_capability_sha256="b" * 64,
    )
    assert all(
        left.campaign_run_identity != right.campaign_run_identity
        for left, right in zip(first, second, strict=True)
    )


@pytest.mark.parametrize("query_ordinal", [-1, 33, True, 1.0])
def test_origin_campaign_run_rejects_non_exact_query_ordinal(
    query_ordinal,
) -> None:
    with pytest.raises(
        A.AutonomousTrialError, match="exact int in 0..32",
    ):
        A._derive_origin_campaign_run(
            _origin_logical_campaign(),
            attempt_capability_sha256="a" * 64,
            query_ordinal=query_ordinal,
        )


def test_origin_campaign_run_does_not_overwrite_existing_physical_component() -> None:
    logical = _origin_logical_campaign()
    already_physical = dataclasses.replace(
        logical,
        search_config={
            **logical.search_config,
            "origin_campaign_run": {
                "attempt_capability_sha256": "a" * 64,
                "query_ordinal": 0,
            },
        },
    )
    with pytest.raises(
        A.AutonomousTrialError, match="already contains origin_campaign_run",
    ):
        A._derive_origin_campaign_run(
            already_physical,
            attempt_capability_sha256="a" * 64,
            query_ordinal=0,
        )


def test_origin_campaign_run_preimage_duplicates_fail_closed(monkeypatch) -> None:
    monkeypatch.setattr(A.ident, "canonical_preimage", lambda _cfg: "same")
    with pytest.raises(
        A.AutonomousTrialError, match="preimages must be pairwise distinct",
    ):
        A._derive_origin_campaign_runs(
            _origin_logical_campaign(),
            attempt_capability_sha256="a" * 64,
        )


def test_origin_campaign_run_identity_duplicates_fail_closed(monkeypatch) -> None:
    monkeypatch.setattr(A.ident, "campaign_id", lambda _cfg: "same")
    with pytest.raises(
        A.AutonomousTrialError, match="identities must be pairwise distinct",
    ):
        A._derive_origin_campaign_runs(
            _origin_logical_campaign(),
            attempt_capability_sha256="a" * 64,
        )


def test_origin_campaign_run_identity_mismatch_fails_closed(monkeypatch) -> None:
    original = A.ident.campaign_id
    calls = 0

    def change_after_derivation(cfg):
        nonlocal calls
        calls += 1
        value = str(original(cfg))
        return value if calls <= 33 else value + "-changed"

    monkeypatch.setattr(A.ident, "campaign_id", change_after_derivation)
    with pytest.raises(
        A.AutonomousTrialError,
        match="identity differs from its physical config",
    ):
        A._derive_origin_campaign_runs(
            _origin_logical_campaign(),
            attempt_capability_sha256="a" * 64,
        )


def test_origin_run_plan_inputs_have_no_caller_supplied_physical_identity() -> None:
    assert "planned_campaign_run_identity" not in inspect.signature(
        A.OriginMemberPlanInput
    ).parameters
    assert "run_plan" not in inspect.signature(A.OriginProducerInputs).parameters
    assert "run_plan_input" in inspect.signature(
        A.OriginProducerInputs
    ).parameters


def test_registry_campaign_binding_rejects_physical_origin_identity(
    t325_registered_trial,
) -> None:
    admission = A._trial_launch_admission(
        trial_manifest=t325_registered_trial.manifest_path,
        trial_id=t325_registered_trial.trial_id,
        workloads=["rr80"],
        generations=2,
        allow_unregistered_exploratory=False,
        effective_preregistration=t325_registered_trial.capability,
    )
    arm_execution = A.trial_registry.bind_trial_arm(
        admission.binding,
        repository_root=t325_registered_trial.repo,
    )
    prepared = A._prepare_campaign_identity(
        workload="rr80",
        trial_id=t325_registered_trial.trial_id,
        generations=2,
        site=A.trigger.site_policy.OTHER,
        contract=_T530_CONTRACT,
        build_context=_no_build_context(),
        arm_execution=arm_execution,
    )
    physical = A._derive_origin_campaign_run(
        prepared.campaign,
        attempt_capability_sha256="a" * 64,
        query_ordinal=0,
    )
    assert physical.campaign_run_identity != prepared.campaign_id
    with pytest.raises(
        A.trial_registry.TrialRegistryError, match=r"\[campaign-binding\]",
    ):
        A.trial_registry.assert_campaign_binding(
            admission.binding,
            arm_execution=arm_execution,
            actual_campaign_id=physical.campaign_run_identity,
        )


def _origin_salted_commitment(salt: str, value: bytes) -> str:
    return hashlib.sha256(bytes.fromhex(salt) + value).hexdigest()


def _origin_candidate_commitment_bytes(
    candidate: bytes, query_ordinal: int, replicate_ordinal: int,
) -> bytes:
    return b"izanagi-reflux-origin-batch-member/v1\0" + _canonical_origin_test_bytes({
        "candidate_wire_b64": base64.b64encode(candidate).decode("ascii"),
        "query_ordinal": query_ordinal,
        "replicate_ordinal": replicate_ordinal,
    })


def _origin_result_commitment_bytes(outcome: str, evidence_sha256: str) -> bytes:
    return b"izanagi-reflux-origin-result-evidence/v1\0" + (
        _canonical_origin_test_bytes({
            "evidence_sha256": evidence_sha256,
            "outcome": outcome,
        })
    )


def _align_origin_result_records(
    frozen,
    capability,
    *,
    launch_admission_record_sha256: str,
) -> tuple[bytes, ...]:
    aligned = []
    for path in frozen.result_evidence_paths:
        record = json.loads(path.read_bytes())
        record["origin_binding"] = {
            "authority_blob_sha256": capability.authority_blob_sha256,
            "source_closure_sha256": capability.source_closure_sha256,
            "origin_id": capability.origin_id,
            "cell_key": capability.cell_key,
            "workload": capability.trial_workload,
            "axis_semantics_sha256": capability.axis_semantics_sha256,
            "verifier_policy_sha256": capability.verifier_policy_sha256,
            "environment_contract_sha256": capability.environment_contract_sha256,
        }
        record["trial_binding"] = {
            "launch_admission_record_sha256": launch_admission_record_sha256,
            "campaign_id": capability.campaign_id,
            "workload": capability.trial_workload,
        }
        provenance_ref = record["evidence"]["execution_provenance_ref"]
        provenance_path = frozen.evidence_root / provenance_ref["path"]
        provenance = json.loads(provenance_path.read_bytes())
        provenance.update({
            "campaign_id": capability.campaign_id,
            "workload": capability.trial_workload,
            "contract_sha256": capability.environment_contract_sha256,
        })
        provenance_bytes = _canonical_origin_test_bytes(provenance)
        provenance_path.write_bytes(provenance_bytes)
        provenance_ref["sha256"] = hashlib.sha256(provenance_bytes).hexdigest()
        raw = _canonical_origin_test_bytes(record)
        path.write_bytes(raw)
        aligned.append(raw)
    return tuple(aligned)


def _materialize_origin_physical_evidence(
    frozen,
    runtime: A.OriginTrialRuntime,
) -> tuple[bytes, ...]:
    evidence_root = runtime.campaign_output_root
    aligned: list[bytes] = []
    for run, record_path in zip(
        runtime.campaign_runs, frozen.result_evidence_paths, strict=True
    ):
        record = json.loads(record_path.read_bytes())
        assert record["ledger_member"]["query_ordinal"] == run.query_ordinal
        root = Path(A.exploration_campaign_layout(
            run.campaign_run_identity, str(evidence_root)
        ).root)
        (root / "runs").mkdir(parents=True, exist_ok=True)
        (root / "reports").mkdir(exist_ok=True)
        (root / "campaign.lock").write_bytes(
            run.identity_preimage.encode("utf-8")
        )

        old_projection_path = (
            frozen.evidence_root
            / record["evidence"]["ordered_wal_ref"]["path"]
        )
        projection = json.loads(old_projection_path.read_bytes())
        old_source_path = (
            frozen.evidence_root / projection["source_wal_ref"]["path"]
        )
        source_raw = old_source_path.read_bytes()
        source_path = root / "runs" / "wal.jsonl"
        source_path.write_bytes(source_raw)
        projection["source_wal_ref"] = {
            "path": source_path.relative_to(evidence_root).as_posix(),
            "sha256": hashlib.sha256(source_raw).hexdigest(),
        }
        projection_path = root / "reports" / "ordered-wal-projection.json"
        projection_raw = _canonical_origin_test_bytes(projection)
        projection_path.write_bytes(projection_raw)

        old_provenance_path = (
            frozen.evidence_root
            / record["evidence"]["execution_provenance_ref"]["path"]
        )
        provenance = json.loads(old_provenance_path.read_bytes())
        provenance["schema_version"] = "execution-provenance/v2"
        provenance["campaign_id"] = runtime.capability.campaign_id
        provenance["campaign_run_identity"] = run.campaign_run_identity
        provenance_path = root / "reports" / "execution-provenance.json"
        provenance_raw = _canonical_origin_test_bytes(provenance)
        provenance_path.write_bytes(provenance_raw)

        record["evidence"]["ordered_wal_ref"] = {
            "path": projection_path.relative_to(evidence_root).as_posix(),
            "sha256": hashlib.sha256(projection_raw).hexdigest(),
        }
        record["evidence"]["execution_provenance_ref"] = {
            "path": provenance_path.relative_to(evidence_root).as_posix(),
            "sha256": hashlib.sha256(provenance_raw).hexdigest(),
        }
        raw = _canonical_origin_test_bytes(record)
        target = evidence_root / A.reflux_result_evidence.result_evidence_relative_path(record)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        aligned.append(raw)
    return tuple(aligned)


def _seal_origin_fixture_ledger(
    client,
    capability,
    run_plan,
    result_record_bytes: tuple[bytes, ...],
) -> None:
    records = {
        record["ledger_member"]["query_ordinal"]: (record, raw)
        for raw in result_record_bytes
        for record in (json.loads(raw),)
    }
    assert tuple(sorted(records)) == tuple(range(33))
    candidate_commitments = []
    result_commitments = []
    constraint_commitments = []
    opened = []
    for member in run_plan.members:
        record, raw = records[member.query_ordinal]
        candidate_bytes = member.candidate_wire.encode("ascii")
        evidence_sha256 = hashlib.sha256(raw).hexdigest()
        physical = record["physical_result"]
        candidate_commitment = _origin_salted_commitment(
            member.candidate_salt,
            _origin_candidate_commitment_bytes(
                candidate_bytes,
                member.query_ordinal,
                member.replicate_ordinal,
            ),
        )
        result_commitment = _origin_salted_commitment(
            member.result_evidence_salt,
            _origin_result_commitment_bytes(
                physical["outcome"], evidence_sha256
            ),
        )
        constraint_sha256 = physical["constraint_sha256"]
        constraint_commitment = _origin_salted_commitment(
            member.constraint_salt,
            constraint_sha256.encode("ascii"),
        )
        candidate_commitments.append(candidate_commitment)
        result_commitments.append(result_commitment)
        constraint_commitments.append(constraint_commitment)
        opened.append(reflux_origin_ledger.OpenedBatchMember(
            query_ordinal=member.query_ordinal,
            replicate_ordinal=member.replicate_ordinal,
            candidate_salt=member.candidate_salt,
            candidate_bytes=candidate_bytes,
            result_evidence_salt=member.result_evidence_salt,
            outcome=physical["outcome"],
            evidence_digest=reflux_origin_ledger.EvidenceDigest(evidence_sha256),
            constraint_salt=member.constraint_salt,
            constraint_sha256=constraint_sha256,
        ))

    attempt = run_plan.reserve_attempts[0]
    snapshot = client.read_origin(capability)
    receipt = client.reserve_batch(
        capability,
        operation_id=run_plan.event_operation_ids.reserve_attempt_0,
        expected_state_commitment=snapshot.state_commitment,
        reservation=reflux_origin_ledger.BatchReserved(
            batch_id=attempt.batch_id,
            iteration_index=attempt.iteration_index,
            member_row_count=33,
            query_ordinal_start=attempt.query_ordinal_start,
        ),
    )
    receipt = client.commit_event(
        capability,
        operation_id=run_plan.event_operation_ids.batch_commit,
        expected_state_commitment=receipt.current_state_commitment,
        event=reflux_origin_ledger.BatchCommitted(
            batch_id=attempt.batch_id,
            iteration_index=attempt.iteration_index,
            members=tuple(
                reflux_origin_ledger.CommittedBatchMember(index, commitment)
                for index, commitment in enumerate(candidate_commitments)
            ),
        ),
    )
    receipt = client.commit_event(
        capability,
        operation_id=run_plan.event_operation_ids.results_prepare,
        expected_state_commitment=receipt.current_state_commitment,
        event=reflux_origin_ledger.BatchResultsPrepared(
            batch_id=attempt.batch_id,
            members=tuple(
                reflux_origin_ledger.PreparedBatchMember(
                    index,
                    candidate_commitments[index],
                    result_commitments[index],
                    constraint_commitments[index],
                )
                for index in range(33)
            ),
        ),
    )
    client.commit_event(
        capability,
        operation_id=run_plan.event_operation_ids.results_open,
        expected_state_commitment=receipt.current_state_commitment,
        event=reflux_origin_ledger.BatchSealed(
            batch_id=attempt.batch_id,
            members=tuple(opened),
        ),
    )
    sealed = client.read_origin(capability)
    assert sealed.phase == "IDLE"
    assert sealed.sealed_queries == 33
    assert len(client.read_sealed_batches(capability)) == 1


def _origin_public_inputs(tmp_path, monkeypatch, registered):
    frozen = origin_fixtures.build_fixture_repository(tmp_path / "origin-frozen")
    registered_arm_execution = A.trial_registry.bind_trial_arm(
        registered.binding,
        repository_root=registered.repo,
    )
    descriptor, descriptor_binding = A._descriptor_from_arm_execution(
        registered_arm_execution
    )
    descriptor_bytes = _canonical_origin_test_bytes(descriptor)
    descriptor_sha256 = hashlib.sha256(descriptor_bytes).hexdigest()
    authority_manifest = origin_fixtures.build_authority_manifest(
        workload={
            "descriptor_sha256": descriptor_sha256,
            "records": descriptor["scale"]["records"],
            "threads": descriptor["scale"]["threads"],
        }
    )
    manifest_bytes = _canonical_origin_test_bytes(authority_manifest)
    origin_id = hashlib.sha256(
        b"izanagi-reflux-origin-manifest/v2\0" + manifest_bytes
    ).hexdigest()
    cell_key = hashlib.sha256(
        b"izanagi-reflux-origin-cell/v1\0"
        + _canonical_origin_test_bytes([
            authority_manifest["workload"]["descriptor_sha256"],
            authority_manifest["axis_semantics_sha256"],
            authority_manifest["verifier_policy_sha256"],
            authority_manifest["environment_contract_sha256"],
        ])
    ).hexdigest()
    authority_bytes = _canonical_origin_test_bytes({
        "authority_schema": "izanagi-reflux-origin-authority/v2",
        "origins": [{
            "cell_key": cell_key,
            "manifest": authority_manifest,
            "origin_id": origin_id,
        }],
    }) + b"\n"

    authority_path = registered.repo / reflux_origin_ledger.AUTHORITY_RELATIVE_PATH
    authority_path.parent.mkdir(parents=True, exist_ok=True)
    authority_path.write_bytes(_canonical_origin_test_bytes({
        "authority_schema": "izanagi-reflux-origin-authority/v2",
        "origins": [],
    }) + b"\n")
    artifacts = registered.repo / "artifacts"
    artifacts.mkdir(exist_ok=True)
    descriptor_path = artifacts / "workload-descriptor.json"
    descriptor_path.write_bytes(descriptor_bytes)
    artifact_paths = [descriptor_path]
    for name in (
        "axis-semantics.json",
        "verifier-policy.json",
        "environment-contract.json",
    ):
        destination = artifacts / name
        destination.write_bytes((frozen.root / "artifacts" / name).read_bytes())
        artifact_paths.append(destination)
    _t325_git(
        registered.repo,
        "add",
        "--",
        *[str(path.relative_to(registered.repo)) for path in [authority_path, *artifact_paths]],
    )
    _t325_git(registered.repo, "commit", "-m", "origin source referents")
    captured_commit = _t325_git(registered.repo, "rev-parse", "HEAD")

    source_record = origin_fixtures.build_source_closure_record(**{
        "captured_commit_oid": captured_commit,
        "authority_series_id": authority_manifest["authority_series_id"],
        "origin_id": origin_id,
        "cell_key": cell_key,
        (
            "referents__authority.workload.descriptor_sha256"
            "__preimage_ref__sha256"
        ): descriptor_sha256,
    })
    source_bytes = _canonical_origin_test_bytes(source_record)
    provisioning_receipt = {
        "authority_blob_sha256": hashlib.sha256(authority_bytes).hexdigest(),
        "source_closure_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "origin_id": origin_id,
        "cell_key": cell_key,
    }
    monkeypatch.setattr(
        reflux_source_closure,
        "resolve_by_contract_sha256",
        lambda digest: object()
        if digest == authority_manifest["environment_contract_sha256"]
        else (_ for _ in ()).throw(ValueError("unknown fixture contract")),
    )
    validated = reflux_source_closure.validate_source_closure(
        source_bytes,
        repo_root=registered.repo,
        authority_manifest=authority_manifest,
        report_cell={
            "descriptor": descriptor,
            "descriptor_binding": descriptor_binding,
        },
        candidate_authority_blob_sha256=hashlib.sha256(authority_bytes).hexdigest(),
        human_approval_receipt=provisioning_receipt,
    )
    authority_path.write_bytes(authority_bytes)
    _t325_git(
        registered.repo,
        "add",
        "--",
        str(authority_path.relative_to(registered.repo)),
    )
    _t325_git(registered.repo, "commit", "-m", "activate fixture origin")
    client = reflux_origin_client.OriginLedgerClient.for_fixture_repository(
        registered.repo
    )
    request = A.OriginBindingRequest(
        client=client,
        validated_source_closure=validated,
        authority_blob_bytes=authority_bytes,
        source_closure_bytes=source_bytes,
        provisioning_receipt=provisioning_receipt,
    )
    provisional_producer = A.OriginProducerInputs(
        run_plan_input=_origin_run_plan_input(),
        verifier_policy_bytes=(
            frozen.root / "artifacts" / "verifier-policy.json"
        ).read_bytes(),
        generator_closure={
            "schema_version": "fixture-generator-closure/v1",
            "generator_sha256": "a" * 64,
        },
        terminal_operation_id=(
            "public-origin-terminal-"
            + hashlib.sha256(str(tmp_path).encode("utf-8")).hexdigest()
        ),
    )
    issued_capabilities: list[object] = []
    original_issue = A.reflux_origin_binding.issue_origin_binding_capability

    def capture_issued_capability(**kwargs):
        assert "origin_campaign_run" not in (
            kwargs["prepared_campaign"].campaign.search_config
        )
        capability = original_issue(**kwargs)
        issued_capabilities.append(capability)
        return capability

    monkeypatch.setattr(
        A.reflux_origin_binding,
        "issue_origin_binding_capability",
        capture_issued_capability,
    )
    fresh_admission = A._trial_launch_admission(
        trial_manifest=registered.manifest_path,
        trial_id=registered.trial_id,
        workloads=["rr80"],
        generations=2,
        allow_unregistered_exploratory=False,
        effective_preregistration=registered.capability,
    )
    fresh_arm_execution = A.trial_registry.bind_trial_arm(
        fresh_admission.binding,
        repository_root=registered.repo,
    )
    preliminary_runtime = A._prepare_origin_trial_runtime(
        admission=fresh_admission,
        request=request,
        producer_inputs=provisional_producer,
        trial_id=registered.trial_id,
        selected=["rr80"],
        generations=2,
        trial_manifest=registered.manifest_path,
        effective_preregistration=registered.capability,
        build_context=_no_build_context(),
        arm_execution=fresh_arm_execution,
        campaign_output_root=frozen.evidence_root,
    )
    assert preliminary_runtime.producer_inputs.enforcement_arm == (
        fresh_arm_execution.resolved_input.arm
    )
    _align_origin_result_records(
        frozen,
        preliminary_runtime.capability,
        launch_admission_record_sha256=(
            preliminary_runtime.launch_admission_record_sha256
        ),
    )
    producer = provisional_producer
    original_complete = A._complete_origin_runtime
    sealed = False

    def materialize_then_complete(runtime):
        nonlocal sealed
        if not sealed:
            materialized = _materialize_origin_physical_evidence(
                frozen, runtime
            )
            _seal_origin_fixture_ledger(
                client,
                runtime.capability,
                runtime.run_plan,
                materialized,
            )
            sealed = True
        return original_complete(runtime)

    monkeypatch.setattr(
        A,
        "_complete_origin_runtime",
        materialize_then_complete,
    )
    return request, producer


def _origin_trial_arguments(registered, run_root: Path) -> dict[str, object]:
    return {
        "trial_id": registered.trial_id,
        "workloads": ["rr80"],
        "generations": 2,
        "provider_kind": "fixture",
        "run_root": run_root,
        "sub": "/unused",
        "do_build": False,
        "drive": _fake_drive,
        "preview": _fake_preview,
        "trial_manifest": registered.manifest_path,
        "effective_preregistration": registered.capability,
    }


def test_origin_public_path_preserves_capability_identity_and_projects_terminal(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    request, producer = _origin_public_inputs(
        tmp_path, monkeypatch, t325_registered_trial
    )
    issued: list[object] = []
    original_issue = A.reflux_origin_binding.issue_origin_binding_capability
    original_assert = A.trial_registry.assert_rederived_launch_admission
    original_finish = A._finish_trial
    original_run_workload = A._run_workload
    original_write = A.reflux_origin_topology.write_recovery_envelope_create_only
    original_evaluate = A.reflux_formal_consumer.evaluate_formal_origin
    snapshot_reads: list[object] = []
    envelope_roots: list[Path] = []
    formal_roots: list[str] = []
    formal_attempt_digests: list[str] = []
    original_read = reflux_origin_client.OriginLedgerClient.read_origin

    def observe_issue(**kwargs):
        assert "origin_campaign_run" not in (
            kwargs["prepared_campaign"].campaign.search_config
        )
        capability = original_issue(**kwargs)
        issued.append(capability)
        return capability

    def observe_assert(admission, **kwargs):
        if kwargs.get("origin_binding") is not None:
            assert kwargs["origin_binding"] is issued[0]
        return original_assert(admission, **kwargs)

    def observe_run_workload(**kwargs):
        runtime = kwargs["origin_runtime"]
        assert runtime.capability is issued[0]
        assert A._ACTIVE_TRIAL_BINDING.get().origin_capability is issued[0]
        return original_run_workload(**kwargs)

    def observe_finish(**kwargs):
        runtime = kwargs["origin_runtime"]
        assert runtime.capability is issued[0]
        assert A._ACTIVE_TRIAL_BINDING.get().origin_capability is issued[0]
        return original_finish(**kwargs)

    def observe_read(self, capability):
        snapshot_reads.append(capability)
        return original_read(self, capability)

    def observe_envelope_write(**kwargs):
        envelope_roots.append(Path(kwargs["evidence_root"]))
        return original_write(**kwargs)

    def observe_formal_evaluation(**kwargs):
        formal_roots.append(kwargs["campaign_output_root"])
        formal_attempt_digests.append(kwargs["attempt_capability_sha256"])
        return original_evaluate(**kwargs)

    monkeypatch.setattr(
        A.reflux_origin_binding, "issue_origin_binding_capability", observe_issue
    )
    monkeypatch.setattr(
        A.trial_registry, "assert_rederived_launch_admission", observe_assert
    )
    monkeypatch.setattr(A, "_finish_trial", observe_finish)
    monkeypatch.setattr(A, "_run_workload", observe_run_workload)
    monkeypatch.setattr(
        A.reflux_origin_topology,
        "write_recovery_envelope_create_only",
        observe_envelope_write,
    )
    monkeypatch.setattr(
        A.reflux_formal_consumer,
        "evaluate_formal_origin",
        observe_formal_evaluation,
    )
    monkeypatch.setattr(
        reflux_origin_client.OriginLedgerClient, "read_origin", observe_read
    )
    run_root = tmp_path / "origin-public-run"
    outcome = A.run_origin_trial(
        origin_binding_request=request,
        origin_producer_inputs=producer,
        **_origin_trial_arguments(t325_registered_trial, run_root),
    )
    assert type(outcome) is A.OriginCompletedTrialReport
    assert issued and all(capability is issued[0] for capability in snapshot_reads)
    assert envelope_roots == [run_root.resolve()]
    assert formal_roots == [str(envelope_roots[0])]
    assert len(formal_attempt_digests) == 1
    envelope_path = run_root / "origin" / "recovery-envelope.json"
    envelope_bytes = envelope_path.read_bytes()
    envelope = json.loads(envelope_bytes)
    assert envelope_bytes == _canonical_origin_test_bytes(envelope)
    assert len(envelope["members"]) == 33
    assert len({
        member["planned_campaign_run_identity"]
        for member in envelope["members"]
    }) == 33
    assert all(
        "fixture-run-" not in member["planned_campaign_run_identity"]
        for member in envelope["members"]
    )
    for member in envelope["members"]:
        campaign_run_identity = member["planned_campaign_run_identity"]
        physical_root = Path(A.exploration_campaign_layout(
            campaign_run_identity, formal_roots[0]
        ).root)
        decoded_lock = campaign_lock.decode_campaign_lock(
            (physical_root / "campaign.lock").read_text(encoding="utf-8")
        )
        assert decoded_lock.identity["search_config"]["origin_campaign_run"] == {
            "attempt_capability_sha256": formal_attempt_digests[0],
            "query_ordinal": member["query_ordinal"],
        }
        projection = json.loads(
            (physical_root / "reports" / "ordered-wal-projection.json")
            .read_bytes()
        )
        assert (
            run_root / projection["source_wal_ref"]["path"]
        ).is_file()
        provenance = json.loads(
            (physical_root / "reports" / "execution-provenance.json")
            .read_bytes()
        )
        assert provenance["campaign_run_identity"] == campaign_run_identity
        assert "fixture-run-" not in provenance["campaign_run_identity"]
    report = outcome.report
    assert "origin_terminal_projection" in report
    projection = report["origin_terminal_projection"]
    assert projection["reason_code"] == "P6Unavailable"
    assert projection["reason_code"] != "FC01"
    assert projection["formal_receipt_sha256"] is not None
    assert projection["evidence_root_sha256"] is not None
    assert request.client.read_origin(issued[0]).terminal_status == "aborted"
    lifecycle_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_LIFECYCLE_PATH
        ).read_bytes().splitlines()
    ]
    terminal = lifecycle_rows[-1]
    start = lifecycle_rows[-2]
    assert start["origin_run_plan_sha256"] == hashlib.sha256(
        envelope_bytes
    ).hexdigest()
    assert _canonical_origin_test_bytes({
        "origin_terminal_projection": report["origin_terminal_projection"]
    }) == _canonical_origin_test_bytes({
        "origin_terminal_projection": terminal["origin_terminal_projection"]
    })


def test_origin_client_omission_is_typed_preflight_before_production_resolution(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    request, producer = _origin_public_inputs(
        tmp_path, monkeypatch, t325_registered_trial
    )
    reached: list[bool] = []

    def forbidden_production_store():
        reached.append(True)
        raise AssertionError("production store resolution was reached")

    monkeypatch.setattr(
        reflux_origin_ledger, "_production_store", forbidden_production_store
    )
    run_root = tmp_path / "missing-origin-client"
    outcome = A.run_origin_trial(
        origin_binding_request=dataclasses.replace(request, client=None),
        origin_producer_inputs=producer,
        **_origin_trial_arguments(t325_registered_trial, run_root),
    )
    assert type(outcome) is A.OriginPreflightFailure
    assert reached == []
    assert not run_root.exists()


def test_origin_producer_arm_must_match_issued_capability_and_closed_arm_set(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    request, producer = _origin_public_inputs(
        tmp_path, monkeypatch, t325_registered_trial
    )
    invalid_root = tmp_path / "invalid-origin-producer-arm"
    invalid = A.run_origin_trial(
        origin_binding_request=request,
        origin_producer_inputs=dataclasses.replace(
            producer,
            enforcement_arm="not-an-arm",
        ),
        **_origin_trial_arguments(t325_registered_trial, invalid_root),
    )
    assert type(invalid) is A.OriginPreflightFailure
    assert "not a registered arm" in invalid.message
    assert not invalid_root.exists()

    issued_arm = t325_registered_trial.binding.arm
    different_arm = next(
        arm for arm in A.trial_registry.ARMS if arm != issued_arm
    )
    mismatch_root = tmp_path / "mismatched-origin-producer-arm"
    mismatch = A.run_origin_trial(
        origin_binding_request=request,
        origin_producer_inputs=dataclasses.replace(
            producer,
            enforcement_arm=different_arm,
        ),
        **_origin_trial_arguments(t325_registered_trial, mismatch_root),
    )
    assert type(mismatch) is A.OriginPreflightFailure
    assert "differs from issued capability" in mismatch.message
    assert not mismatch_root.exists()


def test_origin_arguments_are_all_or_none_before_artifact_creation(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    request, _producer = _origin_public_inputs(
        tmp_path, monkeypatch, t325_registered_trial
    )
    run_root = tmp_path / "one-sided-origin"
    with pytest.raises(A.AutonomousTrialError, match="must be supplied together"):
        A.run_trial(
            **_origin_trial_arguments(t325_registered_trial, run_root),
            origin_binding_request=request,
        )
    typed = A.run_origin_trial(
        **_origin_trial_arguments(t325_registered_trial, run_root),
        origin_binding_request=request,
    )
    assert type(typed) is A.OriginPreflightFailure
    assert not run_root.exists()


def test_origin_request_rejects_unregistered_exploratory_admission(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    request, producer = _origin_public_inputs(
        tmp_path, monkeypatch, t325_registered_trial
    )
    run_root = tmp_path / "origin-exploratory"
    arguments = _origin_trial_arguments(t325_registered_trial, run_root)
    arguments.update({
        "trial_id": "origin-unregistered",
        "workloads": ["ycsb-a"],
        "trial_manifest": None,
        "effective_preregistration": None,
        "allow_unregistered_exploratory": True,
    })
    outcome = A.run_origin_trial(
        origin_binding_request=request,
        origin_producer_inputs=producer,
        **arguments,
    )
    assert type(outcome) is A.OriginPreflightFailure
    assert "registered-effective" in outcome.message
    assert not run_root.exists()


def test_origin_public_result_distinguishes_partial_from_completed(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    request, producer = _origin_public_inputs(
        tmp_path, monkeypatch, t325_registered_trial
    )
    outcome = A.run_origin_trial(
        origin_binding_request=request,
        origin_producer_inputs=producer,
        providers={},
        **_origin_trial_arguments(
            t325_registered_trial, tmp_path / "origin-partial-run"
        ),
    )
    assert type(outcome) is A.OriginPartialTrialReport
    assert outcome.report is not None
    assert outcome.report["status"] == "partial"
    assert "origin_terminal_projection" in outcome.report


def test_origin_envelope_create_failure_is_preflight_and_pre_observation(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    request, producer = _origin_public_inputs(
        tmp_path, monkeypatch, t325_registered_trial
    )
    reached: list[str] = []

    def fail_envelope_write(**_kwargs):
        reached.append("envelope-write")
        raise reflux_origin_topology.TopologyError("fixture create-only failure")

    def forbidden_lifecycle_start(**_kwargs):
        pytest.fail("envelope failure reached lifecycle start")

    def forbidden_observation(*_args, **_kwargs):
        pytest.fail("envelope failure reached observation start")

    monkeypatch.setattr(
        A.reflux_origin_topology,
        "write_recovery_envelope_create_only",
        fail_envelope_write,
    )
    monkeypatch.setattr(
        A.trial_registry,
        "record_trial_start_once",
        forbidden_lifecycle_start,
    )
    monkeypatch.setattr(
        A.trial_registry,
        "begin_attempt_observation",
        forbidden_observation,
    )
    run_root = tmp_path / "origin-envelope-preflight-failure"
    outcome = A.run_origin_trial(
        origin_binding_request=request,
        origin_producer_inputs=producer,
        **_origin_trial_arguments(t325_registered_trial, run_root),
    )
    assert type(outcome) is A.OriginPreflightFailure
    assert reached == ["envelope-write"]
    assert not A._origin_lifecycle_started(
        trial_id=t325_registered_trial.trial_id,
        run_root=run_root,
    )


def test_origin_post_lifecycle_observation_failure_returns_reported_partial(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    request, producer = _origin_public_inputs(
        tmp_path, monkeypatch, t325_registered_trial
    )
    original_lifecycle_start = A.trial_registry.record_trial_start_once

    def compatible_lifecycle_start(**kwargs):
        if "origin_run_plan_sha256" not in inspect.signature(
            original_lifecycle_start
        ).parameters:
            kwargs.pop("origin_run_plan_sha256")
        return original_lifecycle_start(**kwargs)

    def fail_observation(*_args, **_kwargs):
        raise RuntimeError("fixture observation start failure")

    monkeypatch.setattr(
        A.trial_registry,
        "record_trial_start_once",
        compatible_lifecycle_start,
    )
    monkeypatch.setattr(
        A.trial_registry,
        "begin_attempt_observation",
        fail_observation,
    )
    run_root = tmp_path / "origin-observation-partial"
    outcome = A.run_origin_trial(
        origin_binding_request=request,
        origin_producer_inputs=producer,
        **_origin_trial_arguments(t325_registered_trial, run_root),
    )
    assert type(outcome) is A.OriginPartialTrialReport
    assert outcome.report is not None
    assert outcome.report["status"] == "partial"
    assert outcome.report["fatal_error"]["type"] == "RuntimeError"
    assert A._origin_lifecycle_started(
        trial_id=t325_registered_trial.trial_id,
        run_root=run_root,
    )
    lifecycle_rows = [
        json.loads(line)
        for line in (
            t325_registered_trial.repo
            / A.trial_registry.DEFAULT_LIFECYCLE_PATH
        ).read_bytes().splitlines()
    ]
    trial_rows = [
        row
        for row in lifecycle_rows
        if row["trial_id"] == t325_registered_trial.trial_id
    ]
    assert [row["event"] for row in trial_rows] == ["start", "terminal"]
    assert trial_rows[-1]["terminal_status"] == "indeterminate"
    assert trial_rows[-1]["failure_reason"] == "origin-producer-failure"
    assert "origin_terminal_projection" not in trial_rows[-1]


def test_originless_lifecycle_start_omits_run_plan_digest(
    tmp_path, monkeypatch, t325_registered_trial,
) -> None:
    observed: list[dict[str, object]] = []
    original = A.trial_registry.record_trial_start_once

    def observe_start(**kwargs):
        observed.append(dict(kwargs))
        return original(**kwargs)

    monkeypatch.setattr(
        A.trial_registry, "record_trial_start_once", observe_start,
    )
    report = _t325_run(
        t325_registered_trial, tmp_path / "originless-no-plan-digest",
    )
    assert report["status"] == "complete"
    assert len(observed) == 1
    assert "origin_binding" not in observed[0]
    assert "origin_run_plan_sha256" not in observed[0]


if __name__ == "__main__":  # pragma: no cover - plain-runner false-green guard
    raise SystemExit(pytest.main([__file__, "-x"]))


@pytest.mark.parametrize("case", [
    "caller-path", "missing-record", "query-order", "wrong-query", "caller-root",
    "duplicate-path", "missing-member", "symlink-record", "symlink-parent",
])
def test_origin_runtime_collects_only_producer_owned_evidence(
    tmp_path, monkeypatch, t325_registered_trial, case,
) -> None:
    """Mutate only after real fixture materialization and ledger sealing."""
    complete = A._complete_origin_runtime
    observed = []
    rejected = []
    changed = False
    failures = {
        "missing-record": "origin result evidence collection failed",
        "query-order": "query ordinals must be ascending",
        "wrong-query": "path does not match member",
        "duplicate-path": "paths must be distinct",
        "missing-member": "requires exactly 33 members",
        "symlink-record": "origin result evidence collection failed",
        "symlink-parent": "origin result evidence collection failed",
    }

    def inspect_then_complete(runtime):
        nonlocal changed
        observed.append(runtime)
        members = runtime.run_plan.members
        root = runtime.campaign_output_root
        if not changed:
            # All 33 records are valid and at their derived paths before the
            # single mutation; no consumer or collection mechanism is stubbed.
            assert len(members) == 33
            assert tuple(m.query_ordinal for m in members) == tuple(range(33))
            for member in members:
                raw = (root / member.evidence_path).read_bytes()
                record = A.reflux_result_evidence.parse_result_evidence_bytes(raw)
                assert A.reflux_result_evidence.result_evidence_relative_path(
                    record
                ).as_posix() == member.evidence_path
            if case == "caller-path":
                material = runtime.producer_inputs.run_plan_input.member_materials[0]
                with pytest.raises(TypeError, match="evidence_path"):
                    dataclasses.replace(material, evidence_path="reports/elsewhere.json")
                for member in members:
                    assert member.evidence_path == (
                        f"reports/reflux-result-evidence/{runtime.capability.origin_id}/"
                        f"{runtime.producer_inputs.run_plan_input.attempt_0_batch_id}/"
                        f"{member.query_ordinal}.json"
                    )
            elif case == "caller-root":
                with pytest.raises(TypeError, match="evidence_root"):
                    dataclasses.replace(runtime.producer_inputs, evidence_root=tmp_path / "other")
                with pytest.raises(TypeError, match="result_record_bytes"):
                    dataclasses.replace(runtime.producer_inputs, result_record_bytes=())
            elif case == "missing-record":
                (root / members[-1].evidence_path).unlink()
            elif case in {"query-order", "duplicate-path", "missing-member"}:
                if case == "query-order":
                    mutant = (members[1], members[0], *members[2:])
                elif case == "duplicate-path":
                    mutant = (dataclasses.replace(
                        members[0], evidence_path=members[1].evidence_path,
                    ), *members[1:])
                else:
                    mutant = members[:-1]
                # Normal construction already rejects these shapes. Simulate
                # corruption after construction to exercise the collection guard.
                with pytest.raises(reflux_origin_topology.TopologyError):
                    dataclasses.replace(runtime.run_plan, members=mutant)
                object.__setattr__(runtime.run_plan, "members", mutant)
            elif case == "wrong-query":
                (root / members[0].evidence_path).write_bytes(
                    (root / members[1].evidence_path).read_bytes()
                )
            elif case == "symlink-record":
                path = root / members[0].evidence_path
                referent = path.with_suffix(".saved")
                path.rename(referent)
                path.symlink_to(referent)
            elif case == "symlink-parent":
                parent = (root / members[0].evidence_path).parent
                referent = parent.with_name(parent.name + "-saved")
                parent.rename(referent)
                parent.symlink_to(referent, target_is_directory=True)
            changed = True
        if case in failures:
            before = runtime.client.read_origin(runtime.capability)
            with pytest.raises(A.AutonomousTrialError, match=failures[case]) as caught:
                complete(runtime)
            assert runtime.terminal_projection is None
            assert runtime.client.read_origin(runtime.capability) == before
            rejected.append(caught.value)
            raise caught.value
        return complete(runtime)

    monkeypatch.setattr(A, "_complete_origin_runtime", inspect_then_complete)
    request, producer = _origin_public_inputs(
        tmp_path, monkeypatch, t325_registered_trial,
    )
    original_evaluate = A.reflux_formal_consumer.evaluate_formal_origin
    evaluations = []

    def observe_evaluate(**kwargs):
        evaluations.append(kwargs)
        assert kwargs["evidence_root"] == observed[-1].campaign_output_root
        assert kwargs["result_record_bytes"] == tuple(
            (kwargs["evidence_root"] / member.evidence_path).read_bytes()
            for member in observed[-1].run_plan.members
        )
        return original_evaluate(**kwargs)

    monkeypatch.setattr(
        A.reflux_formal_consumer, "evaluate_formal_origin", observe_evaluate,
    )
    outcome = A.run_origin_trial(
        origin_binding_request=request,
        origin_producer_inputs=producer,
        **_origin_trial_arguments(t325_registered_trial, tmp_path / "collected-origin"),
    )
    assert observed
    if case in failures:
        assert rejected
        assert not evaluations
        assert type(outcome) is A.OriginPartialTrialReport
        assert outcome.error_type == "AutonomousTrialError"
    else:
        assert evaluations
        assert type(outcome) is A.OriginCompletedTrialReport


@pytest.mark.parametrize("token", ["", ".", "..", "a/b", "a\\b", "a\x00b", "\ud800"])
@pytest.mark.parametrize("field", ["origin_id", "batch_id"])
def test_origin_evidence_path_reuses_result_evidence_token_rejection(token, field):
    inputs = {"origin_id": "origin", "batch_id": "batch", "query_ordinal": 0}
    inputs[field] = token
    with pytest.raises(A.reflux_result_evidence.ResultEvidenceError):
        A.reflux_result_evidence._safe_path_token(token, label=field)
    with pytest.raises(A.AutonomousTrialError):
        A._origin_result_evidence_path(**inputs)
