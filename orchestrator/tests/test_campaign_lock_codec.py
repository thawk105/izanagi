# -*- coding: utf-8 -*-
"""campaign.lock v1/v2 codec の exact wire contract。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from orchestrator.campaign import campaign_lock, ident
from orchestrator.campaign.build_admission import GeneratorId, build_run_context



# Independent declaration copied from 2a9ba783f^; never derive from production.
_EXPECTED_T733_EXACT62_CLOSURE_PATHS = (
    "orchestrator/campaign/env_contract.py",
    "orchestrator/campaign/env_contract_activation.py",
    "orchestrator/campaign/execution_guard.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/pipeline.py",
    "orchestrator/campaign/wal.py",
    "orchestrator/campaign/ident.py",
    "orchestrator/campaign/artifact_admission.py",
    "orchestrator/verifier/core.py",
    "orchestrator/verifier/dsg.py",
    "orchestrator/verifier/model.py",
    "orchestrator/verifier/parse.py",
    "orchestrator/verifier/__init__.py",
    "orchestrator/verifier/report.py",
    "orchestrator/campaign/s8c_preregistration.py",
    "orchestrator/campaign/s8c_preregistration_evidence.py",
    "orchestrator/campaign/s8c_generation_projection.py",
    "orchestrator/campaign/campaign_lock.py",
    "orchestrator/campaign/contract_loader_binding.py",
    "orchestrator/campaign/guided.py",
    "orchestrator/campaign/replay.py",
    "orchestrator/qualification/artifacts.py",
    "orchestrator/qualification/t126_driver.py",
    "orchestrator/verifier/commit_receipt.py",
    "orchestrator/calibrator/__init__.py",
    "orchestrator/calibrator/effective_clock_policy.py",
    "orchestrator/calibrator/perf_preflight.py",
    "orchestrator/calibrator/runner.py",
    "orchestrator/calibrator/schema_v2.py",
    "orchestrator/calibrator/stability.py",
    "orchestrator/campaign/__init__.py",
    "orchestrator/campaign/axis_trigger_gating.py",
    "orchestrator/campaign/build_admission.py",
    "orchestrator/campaign/buildcache.py",
    "orchestrator/campaign/calibration_verify.py",
    "orchestrator/campaign/campaign_claim.py",
    "orchestrator/campaign/diff_quarantine.py",
    "orchestrator/campaign/env_attestation.py",
    "orchestrator/campaign/genome.py",
    "orchestrator/campaign/layout.py",
    "orchestrator/campaign/lock.py",
    "orchestrator/campaign/model.py",
    "orchestrator/campaign/p2_2.py",
    "orchestrator/campaign/p3_b4_launcher.py",
    "orchestrator/campaign/p3_b4_protocol.py",
    "orchestrator/campaign/reflux_ir.py",
    "orchestrator/campaign/reservation.py",
    "orchestrator/campaign/search_baselines.py",
    "orchestrator/campaign/site_policy.py",
    "orchestrator/campaign/source_digest.py",
    "orchestrator/campaign/trigger_gate_binding.py",
    "orchestrator/critic/__init__.py",
    "orchestrator/critic/online_digest.py",
    "orchestrator/holdout_observation.py",
    "orchestrator/qualification/__init__.py",
    "orchestrator/qualification/attempt_ledger.py",
    "orchestrator/qualification/collector.py",
    "orchestrator/qualification/contract.py",
    "orchestrator/qualification/identity.py",
    "orchestrator/qualification/qsub_binding.py",
    "orchestrator/qualification/retry_index.py",
    "orchestrator/qualification/series.py",
)

def _identity() -> dict[str, object]:
    return {
        "spec_content": "codec fixture あ",
        "ccbench_commit": "0" * 40,
        "search_tag": "codec",
        "search_config": {"build_admission": {"schema": "fixture"}},
        "trial": None,
    }


def _canonical(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


_EXPECTED_T2429_EXACT63_CLOSURE_PATHS = (
    "orchestrator/campaign/env_contract.py",
    "orchestrator/campaign/env_contract_activation.py",
    "orchestrator/campaign/execution_guard.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/pipeline.py",
    "orchestrator/campaign/wal.py",
    "orchestrator/campaign/ident.py",
    "orchestrator/campaign/artifact_admission.py",
    "orchestrator/verifier/core.py",
    "orchestrator/verifier/dsg.py",
    "orchestrator/verifier/model.py",
    "orchestrator/verifier/parse.py",
    "orchestrator/verifier/__init__.py",
    "orchestrator/verifier/report.py",
    "orchestrator/campaign/s8c_preregistration.py",
    "orchestrator/campaign/s8c_preregistration_evidence.py",
    "orchestrator/campaign/s8c_generation_projection.py",
    "orchestrator/campaign/campaign_lock.py",
    "orchestrator/campaign/contract_loader_binding.py",
    "orchestrator/campaign/guided.py",
    "orchestrator/campaign/replay.py",
    "orchestrator/qualification/artifacts.py",
    "orchestrator/qualification/t126_driver.py",
    "orchestrator/verifier/commit_receipt.py",
    "orchestrator/calibrator/__init__.py",
    "orchestrator/calibrator/effective_clock_policy.py",
    "orchestrator/calibrator/perf_preflight.py",
    "orchestrator/calibrator/runner.py",
    "orchestrator/calibrator/schema_v2.py",
    "orchestrator/calibrator/stability.py",
    "orchestrator/campaign/__init__.py",
    "orchestrator/campaign/axis_trigger_gating.py",
    "orchestrator/campaign/build_admission.py",
    "orchestrator/campaign/buildcache.py",
    "orchestrator/campaign/calibration_verify.py",
    "orchestrator/campaign/campaign_claim.py",
    "orchestrator/campaign/diff_quarantine.py",
    "orchestrator/campaign/env_attestation.py",
    "orchestrator/campaign/genome.py",
    "orchestrator/campaign/layout.py",
    "orchestrator/campaign/lock.py",
    "orchestrator/campaign/model.py",
    "orchestrator/campaign/p2_2.py",
    "orchestrator/campaign/p3_b4_launcher.py",
    "orchestrator/campaign/p3_b4_protocol.py",
    "orchestrator/campaign/reflux_ir.py",
    "orchestrator/campaign/reservation.py",
    "orchestrator/campaign/search_baselines.py",
    "orchestrator/campaign/site_policy.py",
    "orchestrator/campaign/source_digest.py",
    "orchestrator/campaign/trigger_gate_binding.py",
    "orchestrator/critic/__init__.py",
    "orchestrator/critic/online_digest.py",
    "orchestrator/holdout_observation.py",
    "orchestrator/qualification/__init__.py",
    "orchestrator/qualification/attempt_ledger.py",
    "orchestrator/qualification/collector.py",
    "orchestrator/qualification/contract.py",
    "orchestrator/qualification/identity.py",
    "orchestrator/qualification/qsub_binding.py",
    "orchestrator/qualification/retry_index.py",
    "orchestrator/qualification/series.py",
    "orchestrator/campaign/verify_fanout_worker.py",
)

def _authority() -> dict[str, object]:
    return {
        "environment_contract_sha256": "1" * 64,
        "activation_serial": 1,
        "activation_state_sha256": "2" * 64,
        "contract_loader_commit": "3" * 40,
        "contract_loader_blob_sha256s": {
            path: hashlib.sha256(
                f"loader-blob-{index}:{path}".encode("utf-8")
            ).hexdigest()
            for index, path in enumerate(
                campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS, start=4,
            )
        },
    }


def _v2_value() -> dict[str, object]:
    return {
        "schema_version": "campaign-lock/v2",
        "identity_preimage": _canonical(_identity()),
        "authority": _authority(),
    }


def _pre_t733_v2_value() -> dict[str, object]:
    value = _v2_value()
    blobs = value["authority"]["contract_loader_blob_sha256s"]
    value["authority"]["contract_loader_blob_sha256s"] = {
        path: blobs[path]
        for path in campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS
    }
    return value


def _non_certifying_common() -> dict[str, object]:
    return {
        "mode": "registered-formal-non-certifying",
        "certifying": False,
        "study_id": "paper-story-a1-20260826-sized-v1",
        "policy_sha256": "4" * 64,
        "preregistration_sha256": "5" * 64,
        "source_commit": "6" * 40,
        "source_binding_sha256": "7" * 64,
        "environment_contract_sha256": "8" * 64,
        "intent_sha256": "9" * 64,
        "campaign_ids": ["campaign-a", "campaign-b", "campaign-c"],
    }


def _non_certifying_lock() -> str:
    return campaign_lock.encode_non_certifying_campaign_lock(
        _canonical(_identity()),
        common_record=_non_certifying_common(),
        workload_binding={
            "workload": "write-heavy",
            "campaign_id": "campaign-a",
            "ordinal": 0,
        },
    )


def test_v1_is_detected_and_original_bytes_are_preserved() -> None:
    raw = json.dumps(_identity(), ensure_ascii=False, indent=2).encode("utf-8")
    decoded = campaign_lock.decode_campaign_lock(raw.decode("utf-8"))
    assert decoded.is_v1
    assert not decoded.is_v2
    assert decoded.authority is None
    assert decoded.identity == _identity()
    assert campaign_lock.preserve_v1_campaign_lock_bytes(raw) is raw


@pytest.mark.parametrize(
    "value",
    [
        {"search_config": {}},
        {"ccbench_commit": "d706650", "search_config": {"fixture": True}},
    ],
)
def test_partial_v1_objects_are_accepted_by_codec(
        value: dict[str, object],
) -> None:
    text = json.dumps(value)
    decoded = campaign_lock.decode_campaign_lock(text)
    assert decoded.is_v1
    assert decoded.identity == value
    assert decoded.identity_preimage == text


def test_admission_preimage_still_requires_exact_identity_keys() -> None:
    policy = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP).policy
    partial = {
        "ccbench_commit": "d706650",
        "search_config": {
            ident.ADMISSION_POLICY_SEARCH_KEY: dict(policy.as_preimage()),
        },
    }
    with pytest.raises(ident.IdentityMismatch, match="top-level exact key"):
        ident.verify_admission_preimage(policy, _canonical(partial))


def test_v2_exact_shape_and_canonical_encoding() -> None:
    expected = _canonical(_v2_value())
    actual = campaign_lock.encode_campaign_lock_v2(
        _canonical(_identity()), _authority(),
    )
    assert actual == expected
    assert not actual.endswith("\n")
    decoded = campaign_lock.decode_campaign_lock(actual)
    assert decoded.is_v2
    assert decoded.identity_preimage == _canonical(_identity())
    assert decoded.authority is not None
    assert decoded.authority.activation_serial == 1


def test_pre_t733_exact_24_uses_dedicated_historical_decoder_type() -> None:
    text = _canonical(_pre_t733_v2_value())

    decoded = campaign_lock.decode_historical_campaign_lock(text)

    assert type(decoded) is campaign_lock.DecodedHistoricalCampaignLock
    assert not isinstance(decoded, campaign_lock.DecodedCampaignLock)
    assert decoded.authority is not None
    assert (
        decoded.authority.recorded_contract_loader_relative_paths
        == campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS
    )
    assert tuple(decoded.authority.contract_loader_blob_sha256s) == (
        campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS
    )
    with pytest.raises(ident.IdentityMismatch, match="exact v2 campaign.lock"):
        ident.verify_recorded_activation_tuple(decoded)  # type: ignore[arg-type]


def test_pre_t733_exact_24_remains_rejected_by_normal_decoder() -> None:
    text = _canonical(_pre_t733_v2_value())

    with pytest.raises(
        campaign_lock.CampaignLockCodecError,
        match="contract_loader_blob_sha256s の exact key",
    ):
        campaign_lock.decode_campaign_lock(text)


@pytest.mark.parametrize(
    "mutation",
    ["subset", "superset", "same-count-replacement"],
)
def test_historical_decoder_rejects_unknown_blob_map_grammars(
        mutation: str,
) -> None:
    value = _pre_t733_v2_value()
    blobs = value["authority"]["contract_loader_blob_sha256s"]
    if mutation in {"subset", "same-count-replacement"}:
        blobs.pop(campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS[-1])
    if mutation in {"superset", "same-count-replacement"}:
        extra = "orchestrator/campaign/verify_fanout_worker.py"
        assert extra in campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
        assert extra not in campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS
        blobs[extra] = "f" * 64

    with pytest.raises(
        campaign_lock.CampaignLockCodecError,
        match="歴史 grammar",
    ):
        campaign_lock.decode_historical_campaign_lock(_canonical(value))


def test_historical_decoder_rejects_reordered_blob_map_wire_keys() -> None:
    value = json.loads(_canonical(_pre_t733_v2_value()))
    blobs = value["authority"]["contract_loader_blob_sha256s"]
    paths = tuple(blobs)
    reordered = {
        path: blobs[path]
        for path in (paths[1], paths[0], *paths[2:])
    }
    value["authority"]["contract_loader_blob_sha256s"] = reordered
    noncanonical = json.dumps(
        value, sort_keys=False, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )

    with pytest.raises(campaign_lock.CampaignLockCodecError):
        campaign_lock.decode_historical_campaign_lock(noncanonical)


@pytest.mark.parametrize(
    "missing", sorted(campaign_lock.V2_KEYS - {"schema_version"}),
)
def test_v2_rejects_each_missing_top_level_key(missing: str) -> None:
    value = _v2_value()
    del value[missing]
    with pytest.raises(campaign_lock.CampaignLockCodecError):
        campaign_lock.decode_campaign_lock(_canonical(value))


def test_v2_without_schema_version_is_decoded_as_v1() -> None:
    # schema_version 除去は降格攻撃で、拒否は codec でなく admission の anti-downgrade 層が担う。
    value = _v2_value()
    del value["schema_version"]
    text = _canonical(value)

    decoded = campaign_lock.decode_campaign_lock(text)

    assert decoded.is_v1
    assert decoded.identity == value
    assert decoded.identity_preimage == text
    assert decoded.authority is None


def test_v2_rejects_extra_or_missing_identity_keys() -> None:
    # v1 の exact 5 key は codec でなく admission-aware な ident 層が検査する。
    for identity in (
        {**_identity(), "extra": 1},
        {key: value for key, value in _identity().items() if key != "trial"},
    ):
        value = _v2_value()
        value["identity_preimage"] = _canonical(identity)
        with pytest.raises(campaign_lock.CampaignLockCodecError):
            campaign_lock.decode_campaign_lock(_canonical(value))


@pytest.mark.parametrize("missing", sorted(campaign_lock.AUTHORITY_KEYS))
def test_v2_rejects_each_missing_authority_key(missing: str) -> None:
    value = _v2_value()
    del value["authority"][missing]
    with pytest.raises(campaign_lock.CampaignLockCodecError):
        campaign_lock.decode_campaign_lock(_canonical(value))


def test_v2_rejects_extra_authority_and_blob_keys() -> None:
    extra_authority = _v2_value()
    extra_authority["authority"]["extra"] = 1
    extra_blob = _v2_value()
    extra_blob["authority"]["contract_loader_blob_sha256s"]["extra.py"] = "4" * 64
    for value in (extra_authority, extra_blob):
        with pytest.raises(campaign_lock.CampaignLockCodecError):
            campaign_lock.decode_campaign_lock(_canonical(value))


@pytest.mark.parametrize(
    "missing", campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS,
    ids=lambda path: Path(path).name,
)
def test_v2_rejects_each_missing_enforcement_source_blob_key(
        missing: str,
) -> None:
    value = _v2_value()
    del value["authority"]["contract_loader_blob_sha256s"][missing]
    with pytest.raises(
        campaign_lock.CampaignLockCodecError,
        match="contract_loader_blob_sha256s の exact key",
    ):
        campaign_lock.decode_campaign_lock(_canonical(value))


def test_v2_rejects_legacy_exact_two_source_blob_keys() -> None:
    legacy_paths = (
        "orchestrator/campaign/env_contract.py",
        "orchestrator/campaign/env_contract_activation.py",
    )
    value = _v2_value()
    blobs = value["authority"]["contract_loader_blob_sha256s"]
    value["authority"]["contract_loader_blob_sha256s"] = {
        path: blobs[path] for path in legacy_paths
    }
    with pytest.raises(
        campaign_lock.CampaignLockCodecError,
        match="contract_loader_blob_sha256s の exact key",
    ):
        campaign_lock.decode_campaign_lock(_canonical(value))


def test_v2_rejects_pre_wave_exact_twelve_source_blob_keys() -> None:
    pre_wave_paths = (
        "orchestrator/campaign/env_contract.py",
        "orchestrator/campaign/env_contract_activation.py",
        "orchestrator/campaign/execution_guard.py",
        "orchestrator/campaign/loop.py",
        "orchestrator/campaign/pipeline.py",
        "orchestrator/campaign/wal.py",
        "orchestrator/campaign/ident.py",
        "orchestrator/campaign/artifact_admission.py",
        "orchestrator/verifier/core.py",
        "orchestrator/verifier/dsg.py",
        "orchestrator/verifier/model.py",
        "orchestrator/verifier/parse.py",
    )
    value = _v2_value()
    blobs = value["authority"]["contract_loader_blob_sha256s"]
    value["authority"]["contract_loader_blob_sha256s"] = {
        path: blobs[path] for path in pre_wave_paths
    }

    with pytest.raises(
        campaign_lock.CampaignLockCodecError,
        match="contract_loader_blob_sha256s の exact key",
    ):
        campaign_lock.decode_campaign_lock(_canonical(value))


@pytest.mark.parametrize("serial", [True, False, 0, -1, 1.0, "1", None])
def test_v2_rejects_non_positive_or_non_exact_activation_serial(
        serial: object,
) -> None:
    value = _v2_value()
    value["authority"]["activation_serial"] = serial
    with pytest.raises(campaign_lock.CampaignLockCodecError):
        campaign_lock.decode_campaign_lock(_canonical(value))


@pytest.mark.parametrize(
    ("key", "bad"),
    [
        ("environment_contract_sha256", "a" * 63),
        ("environment_contract_sha256", "A" * 64),
        ("activation_state_sha256", "g" * 64),
        ("contract_loader_commit", "a" * 39),
        ("contract_loader_commit", "A" * 40),
    ],
)
def test_v2_rejects_invalid_hash_and_commit_shapes(key: str, bad: str) -> None:
    value = _v2_value()
    value["authority"][key] = bad
    with pytest.raises(campaign_lock.CampaignLockCodecError):
        campaign_lock.decode_campaign_lock(_canonical(value))


@pytest.mark.parametrize("bad", ["a" * 63, "A" * 64, "g" * 64, 4, None])
def test_v2_rejects_invalid_loader_blob_hash_shapes(bad: object) -> None:
    value = _v2_value()
    first = campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS[0]
    value["authority"]["contract_loader_blob_sha256s"][first] = bad
    with pytest.raises(campaign_lock.CampaignLockCodecError):
        campaign_lock.decode_campaign_lock(_canonical(value))


def test_duplicate_keys_are_rejected_at_outer_inner_and_nested_levels() -> None:
    valid = _canonical(_v2_value())
    duplicate_outer = valid[:-1] + ',"schema_version":"campaign-lock/v2"}'
    inner = _canonical(_identity())
    duplicate_inner = inner[:-1] + ',"trial":null}'
    inner_value = _v2_value()
    inner_value["identity_preimage"] = duplicate_inner
    duplicate_nested = valid.replace(
        '"activation_serial":1', '"activation_serial":1,"activation_serial":1',
    )
    for text in (duplicate_outer, _canonical(inner_value), duplicate_nested):
        with pytest.raises(campaign_lock.CampaignLockCodecError):
            campaign_lock.decode_campaign_lock(text)


def test_non_finite_json_is_rejected() -> None:
    v1 = _canonical(_identity()).replace('"trial":null', '"trial":NaN')
    outer = _canonical(_v2_value()).replace('"activation_serial":1', '"activation_serial":NaN')
    for text in (v1, outer):
        with pytest.raises(campaign_lock.CampaignLockCodecError):
            campaign_lock.decode_campaign_lock(text)


def test_broken_v2_never_falls_back_to_v1() -> None:
    attack = {
        **_identity(),
        "schema_version": "campaign-lock/v2",
    }
    with pytest.raises(campaign_lock.CampaignLockCodecError):
        campaign_lock.decode_campaign_lock(_canonical(attack))


def test_v2_requires_canonical_inner_and_outer_text() -> None:
    pretty_inner = json.dumps(_identity(), ensure_ascii=False, indent=2)
    noncanonical_inner = _v2_value()
    noncanonical_inner["identity_preimage"] = pretty_inner
    pretty_outer = json.dumps(_v2_value(), ensure_ascii=False, indent=2)
    for text in (_canonical(noncanonical_inner), pretty_outer, _canonical(_v2_value()) + "\n"):
        with pytest.raises(campaign_lock.CampaignLockCodecError):
            campaign_lock.decode_campaign_lock(text)


def test_campaign_lock_can_be_the_first_campaign_module_imported() -> None:
    repo = Path(__file__).resolve().parents[2]
    code = (
        "import sys; "
        "import orchestrator.campaign.campaign_lock; "
        "mods=[m for m in sys.modules if m.startswith('orchestrator.campaign.')]; "
        "assert mods == ['orchestrator.campaign.campaign_lock'], mods"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=repo,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        check=False, timeout=15,
    )
    assert completed.returncode == 0, completed.stderr


def test_non_certifying_lock_uses_dedicated_decoder_and_disclosed_tag() -> None:
    text = _non_certifying_lock()
    decoded = campaign_lock.decode_non_certifying_campaign_lock(text)
    assert decoded.schema_version == "campaign-lock/non-certifying/v1"
    assert decoded.common_record == _non_certifying_common()
    assert decoded.workload_binding == {
        "workload": "write-heavy",
        "campaign_id": "campaign-a",
        "ordinal": 0,
    }
    assert len(decoded.identity_tag) == 64
    with pytest.raises(campaign_lock.CampaignLockCodecError):
        campaign_lock.decode_campaign_lock(text)


def test_m_nc02_retag_and_schema_removal_are_rejected_by_both_decoders() -> None:
    value = json.loads(_non_certifying_lock())
    retagged = dict(value)
    retagged["schema_version"] = "campaign-lock/v2"
    schema_removed = dict(value)
    schema_removed.pop("schema_version")
    for candidate in (retagged, schema_removed):
        text = _canonical(candidate)
        with pytest.raises(campaign_lock.CampaignLockCodecError):
            campaign_lock.decode_campaign_lock(text)
        with pytest.raises(campaign_lock.CampaignLockCodecError):
            campaign_lock.decode_non_certifying_campaign_lock(text)


def test_m_nc03_non_certifying_lock_tag_tamper_is_rejected() -> None:
    value = json.loads(_non_certifying_lock())
    tag = value["a1_non_certifying"]["identity_tag"]
    value["a1_non_certifying"]["identity_tag"] = (
        ("0" if tag[0] != "0" else "1") + tag[1:]
    )
    with pytest.raises(
        campaign_lock.CampaignLockCodecError, match="tag mismatch",
    ):
        campaign_lock.decode_non_certifying_campaign_lock(_canonical(value))


def test_m_nc04_non_certifying_common_and_workload_fields_are_exact() -> None:
    for mutation in ("common-missing", "workload-replaced"):
        value = json.loads(_non_certifying_lock())
        if mutation == "common-missing":
            value["a1_non_certifying"]["common_record"].pop("policy_sha256")
        else:
            value["a1_non_certifying"]["workload_binding"]["campaign_id"] = (
                "campaign-b"
            )
        with pytest.raises(campaign_lock.CampaignLockCodecError):
            campaign_lock.decode_non_certifying_campaign_lock(_canonical(value))


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("mode", "registered-effective"),
        ("certifying", True),
    ],
)
def test_non_certifying_mode_and_certifying_false_are_load_bearing(
    field: str, replacement: object,
) -> None:
    value = json.loads(_non_certifying_lock())
    value["a1_non_certifying"]["common_record"][field] = replacement
    with pytest.raises(campaign_lock.CampaignLockCodecError):
        campaign_lock.decode_non_certifying_campaign_lock(_canonical(value))


def _t733_exact62_v2_value() -> dict[str, object]:
    value = _v2_value()
    blobs = value["authority"]["contract_loader_blob_sha256s"]
    value["authority"]["contract_loader_blob_sha256s"] = {
        path: blobs[path] for path in _EXPECTED_T733_EXACT62_CLOSURE_PATHS
    }
    return value


def test_t733_exact62_uses_dedicated_historical_decoder_type() -> None:
    text = _canonical(_t733_exact62_v2_value())
    for decoded in (
        campaign_lock.decode_historical_campaign_lock(text),
        campaign_lock.decode_historical_campaign_lock_bytes(text.encode("utf-8")),
    ):
        assert type(decoded) is campaign_lock.DecodedHistoricalCampaignLock
        assert not isinstance(decoded, campaign_lock.DecodedCampaignLock)
        assert decoded.original_text == text
        assert decoded.identity == _identity()
        assert type(decoded.authority) is campaign_lock.HistoricalCampaignLockAuthority
        assert decoded.authority.recorded_contract_loader_relative_paths == (
            _EXPECTED_T733_EXACT62_CLOSURE_PATHS
        )
        assert tuple(decoded.authority.contract_loader_blob_sha256s) == (
            _EXPECTED_T733_EXACT62_CLOSURE_PATHS
        )
        with pytest.raises(ident.IdentityMismatch, match="exact v2 campaign.lock"):
            ident.verify_recorded_activation_tuple(decoded)


def test_t733_exact62_remains_rejected_by_normal_decoder() -> None:
    text = _canonical(_t733_exact62_v2_value())
    with pytest.raises(
        campaign_lock.CampaignLockCodecError,
        match="contract_loader_blob_sha256s の exact key",
    ):
        campaign_lock.decode_campaign_lock(text)
    with pytest.raises(campaign_lock.CampaignLockCodecError):
        campaign_lock.decode_campaign_lock_bytes(text.encode("utf-8"))


@pytest.mark.parametrize(
    "mutation", ["subset", "superset", "same-count-replacement", "order"],
)
def test_t733_exact62_rejects_unknown_grammars(mutation: str) -> None:
    value = json.loads(_canonical(_t733_exact62_v2_value()))
    blobs = value["authority"]["contract_loader_blob_sha256s"]
    if mutation in {"subset", "same-count-replacement"}:
        blobs.pop(_EXPECTED_T733_EXACT62_CLOSURE_PATHS[-1])
    if mutation in {"superset", "same-count-replacement"}:
        extra = "orchestrator/campaign/unknown_t2483.py"
        assert extra not in campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
        blobs[extra] = "f" * 64
    if mutation == "order":
        paths = tuple(blobs)
        value["authority"]["contract_loader_blob_sha256s"] = {
            p: blobs[p] for p in (paths[1], paths[0], *paths[2:])
        }
        text = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    else:
        text = _canonical(value)
    # Wire order is checked independently of outer canonical JSON.
    with pytest.raises(campaign_lock.CampaignLockCodecError, match="歴史 grammar"):
        campaign_lock._validate_t733_exact62_historical_authority(
            json.loads(text)["authority"],
        )
    with pytest.raises(campaign_lock.CampaignLockCodecError, match="歴史 grammar"):
        campaign_lock.decode_historical_campaign_lock(text)


def test_t733_exact62_authority_requires_exact_declared_order() -> None:
    from dataclasses import replace

    wire = json.loads(_canonical(_t733_exact62_v2_value()))["authority"]
    authority = campaign_lock._validate_t733_exact62_historical_authority(wire)
    paths = _EXPECTED_T733_EXACT62_CLOSURE_PATHS
    assert campaign_lock.HistoricalCampaignLockAuthority(
        **_t733_exact62_v2_value()["authority"],
        recorded_contract_loader_relative_paths=paths,
    ) == authority
    swapped = (paths[1], paths[0], *paths[2:])
    for grammar in (
        paths[:-1], (*paths, "orchestrator/campaign/unknown_t2483.py"),
        (*paths[:-1], "orchestrator/campaign/unknown_t2483.py"), swapped,
    ):
        with pytest.raises(TypeError, match="記録 grammar"):
            replace(authority, recorded_contract_loader_relative_paths=grammar,
                    contract_loader_blob_sha256s={p: "a" * 64 for p in grammar})
    with pytest.raises(TypeError, match="blob map 順序"):
        replace(authority, contract_loader_blob_sha256s={
            p: authority.contract_loader_blob_sha256s[p] for p in swapped
        })
    for key in campaign_lock.AUTHORITY_KEYS:
        malformed = dict(wire)
        del malformed[key]
        with pytest.raises(campaign_lock.CampaignLockCodecError, match="exact key"):
            campaign_lock._validate_t733_exact62_historical_authority(malformed)
    with pytest.raises(campaign_lock.CampaignLockCodecError, match="exact key"):
        campaign_lock._validate_t733_exact62_historical_authority({**wire, "extra": 1})
    for serial in (True, False, 0, -1, 1.0, "1", None):
        with pytest.raises(campaign_lock.CampaignLockCodecError, match="正の exact int"):
            campaign_lock._validate_t733_exact62_historical_authority(
                {**wire, "activation_serial": serial},
            )
    for path in paths:
        for bad in ("a" * 63, "A" * 64, "g" * 64, 4, None):
            blobs = dict(wire["contract_loader_blob_sha256s"])
            blobs[path] = bad
            with pytest.raises(campaign_lock.CampaignLockCodecError):
                campaign_lock._validate_t733_exact62_historical_authority(
                    {**wire, "contract_loader_blob_sha256s": blobs},
                )


def _t2429_exact63_v2_value() -> dict[str, object]:
    value = _v2_value()
    blobs = value["authority"]["contract_loader_blob_sha256s"]
    value["authority"]["contract_loader_blob_sha256s"] = {
        path: blobs[path] for path in _EXPECTED_T2429_EXACT63_CLOSURE_PATHS
    }
    return value


def test_t2429_exact63_uses_dedicated_historical_decoder_type() -> None:
    text = _canonical(_t2429_exact63_v2_value())
    for decoded in (
        campaign_lock.decode_historical_campaign_lock(text),
        campaign_lock.decode_historical_campaign_lock_bytes(text.encode("utf-8")),
    ):
        assert type(decoded) is campaign_lock.DecodedHistoricalCampaignLock
        assert not isinstance(decoded, campaign_lock.DecodedCampaignLock)
        assert decoded.original_text == text
        assert decoded.identity == _identity()
        assert type(decoded.authority) is campaign_lock.HistoricalCampaignLockAuthority
        assert decoded.authority.recorded_contract_loader_relative_paths == (
            _EXPECTED_T2429_EXACT63_CLOSURE_PATHS
        )
        assert tuple(decoded.authority.contract_loader_blob_sha256s) == (
            _EXPECTED_T2429_EXACT63_CLOSURE_PATHS
        )
        with pytest.raises(ident.IdentityMismatch, match="exact v2 campaign.lock"):
            ident.verify_recorded_activation_tuple(decoded)


def test_t2429_exact63_remains_rejected_by_normal_decoder() -> None:
    text = _canonical(_t2429_exact63_v2_value())
    with pytest.raises(
        campaign_lock.CampaignLockCodecError,
        match="contract_loader_blob_sha256s の exact key",
    ):
        campaign_lock.decode_campaign_lock(text)
    with pytest.raises(campaign_lock.CampaignLockCodecError):
        campaign_lock.decode_campaign_lock_bytes(text.encode("utf-8"))


@pytest.mark.parametrize(
    "mutation", ["subset", "superset", "same-count-replacement", "order", "current-minus-one"],
)
def test_t2429_exact63_rejects_unknown_grammars(mutation: str) -> None:
    value = json.loads(_canonical(_t2429_exact63_v2_value()))
    blobs = value["authority"]["contract_loader_blob_sha256s"]
    if mutation in {"subset", "same-count-replacement"}:
        blobs.pop("orchestrator/campaign/env_contract.py")
    if mutation in {"superset", "same-count-replacement"}:
        extra = "orchestrator/campaign/unknown_t2344.py"
        assert extra not in campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
        blobs[extra] = "f" * 64
    if mutation == "order":
        paths = tuple(blobs)
        value["authority"]["contract_loader_blob_sha256s"] = {
            p: blobs[p] for p in (paths[1], paths[0], *paths[2:])
        }
        text = json.dumps(value, sort_keys=False, separators=(",", ":"), ensure_ascii=False)
    else:
        text = _canonical(value)
    if mutation == "current-minus-one":
        value = _v2_value()
        value["authority"]["contract_loader_blob_sha256s"].pop(
            "orchestrator/campaign/env_contract.py"
        )
        text = _canonical(value)
    wire_paths = tuple(json.loads(text)["authority"]["contract_loader_blob_sha256s"])
    for known in (
        campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS,
        _EXPECTED_T2429_EXACT63_CLOSURE_PATHS,
        _EXPECTED_T733_EXACT62_CLOSURE_PATHS,
        campaign_lock.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS,
    ):
        assert wire_paths != tuple(sorted(known))
    # Wire order is checked independently of outer canonical JSON.
    with pytest.raises(campaign_lock.CampaignLockCodecError, match="歴史 grammar"):
        campaign_lock._validate_t2429_exact63_historical_authority(
            json.loads(text)["authority"],
        )
    with pytest.raises(campaign_lock.CampaignLockCodecError, match="歴史 grammar"):
        campaign_lock.decode_historical_campaign_lock(text)


def test_t2429_exact63_authority_requires_exact_declared_order() -> None:
    from dataclasses import replace

    wire = json.loads(_canonical(_t2429_exact63_v2_value()))["authority"]
    authority = campaign_lock._validate_t2429_exact63_historical_authority(wire)
    paths = _EXPECTED_T2429_EXACT63_CLOSURE_PATHS
    assert campaign_lock.HistoricalCampaignLockAuthority(
        **_t2429_exact63_v2_value()["authority"],
        recorded_contract_loader_relative_paths=paths,
    ) == authority
    swapped = (paths[1], paths[0], *paths[2:])
    for grammar in (
        paths[1:], (*paths, "orchestrator/campaign/unknown_t2344.py"),
        (*paths[1:], "orchestrator/campaign/unknown_t2344.py"), swapped,
    ):
        with pytest.raises(TypeError, match="記録 grammar"):
            replace(authority, recorded_contract_loader_relative_paths=grammar,
                    contract_loader_blob_sha256s={p: "a" * 64 for p in grammar})
    with pytest.raises(TypeError, match="blob map 順序"):
        replace(authority, contract_loader_blob_sha256s={
            p: authority.contract_loader_blob_sha256s[p] for p in swapped
        })
    for key in campaign_lock.AUTHORITY_KEYS:
        malformed = dict(wire)
        del malformed[key]
        with pytest.raises(campaign_lock.CampaignLockCodecError, match="exact key"):
            campaign_lock._validate_t2429_exact63_historical_authority(malformed)
    with pytest.raises(campaign_lock.CampaignLockCodecError, match="exact key"):
        campaign_lock._validate_t2429_exact63_historical_authority({**wire, "extra": 1})
    for serial in (True, False, 0, -1, 1.0, "1", None):
        with pytest.raises(campaign_lock.CampaignLockCodecError, match="正の exact int"):
            campaign_lock._validate_t2429_exact63_historical_authority(
                {**wire, "activation_serial": serial},
            )
    for path in paths:
        for bad in ("a" * 63, "A" * 64, "g" * 64, 4, None):
            blobs = dict(wire["contract_loader_blob_sha256s"])
            blobs[path] = bad
            with pytest.raises(campaign_lock.CampaignLockCodecError):
                campaign_lock._validate_t2429_exact63_historical_authority(
                    {**wire, "contract_loader_blob_sha256s": blobs},
                )


def _run() -> int:
    """Keep this new test file inside the repository plain-runner contract."""
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
