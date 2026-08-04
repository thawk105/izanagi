# -*- coding: utf-8 -*-
"""T-126 artifact namespace、evidence admission、formal 分離を検査する。"""
from __future__ import annotations

import json
import hashlib
import os
import secrets
import sys
from copy import deepcopy
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from campaign import layer3_report, pipeline  # noqa: E402
from campaign.build_admission import (  # noqa: E402
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from campaign.model import Genome  # noqa: E402
from campaign.pin import CURRENT_PIN  # noqa: E402
from campaign.source_digest import (  # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    STOCK,
    SourceEvidence,
)
from qualification.artifacts import (  # noqa: E402
    QualificationArtifactError,
    QualificationRoot,
    create_bytes,
    create_or_verify_bytes,
    create_attempt,
    create_json,
    snapshot_source,
    validate_member_evidence,
    validate_retry_history,
)
from qualification.contract import canonical_json_bytes, load_protocol  # noqa: E402
from qualification.attempt_ledger import (  # noqa: E402
    AttemptLedgerError,
    SeriesAttemptLedger,
    replay_attempt_ledger,
)
from qualification import attempt_ledger as attempt_ledger_module  # noqa: E402


def _root(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    root = QualificationRoot(repo)
    return repo, root, root.issue()


def _entry_snapshot(directory: Path):
    result = {}
    for path in sorted(directory.iterdir()):
        current = path.lstat()
        payload = (
            ("symlink", os.readlink(path)) if path.is_symlink()
            else ("regular", path.read_bytes()) if path.is_file()
            else ("other", None)
        )
        result[path.name] = (
            current.st_mode, current.st_uid, current.st_gid,
            current.st_dev, current.st_ino, current.st_nlink,
            current.st_size, payload,
        )
    return result


@pytest.mark.parametrize(
    "shape",
    ["multiple", "suffix", "mode", "symlink", "nonregular",
     "external-hardlink", "partial-target-stage"],
)
def test_shared_create_writer_global_preflight_is_nonmutating(
        tmp_path, shape):
    _, _, capability = _root(tmp_path)
    relative = "attempts/" + "a" * 64 + "/receipt.json"
    target = create_or_verify_bytes(capability, relative, b"same\n")
    stage = target.parent / (
        ".receipt.json.create-123-0123456789abcdef")
    if shape == "symlink":
        outside = tmp_path / "outside"
        outside.write_bytes(b"outside")
        stage.symlink_to(outside)
    elif shape == "nonregular":
        stage.mkdir()
    else:
        stage.write_bytes(
            b"different\n" if shape == "partial-target-stage" else b"same\n")
        stage.chmod(0o644 if shape == "mode" else 0o600)
    if shape == "multiple":
        second = target.parent / (
            ".receipt.json.create-124-fedcba9876543210")
        second.write_bytes(b"second\n")
        second.chmod(0o600)
    elif shape == "suffix":
        stage.rename(target.parent / ".receipt.json.create-malformed")
    elif shape == "external-hardlink":
        os.link(stage, tmp_path / "external-hardlink")
    before = _entry_snapshot(target.parent)
    with pytest.raises(QualificationArtifactError):
        create_or_verify_bytes(capability, relative, b"same\n")
    assert _entry_snapshot(target.parent) == before


@pytest.mark.parametrize("target_present", [False, True])
@pytest.mark.parametrize(
    "suffix",
    [
        "0-0123456789abcdef",
        "00-0123456789abcdef",
        "001-0123456789abcdef",
        "pid-0123456789abcdef",
        "123-0123456789abcdeF",
        "123-0123456789abcde",
        "123-0123456789abcdef0",
    ],
)
def test_shared_create_writer_rejects_generator_unreachable_suffixes(
        tmp_path, target_present, suffix):
    _, root, capability = _root(tmp_path)
    relative = "scratch/canonical-stage.json"
    target = root.path / relative
    target.parent.mkdir(parents=True)
    expected = b'{"ok":true}\n'
    if target_present:
        target.write_bytes(expected)
        target.chmod(0o600)
    stage = target.parent / f".{target.name}.create-{suffix}"
    if target_present:
        os.link(target, stage)
    else:
        stage.write_bytes(expected)
        stage.chmod(0o600)
    before = _entry_snapshot(target.parent)
    with pytest.raises(QualificationArtifactError):
        create_or_verify_bytes(capability, relative, expected)
    assert _entry_snapshot(target.parent) == before


def test_shared_create_writer_has_exact_owner_mode_gate():
    source = (
        _HERE.parent / "qualification/artifacts.py"
    ).read_text(encoding="utf-8")
    assert "current.st_uid != os.getuid()" in source
    assert "stat.S_IMODE(current.st_mode) != 0o600" in source


@pytest.mark.parametrize("caller", ["source-snapshot", "attempt-ledger"])
def test_shared_create_writer_real_callers_preserve_unsafe_stage(
        tmp_path, caller):
    repo, _, capability = _root(tmp_path)
    if caller == "source-snapshot":
        source = repo / "source"
        source.write_bytes(b"source\n")
        relative = "attempts/" + "b" * 64 + "/source/snapshot"
        target = capability.root / relative
        target.parent.mkdir(parents=True)
        stage = target.parent / (
            ".snapshot.create-001-0123456789abcdef")
        invoke = lambda: snapshot_source(
            capability, source, relative,
            expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    else:
        ledger = SeriesAttemptLedger(
            capability, "c" * 64,
            load_protocol()["retry"]["eligible_reasons"])
        target = (
            capability.root / "series" / ("c" * 64)
            / "attempt-ledger/0000.json")
        target.parent.mkdir(parents=True)
        stage = target.parent / (
            ".0000.json.create-001-0123456789abcdef")
        invoke = lambda: ledger.claim_initial(
            nonce="1" * 32, submission_intent_sha256="2" * 64)
    stage.write_bytes(b"unsafe\n")
    stage.chmod(0o600)
    before = _entry_snapshot(target.parent)
    with pytest.raises(QualificationArtifactError):
        invoke()
    assert _entry_snapshot(target.parent) == before


def _member_events():
    stages = (
        ("qualification_build_start", {"genome": "silo|BACK_OFF=1"}),
        ("qualification_build_done", {
            "trace_bin_sha256": "a" * 64,
            "perf_bin_sha256": "b" * 64,
        }),
        ("qualification_verify_done", {
            "workload": {"tag": "legacy"}, "certified": True,
            "commits": 10, "aborts": 2, "anomalies": 0,
            "argv": [
                "/x/trace", "-ycsb_tuple_num=200", "-ycsb_zipf_skew=0.9",
                "-ycsb_rratio=50", "-ycsb_rmw=true", "-ycsb_max_ope=5",
                "-thread_num=4", "-extime=1", "-clocks_per_us=2100",
            ],
            "binary_sha256": "a" * 64,
        }),
        ("qualification_verify_done", {
            "workload": {"tag": "s2"}, "certified": True,
            "commits": 20, "aborts": 3, "anomalies": 0,
            "argv": [
                "/x/trace", "-ycsb_tuple_num=1000000",
                "-ycsb_zipf_skew=0.9", "-ycsb_rratio=50",
                "-ycsb_rmw=false", "-ycsb_max_ope=10",
                "-thread_num=48", "-extime=3", "-clocks_per_us=2100",
            ],
            "binary_sha256": "a" * 64,
        }),
        ("qualification_bench_done", {
            "tps": [100.0] * 5, "median_tps": 100.0, "rep_returncodes": [0] * 5,
            "settled": True, "unstable": False, "rounds": 1,
        }),
        ("qualification_evaluation_terminal", {
            "fitness_tps": 100.0, "verify_configs": ["legacy", "s2"],
        }),
    )
    return [{
        "schema_version": "t126-qualification-evaluation-event/v1",
        "qualification_lineage": "t126-only",
        "event_index": index,
        "round_index": 1,
        "member_role": "subject",
        "event_type": "member_evaluation_event",
        "evaluation_stage": stage,
        "evaluation_wal_key": "variant",
        "env_tag": "pegasus",
        "payload": {
            "canonical_json": json.dumps(
                payload, sort_keys=True, separators=(",", ":")),
            "sha256": hashlib.sha256(json.dumps(
                payload, sort_keys=True, separators=(",", ":")
            ).encode("ascii")).hexdigest(),
        },
    } for index, (stage, payload) in enumerate(stages)]


def _formal_campaign(tmp_path: Path):
    output_root = tmp_path / "repo" / "output"
    campaign = output_root / "campaigns" / "formal-shaped"
    (campaign / "runs").mkdir(parents=True)
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    genome = Genome("silo", {})
    evidence = SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=str(campaign.resolve()),
        ccbench_commit=CURRENT_PIN,
        genome_sha256=hashlib.sha256(
            genome.canonical().encode("utf-8")
        ).hexdigest(),
        src_token=STOCK,
        source_bytes_sha256="a" * 64,
        tracked_clean=True,
        tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
        tracked_paths=(),
    )
    receipt = derive_build_admission(context, evidence).as_wal_receipt()
    (campaign / "campaign.lock").write_text(json.dumps({
        "ccbench_commit": CURRENT_PIN,
        "search_config": {
            "records": 1,
            "threads": 1,
            "build_admission": dict(context.policy.as_preimage()),
        },
        "search_tag": "test", "spec_content": "x", "trial": "t",
    }), encoding="utf-8")
    record = {
        "ts": 1.0,
        "stage": "build_start",
        "variant": pipeline.variant_id(genome, STOCK),
        "env_tag": "test-env",
        "payload": {
            "genome": genome.canonical(),
            "src_token": STOCK,
            "build_attempt_id": "formal-fixture-attempt",
            "build_admission": receipt,
            "build_admission_receipt_sha256": receipt["receipt_sha256"],
        },
    }
    (campaign / "runs/wal.jsonl").write_text(
        json.dumps(record) + "\n", encoding="utf-8")
    return campaign, output_root


def test_root_bound_writer_is_create_only_and_forbids_formal_artifacts(tmp_path):
    _, root, capability = _root(tmp_path)
    layout = create_attempt(
        root, capability, series_id="a" * 64, attempt_id="b" * 64)
    marker = layout.attempt_dir / "qualification-marker.json"
    assert marker.is_file()
    with pytest.raises(QualificationArtifactError):
        create_json(capability, "../escape.json", {"x": 1})
    with pytest.raises(QualificationArtifactError, match="formal"):
        create_json(capability, "attempts/x/runs/wal.jsonl", {"x": 1})
    with pytest.raises(QualificationArtifactError, match="create-only"):
        create_json(
            capability,
            f"attempts/{'b' * 64}/qualification-marker.json",
            {"replacement": True},
        )


def test_m2_formal_shaped_fixture_with_qualification_marker_is_rejected(tmp_path):
    campaign, output_root = _formal_campaign(tmp_path)
    (campaign / "qualification-marker.json").write_text(json.dumps({
        "schema_version": "t126-qualification-marker/v1",
        "qualification_lineage": "t126-only",
    }), encoding="utf-8")
    with pytest.raises(layer3_report.Layer3ReportError, match="qualification"):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)


def test_m2_normal_formal_campaign_remains_accepted(tmp_path):
    campaign, output_root = _formal_campaign(tmp_path)
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root)
    assert report["schema_version"] == "layer3-material-report/v4"
    assert report["meta"]["campaign_id"] == "formal-shaped"


