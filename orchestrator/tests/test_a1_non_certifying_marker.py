# -*- coding: utf-8 -*-
"""A-1 non-certifying identity と WAL marker の閉じた受理集合。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestrator.campaign import campaign_lock, env_contract, ident, wal
from orchestrator.campaign.build_admission import GeneratorId, build_run_context
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.campaign.model import CampaignConfig, WalRecord


_OLD_IDENTITY = (
    "paper-story-a1-paired-campaign/v1",
    "paper-story-a1-20260826-sized-v1",
    "arm-grouped-positional-v1",
)
_PILOT_IDENTITY = (
    "paper-story-a1-paired-campaign/v2",
    "paper-story-a1-20260901-balanced5-pilot-v1",
    "balanced-a5b5-b5a5-v1",
)
_SIZED_IDENTITY = (
    "paper-story-a1-paired-campaign/v2",
    "paper-story-a1-20260901-balanced5-sized-v1",
    "balanced-a5b5-b5a5-v1",
)
_REGISTERED_IDENTITIES = (_OLD_IDENTITY, _PILOT_IDENTITY, _SIZED_IDENTITY)
_CROSS_PRODUCT_IDENTITIES = (
    (
        "paper-story-a1-paired-campaign/v1",
        "paper-story-a1-20260901-balanced5-pilot-v1",
        "balanced-a5b5-b5a5-v1",
    ),
    (
        "paper-story-a1-paired-campaign/v1",
        "paper-story-a1-20260901-balanced5-sized-v1",
        "arm-grouped-positional-v1",
    ),
    (
        "paper-story-a1-paired-campaign/v2",
        "paper-story-a1-20260826-sized-v1",
        "arm-grouped-positional-v1",
    ),
    (
        "paper-story-a1-paired-campaign/v2",
        "paper-story-a1-20260901-balanced5-pilot-v1",
        "arm-grouped-positional-v1",
    ),
    (
        "paper-story-a1-paired-campaign/v2",
        "paper-story-a1-20260901-balanced5-unknown-v1",
        "balanced-a5b5-b5a5-v1",
    ),
    (
        "paper-story-a1-paired-campaign/v3",
        "paper-story-a1-20260901-balanced5-pilot-v1",
        "balanced-a5b5-b5a5-v1",
    ),
)


def _search_config(
        identity: tuple[str, str, str], *, admission: dict | None = None,
) -> dict[str, object]:
    schema, study_id, pairing_design = identity
    search: dict[str, object] = {
        "schema": schema,
        "study_id": study_id,
        "formal": False,
        "promotion_prohibited": True,
        "pairing_design": pairing_design,
        "non_certifying_mode": "registered-formal-non-certifying",
        "workload": {"name": "write-heavy"},
    }
    if admission is not None:
        search[ident.ADMISSION_POLICY_SEARCH_KEY] = admission
    return search


def _config(
        identity: tuple[str, str, str], *, admission: dict | None = None,
        bound_contract=None, trial: str | None = None,
) -> CampaignConfig:
    return CampaignConfig(
        spec_slug="a1-marker",
        search_tag="paired",
        spec_content="A-1 marker fixture",
        ccbench_commit="a" * 40,
        search_config=_search_config(identity, admission=admission),
        trial=identity[1] if trial is None else trial,
        bound_environment_contract=bound_contract,
    )


def _canonical(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def _lock_text(identity: dict[str, object], *, campaign_id: str) -> str:
    study_id = identity["search_config"]["study_id"]
    return campaign_lock.encode_non_certifying_campaign_lock(
        _canonical(identity),
        common_record={
            "mode": "registered-formal-non-certifying",
            "certifying": False,
            "study_id": study_id,
            "policy_sha256": "1" * 64,
            "preregistration_sha256": "2" * 64,
            "source_commit": "3" * 40,
            "source_binding_sha256": "4" * 64,
            "environment_contract_sha256": "5" * 64,
            "intent_sha256": "6" * 64,
            "campaign_ids": [campaign_id, "campaign-b", "campaign-c"],
        },
        workload_binding={
            "workload": "write-heavy",
            "campaign_id": campaign_id,
            "ordinal": 0,
        },
    )


def _marker_layout(
        tmp_path: Path, identity: tuple[str, str, str], *,
        search_overrides: dict[str, object] | None = None,
        trial: str | None = None,
) -> CampaignLayout:
    layout = CampaignLayout(str(tmp_path / "campaign-a")).ensure()
    cfg = _config(identity, trial=trial)
    if search_overrides is not None:
        cfg.search_config.update(search_overrides)
    Path(layout.lock_file).write_text(
        _lock_text(
            {
                "spec_content": cfg.spec_content,
                "ccbench_commit": cfg.ccbench_commit,
                "search_tag": cfg.search_tag,
                "search_config": cfg.search_config,
                "trial": cfg.trial,
            },
            campaign_id="campaign-a",
        ),
        encoding="utf-8",
    )
    return layout


def _interrupted_layout(
        tmp_path: Path, identity: tuple[str, str, str],
) -> tuple[CampaignConfig, CampaignLayout, object]:
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    authorization = env_contract.authorize("linux-baremetal")
    cfg = _config(
        identity,
        admission=dict(context.policy.as_preimage()),
        bound_contract=authorization.contract,
    )
    campaign_id = str(ident.campaign_id(cfg))
    layout = CampaignLayout(str(tmp_path / campaign_id)).ensure()
    common = {
        "mode": "registered-formal-non-certifying",
        "certifying": False,
        "study_id": identity[1],
        "policy_sha256": "1" * 64,
        "preregistration_sha256": "2" * 64,
        "source_commit": "3" * 40,
        "source_binding_sha256": "4" * 64,
        "environment_contract_sha256": authorization.contract.contract_sha256,
        "intent_sha256": "6" * 64,
        "campaign_ids": [campaign_id, "campaign-b", "campaign-c"],
    }
    Path(layout.lock_file).write_text(
        campaign_lock.encode_non_certifying_campaign_lock(
            ident.canonical_preimage(cfg),
            common_record=common,
            workload_binding={
                "workload": "write-heavy",
                "campaign_id": campaign_id,
                "ordinal": 0,
            },
        ),
        encoding="utf-8",
    )
    wal.append_a1_non_certifying(
        layout,
        WalRecord(
            variant="variant-a",
            stage="build_start",
            env_tag=authorization.contract.env_tag,
            ts=1.0,
            payload={"build_attempt_id": "attempt-1"},
        ),
    )
    return cfg, layout, context.policy


@pytest.mark.parametrize(
    "identity", _REGISTERED_IDENTITIES,
    ids=("legacy", "balanced5-pilot", "balanced5-sized"),
)
def test_ident_accepts_each_registered_exact_identity_tuple(
        identity: tuple[str, str, str],
) -> None:
    assert ident.is_a1_non_certifying_config(_config(identity)) is True


@pytest.mark.parametrize(
    "identity", _CROSS_PRODUCT_IDENTITIES,
    ids=(
        "legacy-schema-pilot-study",
        "legacy-schema-new-sized-study",
        "new-schema-legacy-study",
        "new-study-legacy-pairing",
        "unknown-study",
        "unknown-schema",
    ),
)
def test_ident_rejects_unregistered_schema_study_pairing_cross_products(
        identity: tuple[str, str, str],
) -> None:
    assert ident.is_a1_non_certifying_config(_config(identity)) is False


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("formal", True),
        ("promotion_prohibited", False),
        ("non_certifying_mode", "registered-effective"),
    ),
)
def test_ident_marker_gate_rejects_each_forbidden_flag_with_positive_control(
        field: str, replacement: object,
) -> None:
    accepted = _config(_PILOT_IDENTITY)
    assert ident.is_a1_non_certifying_config(accepted) is True
    accepted.search_config[field] = replacement
    assert ident.is_a1_non_certifying_config(accepted) is False


def test_ident_marker_keeps_exact_campaign_config_type_gate() -> None:
    class DerivedCampaignConfig(CampaignConfig):
        pass

    exact = _config(_PILOT_IDENTITY)
    derived = DerivedCampaignConfig(**exact.__dict__)

    assert ident.is_a1_non_certifying_config(exact) is True
    assert ident.is_a1_non_certifying_config(derived) is False


def test_ident_rejects_trial_study_mismatch_with_positive_control() -> None:
    accepted = _config(_PILOT_IDENTITY)
    assert ident.is_a1_non_certifying_config(accepted) is True
    rejected = _config(
        _PILOT_IDENTITY,
        trial="paper-story-a1-20260901-balanced5-sized-v1",
    )
    assert ident.is_a1_non_certifying_config(rejected) is False


@pytest.mark.parametrize(
    "identity", _REGISTERED_IDENTITIES,
    ids=("legacy", "balanced5-pilot", "balanced5-sized"),
)
def test_wal_accepts_each_registered_exact_identity_tuple(
        tmp_path: Path, identity: tuple[str, str, str],
) -> None:
    layout = _marker_layout(tmp_path, identity)
    with wal.a1_non_certifying_io(layout):
        pass


@pytest.mark.parametrize(
    "identity", _CROSS_PRODUCT_IDENTITIES,
    ids=(
        "legacy-schema-pilot-study",
        "legacy-schema-new-sized-study",
        "new-schema-legacy-study",
        "new-study-legacy-pairing",
        "unknown-study",
        "unknown-schema",
    ),
)
def test_wal_rejects_unregistered_schema_study_pairing_cross_products(
        tmp_path: Path, identity: tuple[str, str, str],
) -> None:
    layout = _marker_layout(tmp_path, identity)
    with pytest.raises(wal.AttemptTopologyError, match="marker"):
        with wal.a1_non_certifying_io(layout):
            pass


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("formal", True),
        ("promotion_prohibited", False),
        ("non_certifying_mode", "registered-effective"),
    ),
)
def test_wal_marker_gate_rejects_each_forbidden_flag_with_positive_control(
        tmp_path: Path, field: str, replacement: object,
) -> None:
    accepted = _marker_layout(tmp_path / "accepted", _PILOT_IDENTITY)
    with wal.a1_non_certifying_io(accepted):
        pass

    rejected = _marker_layout(
        tmp_path / "rejected",
        _PILOT_IDENTITY,
        search_overrides={field: replacement},
    )
    with pytest.raises(wal.AttemptTopologyError, match="marker"):
        with wal.a1_non_certifying_io(rejected):
            pass


def test_wal_rejects_trial_study_mismatch_with_positive_control(
        tmp_path: Path,
) -> None:
    accepted = _marker_layout(tmp_path / "accepted", _PILOT_IDENTITY)
    with wal.a1_non_certifying_io(accepted):
        pass

    rejected = _marker_layout(
        tmp_path / "rejected",
        _PILOT_IDENTITY,
        trial="paper-story-a1-20260901-balanced5-sized-v1",
    )
    with pytest.raises(wal.AttemptTopologyError, match="marker"):
        with wal.a1_non_certifying_io(rejected):
            pass


@pytest.mark.parametrize(
    "identity", (_PILOT_IDENTITY, _SIZED_IDENTITY),
    ids=("pilot", "sized"),
)
def test_balanced5_interruption_is_terminal_invalid_after_ident_resume(
        tmp_path: Path, identity: tuple[str, str, str],
) -> None:
    cfg, layout, policy = _interrupted_layout(tmp_path, identity)

    repair = ident.ensure_resumable_wal(
        cfg, layout, admission_policy=policy,
    )
    states = wal.replay_a1_non_certifying(
        layout, admission_policy=policy,
    )
    state = states["variant-a"]

    assert repair.status == "noop"
    assert state.terminal is True
    assert state.retryable_abort is False
    assert state.last_terminal is not None
    assert state.last_terminal.payload == {
        "reason": "a1-balanced5-interrupted-attempt-invalid",
        "build_attempt_id": "attempt-1",
    }


def test_legacy_interruption_remains_retryable_after_ident_resume(
        tmp_path: Path,
) -> None:
    cfg, layout, policy = _interrupted_layout(tmp_path, _OLD_IDENTITY)

    ident.ensure_resumable_wal(cfg, layout, admission_policy=policy)
    states = wal.replay_a1_non_certifying(
        layout, admission_policy=policy,
    )
    state = states["variant-a"]

    assert state.terminal is True
    assert state.retryable_abort is True
    assert state.last_terminal is not None
    assert state.last_terminal.payload["reason"] == (
        "recovery-abort-incomplete-attempt"
    )


def test_terminal_invalid_recovery_gate_rejects_legacy_pairing(
        tmp_path: Path,
) -> None:
    _cfg, layout, policy = _interrupted_layout(tmp_path, _OLD_IDENTITY)
    before = Path(layout.wal_file).read_bytes()

    with pytest.raises(wal.AttemptTopologyError, match="balanced5 marker"):
        wal.recover_interrupted_attempts_a1_balanced5_terminal_invalid(
            layout,
            admission_policy=policy,
        )

    assert Path(layout.wal_file).read_bytes() == before


def test_retryable_recovery_gate_rejects_balanced5_pairing(
        tmp_path: Path,
) -> None:
    _cfg, layout, policy = _interrupted_layout(tmp_path, _PILOT_IDENTITY)
    before = Path(layout.wal_file).read_bytes()

    with pytest.raises(wal.AttemptTopologyError, match="terminal invalid"):
        wal.recover_interrupted_attempts_a1_non_certifying(
            layout,
            admission_policy=policy,
        )

    assert Path(layout.wal_file).read_bytes() == before


def _run() -> int:
    """Keep this marker test file inside the repository plain-runner contract."""
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
