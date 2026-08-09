# -*- coding: utf-8 -*-
"""campaign.lock v1/v2 を読む WAL・qualification consumer の回帰検査。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
if str(_ORCHESTRATOR) not in sys.path:
    sys.path.insert(0, str(_ORCHESTRATOR))

from orchestrator.campaign import campaign_lock, env_contract, wal
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.campaign.model import (
    COMMIT_CONTRACT_SHA256_KEY,
    STAGE_COMMIT,
)
from orchestrator.qualification.artifacts import select_source_pair
from orchestrator.tests.campaign_lock_test_support import build_v2_campaign_lock


_LEGACY_CONTRACT_KEY = "environment_contract_sha256"
_CCBENCH_COMMIT = "c" * 40


def _identity(*, search_config: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "spec_content": "wal consumer fixture",
        "ccbench_commit": _CCBENCH_COMMIT,
        "search_tag": "consumer",
        "search_config": search_config or {},
        "trial": None,
    }


def _identity_preimage(
        *, search_config: dict[str, object] | None = None,
) -> str:
    return campaign_lock.canonical_json(_identity(search_config=search_config))


def _layout(tmp_path: Path, name: str) -> CampaignLayout:
    return CampaignLayout(root=str(tmp_path / name)).ensure()


def _write_commit(
        layout: CampaignLayout, *, env_tag: str, payload: dict[str, object],
) -> None:
    wal.log(layout, "variant", STAGE_COMMIT, env_tag, payload)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({}, "exact lowercase"),
        ({COMMIT_CONTRACT_SHA256_KEY: "0" * 64}, "campaign.lock と不一致"),
    ],
)
def test_v1_lock_with_contract_h_rejects_unbound_commit(
        tmp_path: Path, payload: dict[str, object], message: str,
) -> None:
    """A-04: v1+H を legacy exemption へ広げる変異を単独で検出する。"""
    authorization = env_contract.authorize("linux-baremetal")
    layout = _layout(tmp_path, "v1-bound")
    wal.write_lock(layout, _identity_preimage(search_config={
        _LEGACY_CONTRACT_KEY: authorization.contract.contract_sha256,
    }))
    _write_commit(
        layout, env_tag=authorization.contract.env_tag, payload=payload,
    )

    with pytest.raises(wal.AttemptTopologyError, match=message):
        wal.replay(layout)


def test_v1_lock_without_contract_h_keeps_legacy_exemption(tmp_path: Path) -> None:
    layout = _layout(tmp_path, "v1-unbound")
    wal.write_lock(layout, _identity_preimage())
    _write_commit(layout, env_tag="historical-env", payload={"fitness_tps": 1.0})

    assert wal.replay(layout)["variant"].committed is True


def test_v2_lock_accepts_commit_matching_authority(tmp_path: Path) -> None:
    authorization = env_contract.authorize("linux-baremetal")
    layout = _layout(tmp_path, "v2-match")
    wal.write_lock(
        layout,
        build_v2_campaign_lock(
            _identity_preimage(), authorization=authorization,
        ),
    )
    _write_commit(
        layout,
        env_tag=authorization.contract.env_tag,
        payload={
            COMMIT_CONTRACT_SHA256_KEY: authorization.contract.contract_sha256,
        },
    )

    assert wal.records_by_stage(layout, "variant")[STAGE_COMMIT] == {
        COMMIT_CONTRACT_SHA256_KEY: authorization.contract.contract_sha256,
    }


def test_v2_lock_rejects_commit_not_matching_authority(tmp_path: Path) -> None:
    authorization = env_contract.authorize("linux-baremetal")
    layout = _layout(tmp_path, "v2-mismatch")
    wal.write_lock(
        layout,
        build_v2_campaign_lock(
            _identity_preimage(), authorization=authorization,
        ),
    )
    _write_commit(
        layout,
        env_tag=authorization.contract.env_tag,
        payload={COMMIT_CONTRACT_SHA256_KEY: "0" * 64},
    )

    with pytest.raises(wal.AttemptTopologyError, match="campaign.lock と不一致"):
        wal.replay(layout)


def test_v2_lock_rejects_commit_env_tag_not_matching_contract(tmp_path: Path) -> None:
    authorization = env_contract.authorize("linux-baremetal")
    layout = _layout(tmp_path, "v2-env-mismatch")
    wal.write_lock(
        layout,
        build_v2_campaign_lock(
            _identity_preimage(), authorization=authorization,
        ),
    )
    _write_commit(
        layout,
        env_tag="pegasus",
        payload={
            COMMIT_CONTRACT_SHA256_KEY: authorization.contract.contract_sha256,
        },
    )

    with pytest.raises(wal.AttemptTopologyError, match="env_tag"):
        wal.records_by_stage(layout, "variant")


@pytest.mark.parametrize(
    "lock_text",
    [
        "{}",
        campaign_lock.canonical_json({
            "schema_version": "campaign-lock/v3",
            "identity_preimage": _identity_preimage(),
            "authority": {},
        }),
    ],
)
def test_wal_reader_wraps_malformed_or_unknown_lock_schema(
        tmp_path: Path, lock_text: str,
) -> None:
    layout = _layout(tmp_path, "invalid-lock")
    wal.write_lock(layout, lock_text)

    with pytest.raises(wal.AttemptTopologyError, match="v1/v2 wire contract"):
        wal.replay(layout)


@pytest.mark.parametrize("schema", ["v1", "v2"])
def test_replay_reads_admission_policy_from_inner_identity(
        tmp_path: Path, schema: str,
) -> None:
    identity_preimage = _identity_preimage(search_config={
        "build_admission": {"schema": "fixture"},
    })
    lock_text = (
        identity_preimage
        if schema == "v1"
        else build_v2_campaign_lock(identity_preimage)
    )
    layout = _layout(tmp_path, f"{schema}-admission-policy")
    wal.write_lock(layout, lock_text)

    with pytest.raises(wal.AttemptTopologyError, match="admission_policy"):
        wal.replay(layout)


def test_trigger_lock_classification_reads_v1_and_v2_inner_identity() -> None:
    search_config = {
        "axis": wal.TRIGGER_AXIS,
        wal.TRIGGER_BINDING_SCHEMA_MARKER_KEY: "fixture-schema",
    }
    identity_preimage = _identity_preimage(search_config=search_config)
    authorization = env_contract.authorize("linux-baremetal")
    decoded_locks = (
        campaign_lock.decode_campaign_lock(identity_preimage),
        campaign_lock.decode_campaign_lock(build_v2_campaign_lock(
            identity_preimage, authorization=authorization,
        )),
    )

    assert all(wal.is_trigger_proposal_campaign_lock(lock) for lock in decoded_locks)


def _source_records() -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    records: list[dict[str, object]] = []
    members: dict[str, dict[str, object]] = {}
    for index, role in enumerate(("subject", "reference"), start=1):
        variant = f"{role}-variant"
        genome = f"silo|BACK_OFF={index}"
        median = float(110 - index * 10)
        members[role] = {
            "source_wal_variant": variant,
            "genome": genome,
            "historical_median_tps": median,
        }
        stage_payloads = (
            ("build_start", {"genome": genome}),
            ("build_done", {}),
            ("verify_done", {
                "certified": True, "anomalies": 0, "commits": 10,
            }),
            ("bench_done", {
                "tps": [median] * 5,
                "median_tps": median,
                "unstable": False,
            }),
            ("commit", {"fitness_tps": median}),
        )
        records.extend({
            "variant": variant,
            "stage": stage,
            "env_tag": "linux-baremetal",
            "ts": float(index),
            "payload": payload,
        } for stage, payload in stage_payloads)
    return records, members


@pytest.mark.parametrize("schema", ["v1", "v2"])
def test_qualification_source_pair_reads_ccbench_commit_from_inner_identity(
        tmp_path: Path, schema: str,
) -> None:
    identity_preimage = _identity_preimage()
    lock_text = (
        identity_preimage
        if schema == "v1"
        else build_v2_campaign_lock(identity_preimage)
    )
    records, members = _source_records()
    lock_path = tmp_path / "campaign.lock"
    wal_path = tmp_path / "wal.jsonl"
    lock_bytes = lock_text.encode("utf-8")
    wal_bytes = b"".join(
        campaign_lock.canonical_json(record).encode("utf-8") + b"\n"
        for record in records
    )
    lock_path.write_bytes(lock_bytes)
    wal_path.write_bytes(wal_bytes)
    required_stage_order = [
        "build_start", "build_done", "verify_done", "bench_done", "commit",
    ]
    protocol = {"source": {
        "campaign_lock_path": lock_path.name,
        "campaign_lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "wal_path": wal_path.name,
        "wal_sha256": hashlib.sha256(wal_bytes).hexdigest(),
        "historical_ccbench_commit": _CCBENCH_COMMIT,
        "required_stage_order": required_stage_order,
        "members": members,
    }}

    assert select_source_pair(tmp_path, protocol) == {
        "lock": _identity(),
        "members": members,
    }


def _run() -> int:
    """Keep this new file inside the repository plain-runner contract."""
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