def test_layer3_rejects_qualification_lineage_nested_in_formal_wal(tmp_path):
    campaign, output_root = _formal_campaign(tmp_path)
    path = campaign / "runs/wal.jsonl"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["payload"]["qualification_lineage"] = "t126-only"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(layer3_report.Layer3ReportError, match="qualification"):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)


def test_m2a_ancestor_marker_alone_rejects_formal_shape(tmp_path):
    campaign, output_root = _formal_campaign(tmp_path)
    (output_root / "qualification-marker.json").write_text(
        json.dumps({
            "schema_version": "t126-qualification-marker/v1",
            "qualification_lineage": "t126-only",
        }), encoding="utf-8")
    with pytest.raises(layer3_report.Layer3ReportError, match="qualification"):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)


def test_m2b_lock_lineage_alone_rejects_without_shape_mask(tmp_path):
    campaign, output_root = _formal_campaign(tmp_path)
    lock_path = campaign / "campaign.lock"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["search_config"]["qualification_lineage"] = "t126-only"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    with pytest.raises(layer3_report.Layer3ReportError, match="qualification"):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)


def test_m3_source_snapshot_requires_the_registered_full_hash(tmp_path):
    _, _, capability = _root(tmp_path)
    source = tmp_path / "source.json"
    source.write_bytes(b'{"stable":true}\n')
    with pytest.raises(QualificationArtifactError, match="hash mismatch"):
        snapshot_source(
            capability, source, "snapshots/source.json",
            expected_sha256="0" * 64,
        )


