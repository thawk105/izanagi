# -*- coding: utf-8 -*-
"""Mutation-red tests for the exclusive P3 B-4 launcher chokepoints."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from unittest import mock

import pytest

from orchestrator.campaign import ident
from orchestrator.campaign import p3_b4_admission_record as A
from orchestrator.campaign import p3_b4_closed_critic as C
from orchestrator.campaign import p3_b4_launcher as B4L
from orchestrator.campaign import p3_s4_loop as L
from orchestrator.campaign import p3_s4_loop_sort as S
from orchestrator.campaign import p3_s4_loop_trigger_gating as T
from orchestrator.campaign import wal
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.campaign.model import STAGE_COMMIT, WalRecord
from orchestrator.verifier.commit_receipt import CommitReceiptError


_VERIFIED = A.VerifiedB4AdmissionRecord(
    admission_record_repository_path="admission.json",
    admission_record_sha256="1" * 64,
    admission_record_commit="2" * 40,
    preregistration_repository_path="docs/preregistration.md",
    preregistration_content_commit="3" * 40,
    preregistration_content_sha256="4" * 64,
    expected_claude_model_snapshot="fixture-model",
    expected_effective_critic_prompt_sha256="5" * 64,
    expected_closed_critic_projection_closure_sha256="6" * 64,
)


def _test_context(driver_kind="base", arm="on"):
    return B4L.create_b4_launch_context_for_test(
        driver_kind=driver_kind,
        arm=arm,
    )


def _marked_base_pair():
    context = _test_context()
    return (
        L.default_cfg(
            reflux=True,
            b4_reflux_ablation=True,
            _b4_launch_context=context,
        ),
        L.default_cfg(
            reflux=False,
            b4_reflux_ablation=True,
            _b4_launch_context=context,
        ),
    )


def _production_context(cfg, *, driver_kind="base", arm="on"):
    context = B4L._create_b4_production_context(
        _VERIFIED,
        driver_kind=driver_kind,
        arm=arm,
    )
    return B4L._bind_b4_campaign(context, str(ident.campaign_id(cfg)))


def _marked_layout(tmp_path: Path):
    on_cfg, _off_cfg = _marked_base_pair()
    campaign_id = str(ident.campaign_id(on_cfg))
    layout = CampaignLayout(str(tmp_path / campaign_id)).ensure()
    wal.write_lock(layout, ident.canonical_preimage(on_cfg))
    return on_cfg, layout


def _commit_record():
    return WalRecord(
        variant="fixture-variant",
        stage=STAGE_COMMIT,
        env_tag=L.ENV_TAG,
        ts=1.0,
        payload={},
    )


def test_m11_real_wal_commit_requires_launch_sidecar(tmp_path):
    """M11: real wal.append rejects a marked lock when sidecar is absent."""
    _cfg, layout = _marked_layout(tmp_path)
    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="requires b4_launch_context.json",
    ):
        wal.append(layout, _commit_record())
    assert not Path(layout.wal_file).exists()


def test_m12_real_wal_commit_rejects_sidecar_for_another_campaign(tmp_path):
    """M12: real wal.append and real G4 reject a cross-campaign sidecar."""
    cfg, layout = _marked_layout(tmp_path)
    context = _production_context(cfg)
    sidecar = B4L._sidecar_value(context)
    sidecar["campaign_id"] = "another-campaign"
    (Path(layout.root) / B4L.B4_LAUNCH_SIDECAR).write_bytes(
        B4L._canonical_json_bytes(sidecar)
    )
    with B4L._activate_b4_launch_context(context):
        with pytest.raises(
            B4L.B4LauncherAuthorizationError,
            match="bound to another campaign",
        ):
            wal.append(layout, _commit_record())
    assert not Path(layout.wal_file).exists()


def test_m13_real_wal_commit_rejects_sidecar_for_other_live_context(tmp_path):
    """M13: real wal.append rejects a correct sidecar with another live context."""
    cfg, layout = _marked_layout(tmp_path)
    sidecar_context = _production_context(cfg, arm="on")
    live_context = _production_context(cfg, arm="off")
    B4L._write_b4_launch_sidecar(layout, sidecar_context)
    with B4L._activate_b4_launch_context(live_context):
        with pytest.raises(
            B4L.B4LauncherAuthorizationError,
            match="differs from the live launch context",
        ):
            wal.append(layout, _commit_record())
    assert not Path(layout.wal_file).exists()


def test_m14_real_production_pair_factory_requires_launch_context(tmp_path):
    """M14: the real production factory rejects before record or artifact I/O."""
    on_cfg, off_cfg = _marked_base_pair()
    artifact_root = tmp_path / "m14-artifacts"
    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="production pair factory",
    ):
        C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=artifact_root,
            admission_record_path=tmp_path / "missing-admission.json",
            expected_driver_kind="base",
            _b4_launch_context=None,
        )
    assert not artifact_root.exists()


def test_m15_real_production_pair_factory_rejects_cross_driver_context(tmp_path):
    """M15: the real factory checks exact context and expected driver kind."""
    on_cfg, off_cfg = _marked_base_pair()
    context = _production_context(on_cfg, driver_kind="base")
    artifact_root = tmp_path / "m15-artifacts"
    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="driver kind differs",
    ):
        C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=artifact_root,
            admission_record_path=tmp_path / "missing-admission.json",
            expected_driver_kind="sort",
            _b4_launch_context=context,
        )
    assert not artifact_root.exists()


def test_m16_test_seal_cannot_be_promoted_by_evidence_class(tmp_path):
    """M16: the real factory rejects test seal identity despite production text."""
    on_cfg, off_cfg = _marked_base_pair()
    campaign_id = str(ident.campaign_id(on_cfg))
    forged = B4L._new_context(
        seal=B4L._B4_TEST_CONTEXT_SEAL,
        evidence_class="production",
        driver_kind="base",
        arm="on",
        admission_record_sha256="1" * 64,
        admission_record_commit="2" * 40,
        campaign_id=campaign_id,
    )
    artifact_root = tmp_path / "m16-artifacts"
    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="test-only",
    ):
        C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=artifact_root,
            admission_record_path=tmp_path / "missing-admission.json",
            expected_driver_kind="base",
            _b4_launch_context=forged,
        )
    assert forged.evidence_class == "production"
    assert not artifact_root.exists()


def test_m17_real_legacy_cli_hard_fails_before_factory():
    """M17: the real retired CLI cannot reach even an injected pair factory."""
    factory = mock.Mock()
    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="orchestrator.campaign.p3_b4_launcher",
    ):
        C.main([], pair_factory=factory)
    assert factory.call_count == 0


def test_m18_driver_registry_uses_real_main_object_identity():
    """M18: registry values are the three real main objects by identity."""
    assert B4L.DRIVER_REGISTRY == {
        "base": L.main,
        "sort": S.main,
        "trigger": T.main,
    }
    assert B4L.DRIVER_REGISTRY["base"] is L.main
    assert B4L.DRIVER_REGISTRY["sort"] is S.main
    assert B4L.DRIVER_REGISTRY["trigger"] is T.main


def test_g9_bootstrap_uses_real_verifier_before_driver(tmp_path, monkeypatch):
    """Routing evidence only, not a mutation-negative substitute."""
    driver_spy = mock.Mock(side_effect=AssertionError("driver reached"))
    monkeypatch.setitem(B4L.DRIVER_REGISTRY, "base", driver_spy)
    with pytest.raises(A.B4AdmissionRecordError):
        B4L.launch_bootstrap(
            driver_kind="base",
            arm="on",
            admission_record_path=tmp_path / "invalid-admission.json",
            proposal_path=tmp_path / "proposal.json",
        )
    assert driver_spy.call_count == 0


def test_launch_sidecar_is_overwritable_for_remeasurement(tmp_path):
    cfg, layout = _marked_layout(tmp_path)
    first = _production_context(cfg, arm="on")
    second = _production_context(cfg, arm="off")
    path = B4L._write_b4_launch_sidecar(layout, first)
    first_bytes = path.read_bytes()
    assert B4L._write_b4_launch_sidecar(layout, second) == path
    assert path.read_bytes() != first_bytes
    with B4L._activate_b4_launch_context(second):
        assert B4L.verify_b4_launch_context(layout) is second


def test_unmarked_commit_does_not_execute_b4_sink_gate(tmp_path, monkeypatch):
    ordinary = L.default_cfg()
    campaign_id = str(ident.campaign_id(ordinary))
    layout = CampaignLayout(str(tmp_path / campaign_id)).ensure()
    wal.write_lock(layout, ident.canonical_preimage(ordinary))
    gate_spy = mock.Mock(
        side_effect=AssertionError("ordinary COMMIT reached the B-4 gate")
    )
    monkeypatch.setattr(B4L, "verify_b4_launch_context", gate_spy)
    with pytest.raises(CommitReceiptError):
        wal.append(layout, _commit_record())
    assert gate_spy.call_count == 0


def test_context_is_not_persisted_in_campaign_identity():
    context = _test_context()
    marked = L.default_cfg(
        b4_reflux_ablation=True,
        _b4_launch_context=context,
    )
    assert set(marked.search_config) == {
        "scale", "axis", "reflux", "records", "threads",
        L.B4_PROTOCOL_KEY,
        "build_admission",
    }
    assert all(value is not context for value in marked.search_config.values())
    assert not hasattr(marked, "b4_launch_context")
