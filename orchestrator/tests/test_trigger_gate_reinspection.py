# -*- coding: utf-8 -*-
"""Detached trigger-gate reinspection ledger regression tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ORCHESTRATOR))

from campaign import source_digest, trigger_gate_reinspection as reinspection  # noqa: E402
from campaign.trigger_gate_reinspection import (  # noqa: E402
    ReinspectionError,
    ReinspectionVerdict,
    canonical_record_sha256,
    create_reinspection_ledger,
    load_reinspection_ledger,
    lookup_reinspection_verdict,
    reinspect_record,
)


_VALID = "  izanagi_gate_pass = true;"
_INVALID = "  izanagi_gate_pass = true;\rSECRET_CANARY"


def _record(implementation: str | None) -> dict[str, object]:
    record: dict[str, object] = {"stage": "legacy-terminal", "payload": {}}
    if implementation is not None:
        record["payload"] = {"proposal": {"implementation": implementation}}
    return record


def _bound_record(implementation: str) -> dict[str, object]:
    return {
        "stage": "build_start",
        "payload": {
            "genome": "silo|BACKOFF_TRIGGER_GATING=1",
            "src_token": "a" * 64,
            "proposal": {"implementation": implementation},
        },
    }


def _write_trigger_source(root: Path, implementation: bytes) -> None:
    path = root / source_digest.TRIGGER_GATE_SOURCE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"  // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating\n"
        b"#if BACKOFF_TRIGGER_GATING\n"
        + implementation
        + b"\n#else\n  Backoff::backoff(FLAGS_clocks_per_us);\n#endif\n"
        b"  // EVOLVE-BLOCK-END silo-backoff-trigger-gating\n"
    )


@pytest.mark.parametrize(
    "record, expected",
    [
        pytest.param(_record(_VALID), ReinspectionVerdict.PASSED, id="passed"),
        pytest.param(_record(_INVALID), ReinspectionVerdict.REJECTED, id="rejected"),
        pytest.param(
            _record(None),
            ReinspectionVerdict.SOURCE_UNAVAILABLE,
            id="source-unavailable",
        ),
    ],
)
def test_reinspect_record_has_closed_three_way_classification(record, expected):
    assert reinspect_record(record) is expected


def test_reinspection_uses_provenance_when_actual_source_is_unavailable(tmp_path):
    assert not (tmp_path / "missing-source-root").exists()
    assert reinspect_record(
        _record(_VALID),
    ) is ReinspectionVerdict.PASSED


def test_reinspection_rejects_invalid_actual_source_without_provenance_override(
        tmp_path, monkeypatch):
    _write_trigger_source(tmp_path, _INVALID.encode("ascii"))

    def reject_actual(*args, **kwargs):
        source_digest.inspect_trigger_gate_source(str(tmp_path), required=True)
        raise AssertionError("invalid actual source unexpectedly passed")

    monkeypatch.setattr(reinspection, "resolve_evidence", reject_actual)
    assert reinspect_record(
        _bound_record(_VALID), source_root=str(tmp_path), ccbench_commit="pin",
    ) is ReinspectionVerdict.REJECTED


def test_m15_reinspection_ledger_never_records_rejected_as_passed(tmp_path):
    record = _record(_INVALID)
    digest = canonical_record_sha256(record)
    path = tmp_path / "campaign-reinspection.json"
    ledger = create_reinspection_ledger(
        str(path), campaign_id="legacy-trigger-campaign", records=[record],
    )
    assert ledger["entries"] == {digest: ReinspectionVerdict.REJECTED.value}
    assert ledger["evidence"] == {
        digest: {"kind": "record-provenance", "source_root": None},
    }
    assert lookup_reinspection_verdict(
        ledger, digest,
    ) is ReinspectionVerdict.REJECTED
    assert "SECRET_CANARY" not in path.read_text(encoding="ascii")
    assert "SECRET_CANARY" not in repr(ledger)


def test_reinspection_ledger_is_create_only_and_consumer_verifies_bytes(tmp_path):
    path = tmp_path / "campaign-reinspection.json"
    record = _record(_VALID)
    first = create_reinspection_ledger(
        str(path), campaign_id="legacy-trigger-campaign", records=[record],
    )
    original = path.read_bytes()
    with pytest.raises(ReinspectionError, match="create-only"):
        create_reinspection_ledger(
            str(path), campaign_id="legacy-trigger-campaign", records=[record],
        )
    assert path.read_bytes() == original
    assert load_reinspection_ledger(
        str(path), campaign_id="legacy-trigger-campaign",
    ) == first

    value = json.loads(original.decode("ascii"))
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="ascii")
    with pytest.raises(ReinspectionError, match="canonical"):
        load_reinspection_ledger(str(path))
