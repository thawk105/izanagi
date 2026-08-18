# -*- coding: utf-8 -*-
"""Explicit post-policy receipt helpers, separate from legacy raw WAL fixtures."""
from __future__ import annotations

import json
from pathlib import Path

from orchestrator.campaign import wal
from orchestrator.campaign.model import STAGE_COMMIT, WalRecord
from orchestrator.verifier import (
    CAMPAIGN_WAL_SINK,
    RECEIPT_PAYLOAD_KEY,
    admit_replay_evidence,
    campaign_lock_sha256,
    issue_commit_receipt,
    validate_live_receipt,
    verify_trace_dir_with_capability,
)


_FIXTURE = Path(__file__).resolve().parent / "fixtures/g1_serial"


def verification_capabilities(tags=("legacy",)):
    results = [verify_trace_dir_with_capability(str(_FIXTURE)) for _ in tags]
    assert all(result.certified for result, _capability in results)
    return [capability for _result, capability in results]


def campaign_receipt(
        layout, variant: str, payload: dict, *, operation_identity: str = "test-op",
        tags=("legacy",)):
    return issue_commit_receipt(
        verification_capabilities(tags),
        workload_tags=list(tags),
        sink_kind=CAMPAIGN_WAL_SINK,
        lock_identity_sha256=campaign_lock_sha256(layout),
        variant=variant,
        operation_identity=operation_identity,
        terminal_payload=payload,
    )


def log_receipted_commit(
        layout, variant: str, env_tag: str, payload: dict, *,
        operation_identity: str = "test-op", tags=("legacy",),
):
    receipt = campaign_receipt(
        layout, variant, payload,
        operation_identity=operation_identity,
        tags=tags,
    )
    return wal.log(
        layout, variant, STAGE_COMMIT, env_tag, payload,
        commit_receipt=receipt,
    )


def replay_evidence(
        *, source_variant: str, source_payload: dict,
        source_lock_sha256: str = "a" * 64,
        source_wal_sha256: str = "b" * 64,
):
    receipt = issue_commit_receipt(
        verification_capabilities(),
        workload_tags=["legacy"],
        sink_kind=CAMPAIGN_WAL_SINK,
        lock_identity_sha256=source_lock_sha256,
        variant=source_variant,
        operation_identity="source-test-op",
        terminal_payload=source_payload,
    )
    serialized = validate_live_receipt(
        receipt,
        sink_kind=CAMPAIGN_WAL_SINK,
        lock_identity_sha256=source_lock_sha256,
        variant=source_variant,
        terminal_payload=source_payload,
    )
    return admit_replay_evidence(
        serialized,
        source_campaign_lock_sha256=source_lock_sha256,
        source_wal_sha256=source_wal_sha256,
        source_variant=source_variant,
        source_terminal_payload=source_payload,
    )


def append_legacy_raw_commit(
        layout, variant: str, env_tag: str, payload: dict, *, ts: float = 1.0,
) -> bytes:
    """Write historical bytes without calling the post-policy production sink."""
    record = WalRecord(
        variant=variant, stage=STAGE_COMMIT, env_tag=env_tag, ts=ts,
        payload=payload,
    )
    line = wal._record_to_line(record).encode("utf-8") + b"\n"
    Path(layout.runs_dir).mkdir(parents=True, exist_ok=True)
    with open(layout.wal_file, "ab") as stream:
        stream.write(line)
    return line


def serialized_receipt_from_record(record: WalRecord) -> dict:
    return json.loads(json.dumps(record.payload[RECEIPT_PAYLOAD_KEY]))
