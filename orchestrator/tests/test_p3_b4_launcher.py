# -*- coding: utf-8 -*-
"""Mutation-red tests for the exclusive P3 B-4 launcher chokepoints."""
from __future__ import annotations

import ast
from dataclasses import replace
import inspect
import json
from pathlib import Path
import sys
from unittest import mock

import pytest

from orchestrator.campaign import backoff_hole_grammar
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
import commit_receipt_support
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


def _commit_with_live_receipt(layout):
    record = _commit_record()
    receipt = commit_receipt_support.campaign_receipt(
        layout,
        record.variant,
        record.payload,
    )
    return wal.append(layout, record, commit_receipt=receipt)


def _production_text_context(cfg, admission, *, seal):
    verified = A.verify_b4_admission_record(
        admission.record_path,
        repository_root=admission.repository,
        driver_kind="base",
    )
    values = {
        "evidence_class": "production",
        "driver_kind": "base",
        "arm": "on",
        "admission_record_sha256": verified.admission_record_sha256,
        "admission_record_commit": verified.admission_record_commit,
        "campaign_id": str(ident.campaign_id(cfg)),
    }
    return B4L.B4LaunchContext(
        _seal=seal,
        **values,
        context_sha256=B4L._context_sha256(**values),
    )


def _with_campaign_id(context, campaign_id):
    values = {
        "evidence_class": context.evidence_class,
        "driver_kind": context.driver_kind,
        "arm": context.arm,
        "admission_record_sha256": context.admission_record_sha256,
        "admission_record_commit": context.admission_record_commit,
        "campaign_id": campaign_id,
    }
    return replace(
        context,
        campaign_id=campaign_id,
        context_sha256=B4L._context_sha256(**values),
    )


def test_m11_real_wal_commit_requires_launch_sidecar(tmp_path):
    """M11: real wal.append rejects a marked lock when sidecar is absent."""
    cfg, layout = _marked_layout(tmp_path)

    def append_without_sidecar(_context, launch_layout):
        (Path(launch_layout.root) / B4L.B4_LAUNCH_SIDECAR).unlink()
        return _commit_with_live_receipt(launch_layout)

    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="requires b4_launch_context.json",
    ):
        _production_context(
            cfg,
            action=append_without_sidecar,
            layout=layout,
        )
    assert not Path(layout.wal_file).exists()


def test_m12_real_wal_commit_rejects_sidecar_for_another_campaign(tmp_path):
    """M12: real wal.append and real G4 reject a cross-campaign sidecar."""
    cfg, layout = _marked_layout(tmp_path)

    def corrupt_sidecar(_context, launch_layout):
        path = Path(launch_layout.root) / B4L.B4_LAUNCH_SIDECAR
        sidecar = json.loads(path.read_bytes())
        sidecar["campaign_id"] = "another-campaign"
        path.write_bytes(B4L._canonical_json_bytes(sidecar))
        return _commit_with_live_receipt(launch_layout)

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
        return _commit_with_live_receipt(launch_layout)

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


def test_m14_real_production_pair_factory_requires_launch_context(
    tmp_path, monkeypatch,
):
    """M14: the real production factory rejects before record or artifact I/O."""
    on_cfg, off_cfg = _marked_base_pair()
    admission = _committed_admission_fixture(
        expected_model="claude-opus-5-m14",
    )
    unsealed = _production_text_context(on_cfg, admission, seal=object())
    artifact_root = tmp_path / "m14-artifacts"
    monkeypatch.setattr(C.shutil, "which", lambda _name: sys.executable)
    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="production pair factory",
    ):
        C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=artifact_root,
            admission_record_path=admission.record_path,
            expected_driver_kind="base",
            _b4_launch_context=unsealed,
            repository_root=admission.repository,
        )
    assert not artifact_root.exists()