@pytest.mark.parametrize(
    "boundary", ["after-write", "after-fsync", "after-link"])
def test_create_partial_crash_is_recoverable_at_each_publish_boundary(
        tmp_path, boundary):
    _, root, capability = _root(tmp_path)
    relative = f"scratch/{boundary}.json"

    def crash(stage):
        if stage == boundary:
            raise OSError("injected create crash")

    with pytest.raises(
            (OSError, QualificationArtifactError), match="injected"):
        create_bytes(
            capability, relative, b'{"ok":true}\n', fault_inject=crash)
    target = root.path / relative
    assert not list(target.parent.glob(f".{target.name}.create-*"))
    recovered = create_or_verify_bytes(
        capability, relative, b'{"ok":true}\n')
    assert recovered.read_bytes() == b'{"ok":true}\n'


@pytest.mark.parametrize(
    ("boundary", "published"),
    [("after-write", False), ("after-fsync", False), ("after-link", True)],
)
def test_create_recovers_staging_abandoned_by_hard_crash(
        tmp_path, boundary, published):
    _, root, capability = _root(tmp_path)
    relative = f"scratch/hard-{boundary}.json"
    target = root.path / relative
    target.parent.mkdir(parents=True)
    staging = target.parent / (
        f".{target.name}.create-{os.getpid()}-{secrets.token_hex(8)}")
    expected = b'{"ok":true}\n'
    staging.write_bytes(
        b'{"ok":' if boundary == "after-write" else expected)
    staging.chmod(0o600)
    if published:
        os.link(staging, target)

    recovered = create_or_verify_bytes(capability, relative, expected)

    assert recovered.read_bytes() == expected
    assert not staging.exists()
    assert not list(target.parent.glob(f".{target.name}.create-*"))


