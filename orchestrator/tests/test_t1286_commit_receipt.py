# -*- coding: utf-8 -*-
"""T-1286 verifier-issued COMMIT receipt chokepoints and replay binding."""
from __future__ import annotations

import ast
from copy import copy, deepcopy
import hashlib
import json
import os
import sys
import types
from pathlib import Path
from types import MappingProxyType

import pytest

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_ORCH.parent))

import commit_receipt_support as receipt_support  # noqa: E402
from orchestrator.campaign import (  # noqa: E402
    artifact_admission,
    campaign_lock,
    guided,
    ident,
    pipeline,
    wal,
)
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.layout import CampaignLayout  # noqa: E402
from orchestrator.campaign.model import (  # noqa: E402
    CampaignConfig,
    STAGE_ABORT,
    STAGE_BENCH_DONE,
    STAGE_BUILD_DONE,
    STAGE_BUILD_START,
    STAGE_COMMIT,
    STAGE_VERIFY_DONE,
    WalRecord,
)
from orchestrator.campaign.pin import CURRENT_PIN  # noqa: E402
from orchestrator.campaign.replay import GenomeResult, parse_flags  # noqa: E402
from orchestrator.campaign.source_digest import (  # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    STOCK,
    SourceEvidence,
)
from orchestrator.qualification.artifacts import (  # noqa: E402
    QualificationArtifactError,
    QualificationEventSink,
    QualificationRoot,
    create_attempt,
    load_jsonl_strict,
)
from orchestrator.verifier import (  # noqa: E402
    CAMPAIGN_WAL_SINK,
    QUALIFICATION_SINK,
    CommitReceiptError,
    ReplayVerificationEvidence,
    VerificationCapability,
    admit_replay_evidence,
    campaign_lock_sha256,
    issue_commit_receipt,
    validate_live_receipt,
    verify_trace_dir_with_capability,
)
from orchestrator.verifier import core as verifier_core  # noqa: E402
from orchestrator.verifier.model import Integrity, VerifyResult  # noqa: E402
from orchestrator.verifier.parse import TxnFramingViolation  # noqa: E402


_CANON = "silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0"
_TEST_BUILD_CONTEXT = build_run_context(
    generator_id=GeneratorId.BACKOFF_SWEEP,
)
_TEST_ADMISSION_POLICY = _TEST_BUILD_CONTEXT.policy


def _v1_layout(tmp_path: Path, name: str = "campaign") -> CampaignLayout:
    layout = CampaignLayout(root=str(tmp_path / name)).ensure()
    cfg = CampaignConfig(
        spec_slug="t1286", search_tag="receipt", spec_content="fixture",
        ccbench_commit="deadbeef",
    )
    cfg = ident.bind_admission_policy(cfg, _TEST_ADMISSION_POLICY)
    wal.write_lock(layout, ident.canonical_preimage(cfg))
    decoded = campaign_lock.decode_campaign_lock(
        Path(layout.lock_file).read_text(encoding="utf-8")
    )
    assert decoded.is_v1
    return layout


def _record(payload: dict, variant: str = "v") -> WalRecord:
    return WalRecord(
        variant=variant, stage=STAGE_COMMIT, env_tag="test", ts=1.0,
        payload=payload,
    )


def _qualification_sink(tmp_path: Path, *, lock_sha: str = "a" * 64):
    repo = tmp_path / "repo"
    repo.mkdir()
    root = QualificationRoot(repo)
    capability = root.issue()
    layout = create_attempt(
        root, capability, series_id="c" * 64, attempt_id="d" * 64,
    )
    sink = QualificationEventSink(
        capability, layout, round_index=1, role="subject",
        source_lock_identity_sha256=lock_sha,
    )
    return layout, sink, lock_sha


def _qualification_receipt(lock_sha: str, payload: dict, variant: str = "v"):
    operation_identity = "qualification-test-op"
    return issue_commit_receipt(
        receipt_support.verification_capabilities(
            sink_kind=QUALIFICATION_SINK,
            lock_identity_sha256=lock_sha,
            variant=variant,
            operation_identity=operation_identity,
        ),
        workload_tags=["legacy"],
        sink_kind=QUALIFICATION_SINK,
        lock_identity_sha256=lock_sha,
        variant=variant,
        operation_identity=operation_identity,
        terminal_payload=payload,
    )