def test_m15_real_production_pair_factory_rejects_cross_driver_context(
    tmp_path, monkeypatch,
):
    """M15: the real factory checks exact context and expected driver kind."""
    on_cfg, off_cfg = _marked_base_pair()
    admission = _committed_admission_fixture(
        expected_model="claude-opus-5-m15",
        driver_kind="sort",
    )
    context = _with_campaign_id(
        _production_context(driver_kind="sort", admission=admission),
        str(ident.campaign_id(on_cfg)),
    )
    artifact_root = tmp_path / "m15-artifacts"
    monkeypatch.setattr(C.shutil, "which", lambda _name: sys.executable)
    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="driver kind differs",
    ):
        C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=artifact_root,
            admission_record_path=admission.record_path,
            expected_driver_kind="base",
            _b4_launch_context=context,
            repository_root=admission.repository,
        )
    assert not artifact_root.exists()


def test_m16_test_seal_cannot_be_promoted_by_evidence_class(
    tmp_path, monkeypatch,
):
    """M16: the real factory rejects test seal identity despite production text."""
    on_cfg, off_cfg = _marked_base_pair()
    admission = _committed_admission_fixture(
        expected_model="claude-opus-5-m16",
    )
    forged = _production_text_context(
        on_cfg,
        admission,
        seal=_test_context()._seal,
    )
    artifact_root = tmp_path / "m16-artifacts"
    monkeypatch.setattr(C.shutil, "which", lambda _name: sys.executable)
    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="test-only",
    ):
        C.create_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=artifact_root,
            admission_record_path=admission.record_path,
            expected_driver_kind="base",
            _b4_launch_context=forged,
            repository_root=admission.repository,
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
            b4_prerun_publication=tmp_path / "publication",
            b4_attempt_id="attempt-0000",
        )
    assert driver_spy.call_count == 0


def test_bootstrap_matching_record_checks_all_projections_then_launches(
    tmp_path, monkeypatch,
):
    admission = _committed_admission_fixture()
    layouts = {}

    def layout_for(campaign_id):
        return layouts.setdefault(
            campaign_id,
            CampaignLayout(str(tmp_path / campaign_id)),
        )

    driver_spy = mock.Mock(return_value=23)
    monkeypatch.setattr(C, "REPOSITORY_ROOT", admission.repository)
    monkeypatch.setattr(B4L, "exploration_campaign_layout", layout_for)
    monkeypatch.setitem(B4L.DRIVER_REGISTRY, "base", driver_spy)
    result = B4L.launch_bootstrap(
        driver_kind="base",
        arm="on",
        admission_record_path=admission.record_path,
        proposal_path=tmp_path / "proposal.json",
        b4_prerun_publication=tmp_path / "publication",
        b4_attempt_id="attempt-0000",
    )
    assert result == 23
    driver_spy.assert_called_once()
    driver_argv = driver_spy.call_args.args[0]
    assert driver_argv.count("--b4-prerun-publication") == 1
    assert driver_argv.count("--b4-attempt-id") == 1
    assert driver_argv[driver_argv.index("--b4-prerun-publication") + 1] == str(
        tmp_path / "publication"
    )
    assert driver_argv[driver_argv.index("--b4-attempt-id") + 1] == (
        "attempt-0000"
    )
    assert len(layouts) == 1
    layout = next(iter(layouts.values()))
    assert (Path(layout.root) / B4L.B4_LAUNCH_SIDECAR).is_file()


