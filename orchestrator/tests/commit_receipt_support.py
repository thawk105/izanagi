# -*- coding: utf-8 -*-
"""Explicit post-policy receipt helpers, separate from legacy raw WAL fixtures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
from types import MappingProxyType

from orchestrator.campaign import artifact_admission, wal
from orchestrator.campaign.build_admission import (
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.model import Genome, STAGE_COMMIT, WalRecord
from orchestrator.campaign.pin import CURRENT_PIN
from orchestrator.campaign.source_digest import (
    EMPTY_TRACKED_DIFF_SHA256,
    SOURCE_EVIDENCE_SCHEMA,
    SourceEvidence,
)
from orchestrator.verifier import (
    CAMPAIGN_WAL_SINK,
    QUALIFICATION_SINK,
    RECEIPT_PAYLOAD_KEY,
    admit_replay_evidence,
    issue_commit_receipt,
    validate_live_receipt,
    verify_trace_dir_with_capability,
)
from orchestrator.verifier.commit_receipt import (
    campaign_lock_sha256_or_absent,
)
from orchestrator.verifier.model import capture_compiled_protocol_source_snapshot


_FIXTURE = Path(__file__).resolve().parent / "fixtures/g1_serial"
_PROOF_SOURCE_TMP = tempfile.TemporaryDirectory(
    prefix="izanagi-proof-source-fixture-",
)
_CCBENCH_ROOT = Path(_PROOF_SOURCE_TMP.name)
_SILO_SOURCE = _CCBENCH_ROOT / "cc/silo"
_SILO_SOURCE.mkdir(parents=True)
(_SILO_SOURCE / "CMakeLists.txt").write_text(
    "ccbench_add_protocol(silo SOURCES transaction.cc WORKLOADS ycsb)\n",
    encoding="utf-8",
)
(_SILO_SOURCE / "transaction.cc").write_text(
    "#if TRACE\n"
    "izanagi_trace::emit_lock_violation(0, 0, {}, {});\n"
    "izanagi_trace::stream(0) << \"P \";\n"
    "#endif\n",
    encoding="utf-8",
)
_MOCC_SOURCE = _CCBENCH_ROOT / "cc/mocc"
_MOCC_SOURCE.mkdir(parents=True)
(_MOCC_SOURCE / "CMakeLists.txt").write_text(
    "ccbench_add_protocol(mocc SOURCES transaction.cc WORKLOADS ycsb)\n",
    encoding="utf-8",
)
(_MOCC_SOURCE / "transaction.cc").write_text(
    "#if TRACE\nizanagi_trace::emit_write(0, 0, {}, {}, 0, 0);\n#endif\n",
    encoding="utf-8",
)


def proof_source_root() -> Path:
    return _CCBENCH_ROOT


_PROOF_GENOME = Genome("silo", {})
_PROOF_BUILD_CONTEXT = build_run_context(
    generator_id=GeneratorId.BACKOFF_SWEEP,
)


def _proof_build_binding(variant: str):
    source = SourceEvidence(
        schema_version=SOURCE_EVIDENCE_SCHEMA,
        source_root=str(_CCBENCH_ROOT),
        ccbench_commit=CURRENT_PIN,
        genome_sha256=hashlib.sha256(
            _PROOF_GENOME.canonical().encode("utf-8")
        ).hexdigest(),
        src_token="stock",
        source_bytes_sha256=hashlib.sha256(
            b"fixed synthetic receipt proof source"
        ).hexdigest(),
        tracked_clean=True,
        tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
        tracked_paths=(),
        proof_source_snapshot=capture_compiled_protocol_source_snapshot(
            "silo", _CCBENCH_ROOT,
        ),
        verification_variant=variant,
    )
    return (
        _PROOF_GENOME,
        source,
        derive_build_admission(_PROOF_BUILD_CONTEXT, source),
    )


def verification_capabilities(
        tags=("legacy",), *, sink_kind: str, lock_identity_sha256: str,
        variant: str, operation_identity: str,
):
    genome, source_evidence, build_admission = _proof_build_binding(variant)
    results = tuple(
        verify_trace_dir_with_capability(
            str(_FIXTURE),
            genome=genome,
            source_evidence=source_evidence,
            build_admission=build_admission,
            receipt_sink_kind=sink_kind,
            receipt_lock_identity_sha256=lock_identity_sha256,
            receipt_variant=variant,
            receipt_operation_identity=operation_identity,
            receipt_workload_tag=tag,
        )
        for tag in tags
    )
    assert all(result.certified for result, _capability in results)
    return [capability for _result, capability in results]


def campaign_receipt(
        layout, variant: str, payload: dict, *, operation_identity: str = "test-op",
        tags=("legacy",), lock_identity_sha256: str | None = None):
    lock_identity = (
        campaign_lock_sha256_or_absent(layout)
        if lock_identity_sha256 is None else lock_identity_sha256
    )
    return issue_commit_receipt(
        verification_capabilities(
            tags,
            sink_kind=CAMPAIGN_WAL_SINK,
            lock_identity_sha256=lock_identity,
            variant=variant,
            operation_identity=operation_identity,
        ),
        workload_tags=list(tags),
        sink_kind=CAMPAIGN_WAL_SINK,
        lock_identity_sha256=lock_identity,
        variant=variant,
        operation_identity=operation_identity,
        terminal_payload=payload,
    )


def qualification_receipt(
        variant: str, payload: dict, *, lock_identity_sha256: str,
        operation_identity: str = "qualification-test-op", tags=("legacy",),
):
    return issue_commit_receipt(
        verification_capabilities(
            tags,
            sink_kind=QUALIFICATION_SINK,
            lock_identity_sha256=lock_identity_sha256,
            variant=variant,
            operation_identity=operation_identity,
        ),
        workload_tags=list(tags),
        sink_kind=QUALIFICATION_SINK,
        lock_identity_sha256=lock_identity_sha256,
        variant=variant,
        operation_identity=operation_identity,
        terminal_payload=payload,
    )


def serialized_qualification_receipt(
        variant: str, payload: dict, *, lock_identity_sha256: str,
        operation_identity: str = "qualification-test-op", tags=("legacy",),
):
    receipt = qualification_receipt(
        variant, payload,
        lock_identity_sha256=lock_identity_sha256,
        operation_identity=operation_identity,
        tags=tags,
    )
    return validate_live_receipt(
        receipt,
        sink_kind=QUALIFICATION_SINK,
        lock_identity_sha256=lock_identity_sha256,
        variant=variant,
        terminal_payload=payload,
    )


def log_receipted_commit(
        layout, variant: str, env_tag: str, payload: dict, *,
        operation_identity: str = "test-op", tags=("legacy",),
        lock_identity_sha256: str | None = None, ts: float | None = None,
):
    receipt = campaign_receipt(
        layout, variant, payload,
        operation_identity=operation_identity,
        tags=tags,
        lock_identity_sha256=lock_identity_sha256,
    )
    return wal.log(
        layout, variant, STAGE_COMMIT, env_tag, payload,
        ts=ts,
        commit_receipt=receipt,
    )


def replay_evidence(
        *, source_variant: str, source_payload: dict,
        source_lock_sha256: str = "a" * 64,
        source_wal_sha256: str = "b" * 64,
):
    receipt = issue_commit_receipt(
        verification_capabilities(
            sink_kind=CAMPAIGN_WAL_SINK,
            lock_identity_sha256=source_lock_sha256,
            variant=source_variant,
            operation_identity="source-test-op",
        ),
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
    source_record = artifact_admission.ImmutableWalRecord(
        variant=source_variant,
        stage=STAGE_COMMIT,
        env_tag="test",
        ts=1.0,
        payload=MappingProxyType({
            **source_payload,
            RECEIPT_PAYLOAD_KEY: serialized,
        }),
    )
    records = (source_record,)
    decision = artifact_admission.CampaignAdmissionDecision(
        classification="test",
        admission_status="admitted",
        verification_status="certified",
        campaign_id="source-test",
        campaign_path="source-test",
        campaign_lock_sha256=source_lock_sha256,
        wal_sha256=source_wal_sha256,
        policy_sha256=None,
        attempt_receipt_sha256s=(),
        overlay_ledger_sha256="c" * 64,
        overlay_record_key=None,
        validator_sha256="d" * 64,
    )
    epoch = artifact_admission.CampaignVerifierEpoch(
        campaign_verifier_epoch="E1:" + "e" * 64,
        state="E1",
        reason_code="recorded-closure",
    )
    # Production exposes no replay-capability issuer.  This test-only fixture
    # extracts the issuer already captured by the public admission closure, so
    # the evidence still crosses the exact production capability check.
    replay_issuers = tuple(
        cell.cell_contents
        for cell in (artifact_admission.require_admitted_campaign.__closure__ or ())
        if callable(cell.cell_contents)
        and getattr(cell.cell_contents, "__name__", None) == "issue"
    )
    assert len(replay_issuers) == 1
    replay_capability = replay_issuers[0](decision, records)
    view = artifact_admission.CertifiedCampaignView(
        layout=artifact_admission.CampaignLayout(root="source-test"),
        records=records,
        decision=decision,
        campaign_verifier_epoch=epoch,
        persisted_certified_commit_count=sum(
            record.stage == STAGE_COMMIT for record in records
        ),
        _certification_token=artifact_admission._CERTIFIED_VIEW_TOKEN,
        _replay_admission_capability=replay_capability,
    )
    return admit_replay_evidence(view, source_record)


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