def test_direct_wal_append_without_receipt_rejects_v1_and_preserves_bytes(tmp_path: Path):
    layout = _v1_layout(tmp_path)
    receipt_support.append_legacy_raw_commit(
        layout, "legacy", "test", {"fitness_tps": 1.0})
    before = Path(layout.wal_file).read_bytes()
    with pytest.raises(CommitReceiptError, match="live CommitReceipt"):
        wal.append(layout, _record({"fitness_tps": 2.0}, "new"))
    assert Path(layout.wal_file).read_bytes() == before


def test_normal_wal_receipt_commits_and_duplicate_is_rejected(tmp_path: Path):
    layout = _v1_layout(tmp_path)
    payload = {"fitness_tps": 2.0}
    receipt = receipt_support.campaign_receipt(layout, "v", payload)
    serialized = validate_live_receipt(
        receipt, sink_kind=CAMPAIGN_WAL_SINK,
        lock_identity_sha256=campaign_lock_sha256(layout),
        variant="v", terminal_payload=payload,
    )
    with pytest.raises(CommitReceiptError, match="live CommitReceipt"):
        wal.append(layout, _record(payload), commit_receipt=serialized)
    assert Path(layout.wal_file).read_bytes() == b""
    wal.append(layout, _record(payload), commit_receipt=receipt)
    committed = Path(layout.wal_file).read_bytes()
    with pytest.raises(CommitReceiptError, match="already consumed"):
        wal.append(layout, _record(payload), commit_receipt=receipt)
    assert Path(layout.wal_file).read_bytes() == committed
    rows = wal.read_records(layout)
    assert len(rows) == 1
    assert rows[0].payload["commit_verification_receipt"]["receipt_id"]