def test_bootstrap_rejects_stale_or_driver_mismatched_projection_before_sidecar(
    tmp_path, monkeypatch,
):
    live_projections = {
        kind: C.projection_sha256(kind)
        for kind in A.B4_PROJECTION_DRIVER_KINDS
    }
    stale_projections = {
        kind: (
            ("0" if value[0] != "0" else "1") + value[1:]
        )
        for kind, value in live_projections.items()
    }
    stale_admission = _committed_admission_fixture(
        document_projections=stale_projections,
        expected_projection=stale_projections["base"],
    )
    mismatched_admission = _committed_admission_fixture(
        expected_projection=stale_projections["base"],
        verify_record=False,
    )
    for case_name, admission in (
        ("stale-document", stale_admission),
        ("driver-document-mismatch", mismatched_admission),
    ):
        layout_root = tmp_path / case_name
        layout_spy = mock.Mock(
            return_value=CampaignLayout(str(layout_root))
        )
        driver_spy = mock.Mock(
            side_effect=AssertionError("driver must not be called")
        )
        monkeypatch.setattr(C, "REPOSITORY_ROOT", admission.repository)
        monkeypatch.setattr(
            B4L,
            "exploration_campaign_layout",
            layout_spy,
        )
        monkeypatch.setitem(B4L.DRIVER_REGISTRY, "base", driver_spy)
        with pytest.raises(A.B4AdmissionRecordError):
            B4L.launch_bootstrap(
                driver_kind="base",
                arm="on",
                admission_record_path=admission.record_path,
                proposal_path=tmp_path / f"{case_name}-proposal.json",
                b4_prerun_publication=tmp_path / "publication",
                b4_attempt_id="attempt-0000",
            )
        driver_spy.assert_not_called()
        layout_spy.assert_not_called()
        assert not layout_root.exists()
        assert not (layout_root / B4L.B4_LAUNCH_SIDECAR).exists()


def test_module_attributes_cannot_mint_a_production_context(monkeypatch):
    """F1: try every direct module attribute as a context or context factory.

    Function closure cells are intentionally not traversed.  Resistance to
    same-process closure introspection and module-attribute replacement is a
    documented non-guarantee, not a property asserted by this test.
    """
    admission = _committed_admission_fixture(
        expected_model="claude-opus-5-module-surface",
    )
    monkeypatch.setattr(C, "REPOSITORY_ROOT", admission.repository)
    verified = A.verify_b4_admission_record(
        admission.record_path,
        repository_root=admission.repository,
        driver_kind="base",
    )
    campaign_id = "module-surface-campaign"
    attributes = tuple(vars(B4L).values())

    def context_for(seal):
        values = {
            "evidence_class": "production",
            "driver_kind": "base",
            "arm": "on",
            "admission_record_sha256": verified.admission_record_sha256,
            "admission_record_commit": verified.admission_record_commit,
            "campaign_id": campaign_id,
        }
        return B4L.B4LaunchContext(
            _seal=seal,
            **values,
            context_sha256=B4L._context_sha256(**values),
        )

    def assert_rejected(candidate):
        if type(candidate) is B4L.B4LaunchContext:
            candidate = _with_campaign_id(candidate, campaign_id)
        with pytest.raises(B4L.B4LauncherAuthorizationError):
            B4L.require_b4_production_context(
                candidate,
                expected_driver_kind="base",
                expected_campaign_id=campaign_id,
                expected_arm="on",
                boundary="module attribute surface",
            )

    def invoke_context_factory(factory, seal):
        if factory is B4L.B4LaunchContext:
            return context_for(seal)
        if not inspect.isfunction(factory):
            return None
        if factory.__module__ != B4L.__name__:
            return None
        signature = inspect.signature(factory)
        if "B4LaunchContext" not in str(signature.return_annotation):
            return None
        supplied = {
            "seal": seal,
            "_seal": seal,
            "context": context_for(seal),
            "evidence_class": "production",
            "driver_kind": "base",
            "arm": "on",
            "admission_record_sha256": verified.admission_record_sha256,
            "admission_record_commit": verified.admission_record_commit,
            "campaign_id": campaign_id,
            "admission_record_path": admission.record_path,
            "boundary": "module attribute factory",
            "expected_driver_kind": "base",
            "expected_campaign_id": campaign_id,
            "expected_arm": "on",
        }
        kwargs = {}
        for parameter in signature.parameters.values():
            if parameter.kind in {
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            }:
                continue
            if parameter.name in supplied:
                kwargs[parameter.name] = supplied[parameter.name]
            elif parameter.default is inspect.Parameter.empty:
                return None
        try:
            return factory(**kwargs)
        except (B4L.B4LauncherAuthorizationError, TypeError, ValueError):
            return None

    for attribute in attributes:
        assert_rejected(attribute)
        for seal in attributes:
            produced = invoke_context_factory(attribute, seal)
            if type(produced) is tuple:
                for item in produced:
                    assert_rejected(item)
            elif produced is not None:
                assert_rejected(produced)


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