def test_m4_settled_false_rejects_and_full_evidence_accepts():
    records = _member_events()
    admitted = validate_member_evidence(
        records, expected_role="subject", expected_round=1)
    assert admitted["settled"] is True
    mutated = deepcopy(records)
    payload = json.loads(mutated[4]["payload"]["canonical_json"])
    payload["settled"] = False
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    mutated[4]["payload"] = {
        "canonical_json": encoded,
        "sha256": hashlib.sha256(encoded.encode("ascii")).hexdigest(),
    }
    with pytest.raises(QualificationArtifactError, match="settled"):
        validate_member_evidence(
            mutated, expected_role="subject", expected_round=1)


def test_m5a_exact_s2_tag_order_has_no_argv_mask():
    records = _member_events()
    records[2]["payload"], records[3]["payload"] = (
        records[3]["payload"], records[2]["payload"])
    with pytest.raises(QualificationArtifactError, match="legacy\\+S2"):
        validate_member_evidence(
            records, expected_role="subject", expected_round=1)


def test_m5b_s2_exact_argv_flag_has_no_shape_or_tag_mask():
    records = _member_events()
    payload = json.loads(records[3]["payload"]["canonical_json"])
    payload["argv"][-1] = "-clocks_per_us=2099"
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    records[3]["payload"] = {
        "canonical_json": encoded,
        "sha256": hashlib.sha256(encoded.encode("ascii")).hexdigest(),
    }
    with pytest.raises(QualificationArtifactError, match="runtime evidence"):
        validate_member_evidence(
            records, expected_role="subject", expected_round=1)


def test_anomaly_gate_remains_conjunctive():
    records = _member_events()
    payload = json.loads(records[3]["payload"]["canonical_json"])
    payload["anomalies"] = 1
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    records[3]["payload"] = {
        "canonical_json": encoded,
        "sha256": hashlib.sha256(encoded.encode("ascii")).hexdigest(),
    }
    with pytest.raises(QualificationArtifactError):
        validate_member_evidence(
            records, expected_role="subject", expected_round=1)


