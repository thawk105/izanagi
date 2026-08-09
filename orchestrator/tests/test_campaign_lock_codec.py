# -*- coding: utf-8 -*-
"""campaign.lock v1/v2 codec の exact wire contract。"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from orchestrator.campaign import campaign_lock


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


def _authority() -> dict[str, object]:
    return {
        "environment_contract_sha256": "1" * 64,
        "activation_serial": 1,
        "activation_state_sha256": "2" * 64,
        "contract_loader_commit": "3" * 40,
        "contract_loader_blob_sha256s": {
            path: str(index) * 64
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


def test_v1_is_detected_and_original_bytes_are_preserved() -> None:
    raw = json.dumps(_identity(), ensure_ascii=False, indent=2).encode("utf-8")
    decoded = campaign_lock.decode_campaign_lock(raw.decode("utf-8"))
    assert decoded.is_v1
    assert not decoded.is_v2
    assert decoded.authority is None
    assert decoded.identity == _identity()
    assert campaign_lock.preserve_v1_campaign_lock_bytes(raw) is raw


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


@pytest.mark.parametrize("missing", sorted(campaign_lock.V2_KEYS))
def test_v2_rejects_each_missing_top_level_key(missing: str) -> None:
    value = _v2_value()
    del value[missing]
    with pytest.raises(campaign_lock.CampaignLockCodecError):
        campaign_lock.decode_campaign_lock(_canonical(value))


def test_v1_and_v2_reject_extra_or_missing_identity_keys() -> None:
    for identity in (
        {**_identity(), "extra": 1},
        {key: value for key, value in _identity().items() if key != "trial"},
    ):
        with pytest.raises(campaign_lock.CampaignLockCodecError):
            campaign_lock.decode_campaign_lock(_canonical(identity))
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


def _run() -> int:
    """Keep this new test file inside the repository plain-runner contract."""
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