def test_g4_rejects_decoded_campaign_identity_behind_matching_directory(
    tmp_path,
):
    """G4 derives campaign id from lock identity, not the layout basename."""
    cfg, layout = _marked_layout(tmp_path)
    identity = json.loads(Path(layout.lock_file).read_bytes())
    identity["search_config"]["records"] += 1
    Path(layout.lock_file).write_bytes(B4L._canonical_json_bytes(identity))

    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match=(
            "bound to another campaign"
            "|campaign id differs at certified sink"
        ),
    ):
        _production_context(
            cfg,
            layout=layout,
            action=lambda _context, launch_layout: wal.append(
                launch_layout, _commit_record()
            ),
        )
    assert not Path(layout.wal_file).exists()


def test_commit_receipt_uses_same_lock_snapshot_as_b4_classification(
    tmp_path, monkeypatch,
):
    """A markerless classification cannot borrow a later marked lock hash."""
    _cfg, layout = _marked_layout(tmp_path)
    marked_lock = Path(layout.lock_file).read_bytes()
    record = _commit_record()
    receipt = commit_receipt_support.campaign_receipt(
        layout,
        record.variant,
        record.payload,
    )
    markerless_identity = json.loads(marked_lock)
    markerless_identity["search_config"].pop(B4P.B4_PROTOCOL_KEY)
    Path(layout.lock_file).write_bytes(
        B4L._canonical_json_bytes(markerless_identity)
    )
    real_classifier = wal._has_exact_b4_protocol_marker

    def replace_lock_after_classification(decoded):
        marked = real_classifier(decoded)
        assert marked is False
        replacement = Path(layout.root) / "campaign.lock.replacement"
        replacement.write_bytes(marked_lock)
        replacement.replace(layout.lock_file)
        return marked

    monkeypatch.setattr(
        wal,
        "_has_exact_b4_protocol_marker",
        replace_lock_after_classification,
    )
    with pytest.raises(CommitReceiptError, match="binding mismatch"):
        wal.append(layout, record, commit_receipt=receipt)
    assert wal.read_records(layout) == []


def test_m21_absent_lock_snapshot_rejects_restored_marked_receipt(
    tmp_path, monkeypatch,
):
    """An absent classification cannot borrow a restored marked lock receipt."""
    _cfg, layout = _marked_layout(tmp_path)
    marked_lock = Path(layout.lock_file).read_bytes()
    record = _commit_record()
    receipt = commit_receipt_support.campaign_receipt(
        layout,
        record.variant,
        record.payload,
    )
    Path(layout.lock_file).unlink()
    real_classifier = wal._has_exact_b4_protocol_marker
    gate_spy = mock.Mock(
        side_effect=AssertionError("absent snapshot reached the B-4 gate")
    )
    monkeypatch.setattr(B4L, "verify_b4_launch_context", gate_spy)

    def restore_lock_after_classification(decoded):
        marked = real_classifier(decoded)
        assert decoded is None
        assert marked is False
        replacement = Path(layout.root) / "campaign.lock.replacement"
        replacement.write_bytes(marked_lock)
        replacement.replace(layout.lock_file)
        return marked

    monkeypatch.setattr(
        wal,
        "_has_exact_b4_protocol_marker",
        restore_lock_after_classification,
    )
    with pytest.raises(CommitReceiptError, match="binding mismatch"):
        wal.append(layout, record, commit_receipt=receipt)
    assert gate_spy.call_count == 0
    assert Path(layout.wal_file).read_bytes() == b""