def test_receipt_rejects_changed_lock_and_changed_payload_without_write(tmp_path: Path):
    layout = _v1_layout(tmp_path)
    payload = {"fitness_tps": 2.0}
    receipt = receipt_support.campaign_receipt(layout, "v", payload)
    Path(layout.wal_file).touch()
    before = Path(layout.wal_file).read_bytes()

    original_lock = json.loads(Path(layout.lock_file).read_text(encoding="utf-8"))
    Path(layout.lock_file).write_text(
        json.dumps(original_lock, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with pytest.raises(CommitReceiptError, match="binding mismatch"):
        wal.append(layout, _record(payload), commit_receipt=receipt)
    assert Path(layout.wal_file).read_bytes() == before

    layout2 = _v1_layout(tmp_path, "campaign-two")
    receipt2 = receipt_support.campaign_receipt(layout2, "v", payload)
    with pytest.raises(CommitReceiptError, match="binding mismatch"):
        wal.append(
            layout2, _record({"fitness_tps": 3.0}), commit_receipt=receipt2,
        )
    assert Path(layout2.wal_file).read_bytes() == b""


def test_wal_append_accepts_issuer_bound_receipt_without_physical_lock(tmp_path: Path):
    layout = _v1_layout(tmp_path)
    payload = {"fitness_tps": 2.0}
    receipt = receipt_support.campaign_receipt(layout, "v", payload)
    lock_identity = campaign_lock_sha256(layout)
    Path(layout.lock_file).unlink()

    wal.append(layout, _record(payload), commit_receipt=receipt)

    rows = wal.read_records(layout)
    assert len(rows) == 1
    assert (
        rows[0].payload["commit_verification_receipt"]["lock_identity_sha256"]
        == lock_identity
    )


@pytest.mark.parametrize("fixture", ["r1_write_skew", "r2_lost_update"])
def test_uncertified_verifier_capability_cannot_issue_receipt(
        fixture: str,
):
    trace_dir = _HERE / "fixtures" / fixture
    result, capability = verify_trace_dir_with_capability(
        str(trace_dir),
        receipt_sink_kind=CAMPAIGN_WAL_SINK,
        receipt_lock_identity_sha256="a" * 64,
        receipt_variant="v",
        receipt_operation_identity="op",
        receipt_workload_tag="legacy",
    )
    assert result.certified is False
    assert result.verdict in {"indeterminate", "non-serializable"}
    with pytest.raises(CommitReceiptError, match="not certified"):
        issue_commit_receipt(
            [capability], workload_tags=["legacy"],
            sink_kind="campaign-wal", lock_identity_sha256="a" * 64,
            variant="v", operation_identity="op",
            terminal_payload={"fitness_tps": 1.0},
        )


def test_verification_capability_hash_ignores_framing_violation_details(
        monkeypatch,
):
    def _result(detail: TxnFramingViolation) -> VerifyResult:
        return VerifyResult(
            trace_dir="/fixture/stable-trace",
            serializable=True,
            n_txns=1,
            integrity=Integrity(
                framing_violations=1,
                framing_violation_details=[detail],
                notes=["stable note"],
            ),
        )

    results = iter((
        _result(TxnFramingViolation(
            kind="count-mismatch", txid=0,
            expected_reads=1, observed_reads=0,
            expected_writes=0, observed_writes=0,
        )),
        _result(TxnFramingViolation(kind="missing-end", txid=0)),
    ))
    monkeypatch.setattr(
        verifier_core,
        "verify_trace_dir",
        lambda *args, **kwargs: next(results),
    )
    binding = {
        "receipt_sink_kind": CAMPAIGN_WAL_SINK,
        "receipt_lock_identity_sha256": "a" * 64,
        "receipt_variant": "v",
        "receipt_operation_identity": "op",
        "receipt_workload_tag": "legacy",
    }

    _first_result, first = verify_trace_dir_with_capability(
        "ignored", **binding,
    )
    _second_result, second = verify_trace_dir_with_capability(
        "ignored", **binding,
    )

    assert first._result_sha256 == second._result_sha256


def test_caller_built_verify_result_has_no_receipt_issuer() -> None:
    caller_result = VerifyResult(
        trace_dir="never-read",
        serializable=True,
        n_txns=1,
    )
    with pytest.raises(TypeError, match="verifier-issued"):
        VerificationCapability(
            caller_result,
            sink_kind=CAMPAIGN_WAL_SINK,
            lock_identity_sha256="a" * 64,
            variant="v",
            operation_identity="op",
            workload_tag="legacy",
        )


def test_verification_capability_is_operation_bound_and_single_use() -> None:
    trace_dir = _HERE / "fixtures" / "g1_serial"
    binding = {
        "receipt_sink_kind": CAMPAIGN_WAL_SINK,
        "receipt_lock_identity_sha256": "a" * 64,
        "receipt_variant": "v",
        "receipt_operation_identity": "op-1",
        "receipt_workload_tag": "legacy",
    }
    result, capability = verify_trace_dir_with_capability(
        str(trace_dir), **binding,
    )
    assert result.certified
    assert not hasattr(capability, "_issuer_token")
    issue_args = {
        "workload_tags": ["legacy"],
        "sink_kind": CAMPAIGN_WAL_SINK,
        "lock_identity_sha256": "a" * 64,
        "variant": "v",
        "operation_identity": "op-1",
        "terminal_payload": {"fitness_tps": 1.0},
    }
    issue_commit_receipt([capability], **issue_args)
    with pytest.raises(CommitReceiptError, match="consumed"):
        issue_commit_receipt([capability], **issue_args)

    _result, copy_source = verify_trace_dir_with_capability(
        str(trace_dir), **binding,
    )
    shallow_clone = copy(copy_source)
    deep_clone = deepcopy(copy_source)
    issue_commit_receipt([copy_source], **issue_args)
    with pytest.raises(CommitReceiptError, match="consumed"):
        issue_commit_receipt([shallow_clone], **issue_args)
    with pytest.raises(CommitReceiptError, match="issuer authority"):
        issue_commit_receipt([deep_clone], **issue_args)

    _result, other_capability = verify_trace_dir_with_capability(
        str(trace_dir), **binding,
    )
    mutated_clone = copy(other_capability)
    object.__setattr__(mutated_clone, "_variant", "other-v")
    object.__setattr__(mutated_clone, "_operation_identity", "op-2")
    object.__setattr__(mutated_clone, "_result_sha256", "f" * 64)
    with pytest.raises(CommitReceiptError, match="different operation"):
        issue_commit_receipt(
            [mutated_clone],
            **{
                **issue_args,
                "variant": "other-v",
                "operation_identity": "op-2",
            },
        )
    mismatches = (
        {"operation_identity": "op-2"},
        {"variant": "other-v"},
        {"lock_identity_sha256": "b" * 64},
        {"sink_kind": QUALIFICATION_SINK},
        {"workload_tags": ["other-workload"]},
    )
    for mismatch in mismatches:
        with pytest.raises(CommitReceiptError, match="different operation"):
            issue_commit_receipt(
                [other_capability],
                **{**issue_args, **mismatch},
            )
    issue_commit_receipt([other_capability], **issue_args)


def test_caller_built_serialized_receipt_cannot_become_replay_evidence(
    tmp_path: Path,
) -> None:
    assert not hasattr(
        artifact_admission,
        "_issue_replay_admission_capability",
    )
    from orchestrator.verifier import commit_receipt as receipt_module
    assert not hasattr(receipt_module, "_REPLAY_TOKEN")
    assert not hasattr(receipt_module, "_issue_replay_verification_evidence")
    serialized = {
        "schema": "campaign-commit-verification-receipt/v1",
        "certified": True,
    }
    with pytest.raises(TypeError, match="admission-issued"):
        ReplayVerificationEvidence(
            receipt=serialized,
            source_campaign_lock_sha256="a" * 64,
            source_wal_sha256="b" * 64,
            source_variant="source-v",
        )
    with pytest.raises(CommitReceiptError, match="CertifiedCampaignView"):
        admit_replay_evidence(serialized, serialized)
    view = _receiptless_certified_source_view(tmp_path)
    with pytest.raises(CommitReceiptError, match="exact COMMIT source record"):
        admit_replay_evidence(view, serialized)
    with pytest.raises(CommitReceiptError, match="lacks replay admission authority"):
        admit_replay_evidence(view, view.records[-1])

    class FakeReplayAuthority:
        def _assert_source(self, _view, _record) -> None:
            return None

    forged_view = artifact_admission.CertifiedCampaignView(
        layout=view.layout,
        records=view.records,
        decision=view.decision,
        campaign_verifier_epoch=view.campaign_verifier_epoch,
        _certification_token=artifact_admission._CERTIFIED_VIEW_TOKEN,
        _replay_admission_capability=FakeReplayAuthority(),
    )
    with pytest.raises(CommitReceiptError, match="lacks replay admission authority"):
        admit_replay_evidence(forged_view, forged_view.records[-1])


def test_qualification_sink_receipt_gate_is_locked_and_byte_stable(tmp_path: Path):
    layout, sink, lock_sha = _qualification_sink(tmp_path)
    path = layout.attempt_dir / "rounds/0001/subject/evaluation-events.jsonl"
    payload = {"fitness_tps": 2.0}
    with pytest.raises(QualificationArtifactError, match="live CommitReceipt"):
        sink.emit(layout, "v", STAGE_COMMIT, "pegasus", payload)
    assert path.read_bytes() == b""

    receipt = _qualification_receipt(lock_sha, payload)
    serialized = validate_live_receipt(
        receipt, sink_kind=QUALIFICATION_SINK,
        lock_identity_sha256=lock_sha, variant="v",
        terminal_payload=payload,
    )
    with pytest.raises(QualificationArtifactError, match="live CommitReceipt"):
        sink.emit(
            layout, "v", STAGE_COMMIT, "pegasus", payload,
            commit_receipt=serialized,
        )
    assert path.read_bytes() == b""
    sink.emit(
        layout, "v", STAGE_COMMIT, "pegasus", payload,
        commit_receipt=receipt,
    )
    committed = path.read_bytes()
    with pytest.raises(QualificationArtifactError, match="already consumed"):
        sink.emit(
            layout, "v", STAGE_COMMIT, "pegasus", payload,
            commit_receipt=receipt,
        )
    assert path.read_bytes() == committed
    assert load_jsonl_strict(path)[0]["commit_verification_receipt"]["receipt_id"]


def test_recovery_internal_writer_rejects_commit_before_write(tmp_path: Path):
    layout = _v1_layout(tmp_path)
    path = Path(layout.wal_file)
    path.touch()
    fd = os.open(path, os.O_RDWR | os.O_APPEND)
    try:
        with pytest.raises(wal.InterruptedAttemptRecoveryError, match="STAGE_ABORT only"):
            wal._append_records_locked(layout, fd, [_record({})])
    finally:
        os.close(fd)
    assert path.read_bytes() == b""


def test_guided_bare_certified_result_is_rejected_before_wal_write(tmp_path: Path):
    layout = _v1_layout(tmp_path)
    result = GenomeResult(
        genome=_CANON, flags=parse_flags(_CANON), fitness_tps=1.0,
        tps=[1.0] * 5, leading_indicators={}, certified=True,
    )
    with pytest.raises(ValueError, match="source verifier receipt"):
        guided._log_eval(layout, result)
    assert not Path(layout.wal_file).exists()


def _receiptless_certified_source_view(tmp_path: Path):
    source = CampaignLayout(root=str(tmp_path / "source-view")).ensure()
    rows = (
        (STAGE_BUILD_START, {"genome": _CANON}),
        (STAGE_BENCH_DONE, {
            "median_tps": 1.0, "tps": [1.0] * 5,
            "leading_indicators": {},
        }),
        (STAGE_VERIFY_DONE, {"certified": True}),
        (STAGE_COMMIT, {"fitness_tps": 1.0}),
    )
    records = tuple(
        artifact_admission.ImmutableWalRecord(
            variant="source-v", stage=stage, env_tag="test", ts=float(index),
            payload=MappingProxyType(payload),
        )
        for index, (stage, payload) in enumerate(rows)
    )
    decision = artifact_admission.CampaignAdmissionDecision(
        classification="test", admission_status="admitted",
        verification_status="certified", campaign_id="source",
        campaign_path=source.root, campaign_lock_sha256="a" * 64,
        wal_sha256="b" * 64, policy_sha256=None,
        attempt_receipt_sha256s=(), overlay_ledger_sha256="c" * 64,
        overlay_record_key=None, validator_sha256="d" * 64,
    )
    epoch = artifact_admission.CampaignVerifierEpoch(
        campaign_verifier_epoch="E1:" + "e" * 64,
        state="E1", reason_code="recorded-closure",
    )
    return artifact_admission.CertifiedCampaignView(
        layout=source, records=records, decision=decision,
        campaign_verifier_epoch=epoch,
        _certification_token=artifact_admission._CERTIFIED_VIEW_TOKEN,
    )


def test_cmd_evaluate_rejects_receiptless_result_from_exact_source_view(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    root = str(tmp_path / "guided-root")
    trial = "false-source"
    layout = guided._trial_layout(trial, root)
    layout.ensure()
    meta = {
        "tag": "balanced", "workload": {"ycsb_rratio": "50"},
        "seed": "7", "trial": trial,
    }
    guided._write_meta(layout, meta)
    ident.ensure_resumable_wal(
        guided._trial_config(meta, trial), layout,
        admission_policy=guided._NO_BUILD_POLICY,
        require_environment_contract=False,
    )
    source_view = _receiptless_certified_source_view(tmp_path)
    before = Path(layout.wal_file).read_bytes() if Path(layout.wal_file).exists() else b""
    monkeypatch.setattr(
        guided.replay, "discover_p2_2_dir", lambda *_args, **_kwargs: source_view,
    )
    monkeypatch.setattr(guided, "_print_state", lambda *_args: None)
    with pytest.raises(ValueError, match="source verifier receipt"):
        guided.cmd_evaluate(types.SimpleNamespace(
            trial=trial, root=root, genome="B0-L-W0",
        ))
    after = Path(layout.wal_file).read_bytes() if Path(layout.wal_file).exists() else b""
    assert after == before


def test_legacy_receiptless_replay_and_recovery_are_byte_stable(tmp_path: Path):
    layout = _v1_layout(tmp_path)
    admission = derive_build_admission(
        _TEST_BUILD_CONTEXT,
        SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=os.path.realpath(layout.root),
            ccbench_commit=CURRENT_PIN,
            genome_sha256=hashlib.sha256(_CANON.encode("utf-8")).hexdigest(),
            src_token=STOCK,
            source_bytes_sha256=hashlib.sha256(
                b"legacy-receiptless-fixture"
            ).hexdigest(),
            tracked_clean=True,
            tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
            tracked_paths=(),
        ),
    ).as_wal_receipt()
    attempt_id = "legacy-receiptless-attempt"
    propagated = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": admission["receipt_sha256"],
    }
    wal.log(layout, "legacy", STAGE_BUILD_START, "test", {
        "genome": _CANON,
        "src_token": STOCK,
        "build_admission": admission,
        **propagated,
    })
    wal.log(layout, "legacy", STAGE_BUILD_DONE, "test", dict(propagated))
    receipt_support.append_legacy_raw_commit(
        layout, "legacy", "test", {"fitness_tps": 1.0, **propagated})
    before = Path(layout.wal_file).read_bytes()
    assert wal.replay(layout)["legacy"].committed
    assert wal.recover_interrupted_attempts(
        layout, admission_policy=_TEST_ADMISSION_POLICY,
    ) == []
    assert wal.replay(layout)["legacy"].committed
    assert Path(layout.wal_file).read_bytes() == before


def test_forked_second_writer_cannot_reuse_parent_process_receipt(tmp_path: Path):
    layout = _v1_layout(tmp_path)
    payload = {"fitness_tps": 2.0}
    receipt = receipt_support.campaign_receipt(layout, "v", payload)
    start_r, start_w = os.pipe()
    pid = os.fork()
    if pid == 0:  # pragma: no cover - assertion is observed through child rc
        os.close(start_w)
        os.read(start_r, 1)
        try:
            wal.append(layout, _record(payload), commit_receipt=receipt)
        except CommitReceiptError:
            os._exit(0)
        os._exit(1)
    os.close(start_r)
    os.write(start_w, b"x")
    os.close(start_w)
    wal.append(layout, _record(payload), commit_receipt=receipt)
    _child, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
    assert len(wal.read_records(layout)) == 1


def _commit_calls(path: Path) -> list[tuple[str, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or len(node.args) < 3:
            continue
        stage = node.args[2]
        if not isinstance(stage, ast.Name) or stage.id != "STAGE_COMMIT":
            continue
        func = node.func
        parts = []
        while isinstance(func, ast.Attribute):
            parts.append(func.attr)
            func = func.value
        if isinstance(func, ast.Name):
            parts.append(func.id)
        calls.append((".".join(reversed(parts)), node.lineno))
    return calls


def test_production_commit_producer_census_is_exactly_five():
    pipeline_calls = _commit_calls(Path(pipeline.__file__))
    guided_calls = _commit_calls(Path(guided.__file__))
    assert [name for name, _line in pipeline_calls] == [
        "wal.log", "qualification_policy.event_sink.emit",
        "wal.log", "qualification_policy.event_sink.emit",
    ]
    assert [name for name, _line in guided_calls] == ["wal.log"]

    all_calls = []
    for path in sorted(_ORCH.rglob("*.py")):
        if "tests" in path.parts:
            continue
        all_calls.extend(
            (path.relative_to(_ORCH).as_posix(), name)
            for name, _line in _commit_calls(path)
        )
    assert all_calls == [
        ("campaign/guided.py", "wal.log"),
        ("campaign/pipeline.py", "wal.log"),
        ("campaign/pipeline.py", "qualification_policy.event_sink.emit"),
        ("campaign/pipeline.py", "wal.log"),
        ("campaign/pipeline.py", "qualification_policy.event_sink.emit"),
    ]


def test_verification_capability_issuer_call_site_is_exactly_core_entrypoint():
    issuer_calls = []
    forbidden_issuer_names = []
    for path in sorted(_ORCH.rglob("*.py")):
        if "tests" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        if "_issue_verification_capability" in source:
            forbidden_issuer_names.append(path.relative_to(_ORCH).as_posix())
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "_VerificationCapability"):
                issuer_calls.append(
                    (path.relative_to(_ORCH).as_posix(), node.lineno)
                )
    assert forbidden_issuer_names == []
    assert len(issuer_calls) == 1
    assert issuer_calls[0][0] == "verifier/core.py"


def _run() -> int:
    """Repository plain-runner contract: execute, never false-green collect zero."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
