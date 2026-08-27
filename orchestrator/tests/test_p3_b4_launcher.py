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
from orchestrator.campaign import p3_b4_protocol as B4P
from orchestrator.campaign import p3_s4_loop as L
from orchestrator.campaign import p3_s4_loop_sort as S
from orchestrator.campaign import p3_s4_loop_trigger_gating as T
from orchestrator.campaign import wal
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.campaign.model import STAGE_COMMIT, WalRecord
from orchestrator.verifier.commit_receipt import CommitReceiptError
from test_p3_b4_closed_critic import (  # noqa: E402
    _committed_admission_fixture,
    _production_launch_context as _verified_b4_context,
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


def _production_context(
    cfg=None,
    *,
    driver_kind="base",
    arm="on",
    admission=None,
    action=None,
    layout=None,
):
    return _verified_b4_context(
        cfg,
        driver_kind=driver_kind,
        arm=arm,
        admission=admission,
        action=action,
        layout=layout,
    )


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

    def corrupt_sidecar(_context, launch_layout):
        path = Path(launch_layout.root) / B4L.B4_LAUNCH_SIDECAR
        sidecar = json.loads(path.read_bytes())
        sidecar["campaign_id"] = "another-campaign"
        path.write_bytes(B4L._canonical_json_bytes(sidecar))
        return wal.append(launch_layout, _commit_record())

    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="bound to another campaign",
    ):
        _production_context(cfg, action=corrupt_sidecar, layout=layout)
    assert not Path(layout.wal_file).exists()


def test_m13_real_wal_commit_rejects_sidecar_for_other_live_context(tmp_path):
    """M13: real wal.append rejects a correct sidecar with another live context."""
    cfg, layout = _marked_layout(tmp_path)
    first_admission = _committed_admission_fixture(
        expected_model="claude-opus-5-m13-first",
    )
    second_admission = _committed_admission_fixture(
        expected_model="claude-opus-5-m13-second",
    )
    sidecar_bytes = _production_context(
        cfg,
        admission=first_admission,
        layout=layout,
        action=lambda _context, launch_layout: (
            Path(launch_layout.root) / B4L.B4_LAUNCH_SIDECAR
        ).read_bytes(),
    )

    def restore_other_sidecar(_context, launch_layout):
        (Path(launch_layout.root) / B4L.B4_LAUNCH_SIDECAR).write_bytes(
            sidecar_bytes
        )
        return wal.append(launch_layout, _commit_record())

    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="differs from the live launch context",
    ):
        _production_context(
            cfg,
            admission=second_admission,
            action=restore_other_sidecar,
            layout=layout,
        )
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
    context = _production_context(driver_kind="sort")
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
            expected_driver_kind="base",
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
    invalid_record = tmp_path / "invalid-admission.json"
    invalid_record.write_text("{}", encoding="utf-8")
    driver_spy = mock.Mock(side_effect=AssertionError("driver reached"))
    monkeypatch.setitem(B4L.DRIVER_REGISTRY, "base", driver_spy)
    with pytest.raises(A.B4AdmissionRecordError):
        B4L.launch_bootstrap(
            driver_kind="base",
            arm="on",
            admission_record_path=invalid_record,
            proposal_path=tmp_path / "proposal.json",
        )
    assert driver_spy.call_count == 0


def test_production_issuer_and_activation_are_not_module_attributes():
    """F1: only closure launchers can mint and activate the production seal."""
    for name in (
        "_create_b4_production_context",
        "_bind_b4_campaign",
        "_write_b4_launch_sidecar",
        "_activate_b4_launch_context",
        "_B4_PRODUCTION_CONTEXT_SEAL",
        "_ACTIVE_B4_LAUNCH_CONTEXT",
        "_build_launcher_closure",
    ):
        assert not hasattr(B4L, name)