def test_markerless_commit_accepts_matching_live_receipt(tmp_path, monkeypatch):
    ordinary = L.default_cfg()
    campaign_id = str(ident.campaign_id(ordinary))
    layout = CampaignLayout(str(tmp_path / campaign_id)).ensure()
    wal.write_lock(layout, ident.canonical_preimage(ordinary))
    gate_spy = mock.Mock(
        side_effect=AssertionError("ordinary COMMIT reached the B-4 gate")
    )
    monkeypatch.setattr(B4L, "verify_b4_launch_context", gate_spy)

    committed = _commit_with_live_receipt(layout)

    assert wal.read_records(layout) == [committed]
    assert gate_spy.call_count == 0


def test_non_b4_commit_without_search_config_accepts_matching_live_receipt(
    tmp_path, monkeypatch,
):
    ordinary = L.default_cfg()
    identity = json.loads(ident.canonical_preimage(ordinary))
    identity.pop("search_config")
    layout = CampaignLayout(str(tmp_path / "non-b4-campaign")).ensure()
    wal.write_lock(
        layout,
        json.dumps(
            identity,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
    )
    gate_spy = mock.Mock(
        side_effect=AssertionError("non-B-4 COMMIT reached the B-4 gate")
    )
    monkeypatch.setattr(B4L, "verify_b4_launch_context", gate_spy)

    committed = _commit_with_live_receipt(layout)

    assert wal.read_records(layout) == [committed]
    assert gate_spy.call_count == 0


@pytest.mark.parametrize("search_config", (None, [], "legacy"))
def test_commit_rejects_non_mapping_search_config(tmp_path, search_config):
    ordinary = L.default_cfg()
    identity = json.loads(ident.canonical_preimage(ordinary))
    identity["search_config"] = search_config
    layout = CampaignLayout(str(tmp_path / "malformed-search-config")).ensure()
    wal.write_lock(
        layout,
        json.dumps(
            identity,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
    )

    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="cannot classify",
    ):
        wal.append(layout, _commit_record())
    assert not Path(layout.wal_file).exists()


@pytest.mark.parametrize(
    "decoded",
    (object(), mock.Mock(identity=[])),
    ids=("missing-identity", "non-dict-identity"),
)
def test_classifier_rejects_malformed_decoded_or_identity(decoded):
    with pytest.raises(
        B4L.B4LauncherAuthorizationError,
        match="cannot classify",
    ):
        wal._has_exact_b4_protocol_marker(decoded)


def test_lockless_commit_accepts_explicit_absence_binding(tmp_path):
    layout = CampaignLayout(str(tmp_path / "lockless-campaign")).ensure()

    committed = _commit_with_live_receipt(layout)

    assert wal.read_records(layout) == [committed]


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


@pytest.mark.parametrize("raw", (
    b"\xff",
    b"[]",
    b'{"search_config":{"b4_protocol":"p3-b4-reflux-ablation/v1"}}',
))
def test_existing_unclassifiable_lock_rejects_commit(tmp_path, raw):
    """F4: unreadable or incomplete existing lock shapes all fail closed."""
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
    """F4: source imports one protocol definition and repeats no literals."""
    protocol_source = Path(B4P.__file__).read_text(encoding="utf-8")
    protocol_literals = {
        node.value
        for node in ast.walk(ast.parse(protocol_source))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert B4P.B4_PROTOCOL_KEY in protocol_literals
    assert B4P.B4_PROTOCOL_VALUE in protocol_literals

    for module in (L, S, T, wal):
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        literals = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        assert B4P.B4_PROTOCOL_KEY not in literals
        assert B4P.B4_PROTOCOL_VALUE not in literals
        protocol_imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.level == 1
            and node.module == "p3_b4_protocol"
            for alias in node.names
        }
        assert {"B4_PROTOCOL_KEY", "B4_PROTOCOL_VALUE"} <= protocol_imports


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
        backoff_hole_grammar.BACKOFF_GRAMMAR_VERSION_KEY,
        "build_admission",
    }
    assert all(value is not context for value in marked.search_config.values())
    assert not hasattr(marked, "b4_launch_context")


def _run():
    return pytest.main([__file__])


if __name__ == "__main__":
    sys.exit(_run())