def test_m7_retry_only_once_before_first_observation():
    protocol = load_protocol()
    eligible = {
        "attempt_id": "a" * 64, "observations_recorded": 0,
        "terminal": None, "failure_reason": "pre-member-infrastructure",
    }
    current = {
        "attempt_id": "b" * 64, "observations_recorded": 0,
        "terminal": None, "failure_reason": "pre-member-infrastructure",
    }
    assert validate_retry_history([eligible], protocol) is True
    assert validate_retry_history([eligible, current], protocol) is False
    observed = dict(eligible, observations_recorded=1)
    with pytest.raises(QualificationArtifactError, match="first observation"):
        validate_retry_history([observed, current], protocol)


def test_m7a_series_ledger_rejects_duplicate_initial_submission(tmp_path):
    _, _, capability = _root(tmp_path)
    protocol = load_protocol()
    ledger = SeriesAttemptLedger(
        capability, "a" * 64, protocol["retry"]["eligible_reasons"])
    ledger.claim_initial(
        nonce="1" * 32, submission_intent_sha256="2" * 64)
    ledger.bind_submitted(
        retry_index=0, nonce="1" * 32, job_id="123.server",
        attempt_id="5" * 64, qsub_invocation_sha256="4" * 64,
        submission_evidence_sha256="6" * 64)
    with pytest.raises(AttemptLedgerError, match="duplicate initial"):
        ledger.claim_initial(
            nonce="3" * 32, submission_intent_sha256="4" * 64)


def test_m7b_series_ledger_rejects_retry_of_retry(tmp_path):
    _, _, capability = _root(tmp_path)
    protocol = load_protocol()
    ledger = SeriesAttemptLedger(
        capability, "a" * 64, protocol["retry"]["eligible_reasons"])
    ledger.claim_initial(
        nonce="1" * 32, submission_intent_sha256="2" * 64)
    ledger.bind_submitted(
        retry_index=0, nonce="1" * 32, job_id="123.server",
        attempt_id="5" * 64, qsub_invocation_sha256="4" * 64,
        submission_evidence_sha256="6" * 64)
    ledger.record_outcome(
        attempt_id="5" * 64, retry_index=0, observations_recorded=0,
        terminal=None, failure_class="pre-member-infrastructure",
        receipt_sha256="7" * 64)
    ledger.claim_retry(
        nonce="8" * 32, submission_intent_sha256="9" * 64,
        retry_from_attempt_id="5" * 64,
        retry_from_receipt_sha256="7" * 64)
    ledger.bind_submitted(
        retry_index=1, nonce="8" * 32, job_id="124.server",
        attempt_id="b" * 64, qsub_invocation_sha256="a" * 64,
        submission_evidence_sha256="c" * 64)
    ledger.record_outcome(
        attempt_id="b" * 64, retry_index=1, observations_recorded=0,
        terminal=None, failure_class="pre-member-infrastructure",
        receipt_sha256="d" * 64)
    assert ledger.replay.state == "retry_failed"
    with pytest.raises(AttemptLedgerError, match="suffix|retry"):
        ledger.claim_retry(
            nonce="e" * 32, submission_intent_sha256="f" * 64,
            retry_from_attempt_id="b" * 64,
            retry_from_receipt_sha256="d" * 64)


def test_attempt_ledger_rejects_submitted_without_intent(tmp_path):
    _, _, capability = _root(tmp_path)
    protocol = load_protocol()
    partial = SeriesAttemptLedger(
        capability, "2" * 64, protocol["retry"]["eligible_reasons"])
    with pytest.raises(AttemptLedgerError, match="intent"):
        partial.bind_submitted(
            retry_index=0, nonce="1" * 32, job_id="123.server",
            attempt_id="3" * 64, qsub_invocation_sha256="5" * 64,
            submission_evidence_sha256="4" * 64)