def test_launch_sidecar_is_overwritable_for_remeasurement(tmp_path):
    cfg, layout = _marked_layout(tmp_path)
    first_admission = _committed_admission_fixture(
        expected_model="claude-opus-5-overwrite-first",
    )
    second_admission = _committed_admission_fixture(
        expected_model="claude-opus-5-overwrite-second",
    )

    def observe(context, launch_layout):
        path = Path(launch_layout.root) / B4L.B4_LAUNCH_SIDECAR
        verified = B4L.verify_b4_launch_context(
            launch_layout,
            expected_driver_kind="base",
            expected_campaign_id=str(ident.campaign_id(cfg)),
            expected_arm="on",
        )
        assert verified is context
        return path, path.read_bytes()

    first_path, first_bytes = _production_context(
        cfg,
        admission=first_admission,
        action=observe,
        layout=layout,
    )
    second_path, second_bytes = _production_context(
        cfg,
        admission=second_admission,
        action=observe,
        layout=layout,
    )
    assert first_path == second_path
    assert first_bytes != second_bytes


@pytest.mark.parametrize(
    ("lock_change", "message"),
    (
        ("driver", "driver kind differs"),
        ("arm", "arm differs"),
    ),
)
def test_g4_uses_decoded_lock_expectations(
    tmp_path, lock_change, message,
):
    """F2/F3: G4 compares the live context with decoded lock fields."""
    cfg, layout = _marked_layout(tmp_path)
    identity = json.loads(ident.canonical_preimage(cfg))
    if lock_change == "driver":
        identity["search_tag"] = "s5-sort-autonomous"
        identity["trial"] = "p3-s5-sort-loop"
        identity["search_config"]["axis"] = "silo-writeset-sort"
    else:
        identity["search_config"]["reflux"] = "off"
    Path(layout.lock_file).write_text(
        json.dumps(
            identity,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )

    with pytest.raises(B4L.B4LauncherAuthorizationError, match=message):
        _production_context(
            cfg,
            layout=layout,
            action=lambda _context, launch_layout: wal.append(
                launch_layout, _commit_record()
            ),
        )
    assert not Path(layout.wal_file).exists()


def test_production_validator_requires_exact_campaign_and_arm():
    """F3: the central validator rejects both binding dimensions exactly."""
    cfg, _off_cfg = _marked_base_pair()
    context = _production_context(cfg)
    campaign_id = str(ident.campaign_id(cfg))
    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="campaign id differs",
    ):
        B4L.require_b4_production_context(
            context,
            expected_driver_kind="base",
            expected_campaign_id=f"{campaign_id}-other",
            expected_arm="on",
            boundary="binding regression",
        )
    with pytest.raises(B4L.B4LauncherAuthorizationError, match="arm differs"):
        B4L.require_b4_production_context(
            context,
            expected_driver_kind="base",
            expected_campaign_id=campaign_id,
            expected_arm="off",
            boundary="binding regression",
        )


@pytest.mark.parametrize("raw", (b"\xff", b"{}"))
def test_existing_unclassifiable_lock_rejects_commit(tmp_path, raw):
    """F4: invalid UTF-8 and invalid lock schema both fail closed."""
    layout = CampaignLayout(str(tmp_path / "invalid-lock")).ensure()
    Path(layout.lock_file).write_bytes(raw)
    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="cannot classify",
    ):
        wal.append(layout, _commit_record())
    assert not Path(layout.wal_file).exists()


def test_existing_unreadable_lock_rejects_commit(tmp_path):
    """F4: an existing lock that cannot be read does not bypass G4."""
    layout = CampaignLayout(str(tmp_path / "unreadable-lock")).ensure()
    Path(layout.lock_file).mkdir()
    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="cannot classify",
    ):
        wal.append(layout, _commit_record())
    assert not Path(layout.wal_file).exists()


def test_all_drivers_and_wal_import_the_protocol_constants():
    """F4: the marker has one low-level source of truth."""
    for module in (L, S, T, wal):
        assert module.B4_PROTOCOL_KEY is B4P.B4_PROTOCOL_KEY
        assert module.B4_PROTOCOL_VALUE is B4P.B4_PROTOCOL_VALUE


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