@pytest.mark.parametrize(
    "event_type",
    ["initial_intent", "initial_submitted", "attempt_outcome_pending",
     "attempt_outcome"],
)
@pytest.mark.parametrize("boolean_index", [False, True])
def test_attempt_ledger_payloads_reject_boolean_retry_index(
        tmp_path, event_type, boolean_index):
    _, _, capability = _root(tmp_path)
    protocol = load_protocol()
    ledger = SeriesAttemptLedger(
        capability, "3" * 64, protocol["retry"]["eligible_reasons"])
    ledger.claim_initial(
        nonce="1" * 32, submission_intent_sha256="2" * 64)
    ledger.bind_submitted(
        retry_index=0, nonce="1" * 32, job_id="123.server",
        attempt_id="4" * 64, qsub_invocation_sha256="5" * 64,
        submission_evidence_sha256="6" * 64)
    ledger.record_outcome(
        attempt_id="4" * 64, retry_index=0, observations_recorded=0,
        terminal=None, failure_class="pre-member-infrastructure",
        receipt_sha256="7" * 64)
    events = ledger.load()
    previous = "0" * 64
    for event in events:
        event["previous_event_sha256"] = previous
        if event["event_type"] == event_type:
            event["payload"]["retry_index"] = boolean_index
        unhashed = {
            key: value for key, value in event.items()
            if key != "event_sha256"}
        event["event_sha256"] = hashlib.sha256(
            canonical_json_bytes(unhashed)).hexdigest()
        previous = event["event_sha256"]
    with pytest.raises(AttemptLedgerError, match="retry index"):
        replay_attempt_ledger(
            events, series_id="3" * 64,
            eligible_reasons=protocol["retry"]["eligible_reasons"])


def test_m7c_series_ledger_rejects_retry_after_first_observation(tmp_path):
    _, _, capability = _root(tmp_path)
    protocol = load_protocol()
    observed = SeriesAttemptLedger(
        capability, "5" * 64, protocol["retry"]["eligible_reasons"])
    observed.claim_initial(
        nonce="6" * 32, submission_intent_sha256="7" * 64)
    observed.bind_submitted(
        retry_index=0, nonce="6" * 32, job_id="123.server",
        attempt_id="8" * 64, qsub_invocation_sha256="4" * 64,
        submission_evidence_sha256="9" * 64)
    observed.record_outcome(
        attempt_id="8" * 64, retry_index=0, observations_recorded=1,
        terminal=None, failure_class="pre-member-infrastructure",
        receipt_sha256="a" * 64)
    with pytest.raises(AttemptLedgerError, match="pre-observation"):
        observed.claim_retry(
            nonce="b" * 32, submission_intent_sha256="c" * 64,
            retry_from_attempt_id="8" * 64,
            retry_from_receipt_sha256="a" * 64)


def test_m7c_series_ledger_terminal_state_is_the_effective_retry_anchor(
        tmp_path, monkeypatch):
    _, _, capability = _root(tmp_path)
    protocol = load_protocol()
    terminal = SeriesAttemptLedger(
        capability, "d" * 64, protocol["retry"]["eligible_reasons"])
    terminal.claim_initial(
        nonce="1" * 32, submission_intent_sha256="2" * 64)
    terminal.bind_submitted(
        retry_index=0, nonce="1" * 32, job_id="123.server",
        attempt_id="3" * 64, qsub_invocation_sha256="8" * 64,
        submission_evidence_sha256="4" * 64)
    terminal.record_outcome(
        attempt_id="3" * 64, retry_index=0, observations_recorded=0,
        terminal="lower_boundary", failure_class="none",
        receipt_sha256="5" * 64)
    with pytest.raises(AttemptLedgerError, match="pre-observation"):
        terminal.claim_retry(
            nonce="6" * 32, submission_intent_sha256="7" * 64,
            retry_from_attempt_id="3" * 64,
            retry_from_receipt_sha256="5" * 64)
    monkeypatch.setattr(
        attempt_ledger_module, "_require_retry_admission",
        lambda **_kwargs: None)
    terminal.claim_retry(
        nonce="6" * 32, submission_intent_sha256="7" * 64,
        retry_from_attempt_id="3" * 64,
        retry_from_receipt_sha256="5" * 64)
    assert terminal.replay.state == "retry_intent"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
