# -*- coding: utf-8 -*-
"""T-126 single-process FSM、driver 順序、exact pipeline opt-in を検査する。"""
from __future__ import annotations

import sys
import os
import json
import select
import signal
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[1]))

import test_campaign as campaign_fixtures  # noqa: E402
from orchestrator.calibrator import schema_v2  # noqa: E402
from orchestrator.campaign import env_attestation, env_contract, pipeline  # noqa: E402
from orchestrator.campaign.build_admission import (  # noqa: E402
    BuildProvenance,
    GeneratorId,
    build_run_context,
)
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.qualification.artifacts import (  # noqa: E402
    QualificationArtifactError,
    QualificationEventSink,
    QualificationLayout,
    QualificationRoot,
    create_attempt,
    load_jsonl_strict,
    validate_member_evidence,
)
from orchestrator.qualification.contract import load_protocol  # noqa: E402
from orchestrator.qualification.series import SeriesFSM, SeriesStateError, replay_ledger  # noqa: E402
from orchestrator.qualification.t126_driver import (  # noqa: E402
    ActiveProcessGroups,
    AttestationError,
    MemberRunError,
    RC_ATTESTATION,
    MonotonicEnvelope,
    QualificationDriverError,
    run_series,
)
from orchestrator.qualification import t126_driver  # noqa: E402
from test_schema_v2 import _valid_document  # noqa: E402


def test_t452_attest_preserves_intentional_fail_closed_behavior(monkeypatch, tmp_path):
    """[T-452] wave では意図的に現挙動を保存した。修正はユーザー裁定待ちの別タスク。"""
    calibration = schema_v2.validate_calibration_v2(_valid_document())
    raw = env_attestation.profile_to_dict(calibration.attestation_profile)
    del raw["effective_clock"]["tolerance_pct"]
    observed = env_attestation.normalize_observed_profile(raw)
    verified = SimpleNamespace(
        calibration=calibration,
        attestation_profile_sha256=env_attestation.profile_sha256(
            calibration.attestation_profile,
        ),
    )
    monkeypatch.setattr(
        t126_driver.env_attestation, "load_verified_calibration",
        lambda _contract, _root: verified,
    )
    monkeypatch.setattr(t126_driver.env_attestation, "probe", lambda: observed)

    with pytest.raises(QualificationDriverError, match="AttestationError"):
        t126_driver._attest(tmp_path, object())

def test_qualification_entry_constructs_run_context_for_live_member_build():
    source = (_ROOT / "orchestrator/qualification/t126_driver.py").read_text(
        encoding="utf-8"
    )
    assert "build_run_context(" in source
    assert "build_context=build_context" in source
    assert "BuildAdmission(" not in source


def test_qualification_policy_rejects_unadmitted_coder_before_build_spy(tmp_path):
    _, capability, layout, _ = _fsm(tmp_path)
    sink = QualificationEventSink(
        capability, layout, round_index=1, role="subject")
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(sink)
    pegasus_authorization = env_contract.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    genome = Genome("silo", {"BACK_OFF": 1})
    perf = pipeline.PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        }, extime=3, reps=5,
    )
    dirty = campaign_fixtures._source_evidence(
        genome, "d706650", src_token="2" * 64,
        source_root=str(tmp_path / "dirty-coder-source"),
    )
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    builds = []
    original_source_digest = pipeline.source_digest
    monkey_source_digest = type("SourceDigestSpy", (), {
        "STOCK": pipeline.source_digest.STOCK,
        "resolve_evidence": staticmethod(lambda *_args, **_kwargs: dirty),
    })
    original_build_v2 = pipeline.buildcache.build_v2
    pipeline.source_digest = monkey_source_digest
    pipeline.buildcache.build_v2 = lambda *_args, **_kwargs: builds.append(_kwargs)
    try:
        result = pipeline.evaluate(
            genome, layout, "pegasus", "d706650", perf, 2100, numactl=(),
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload())
            ],
            do_bench=True, do_settle=True, src_token=dirty.src_token,
            cache_root=str(tmp_path / "cache"), bench_max_rounds=1,
            env_contract=pegasus, authorization_contract=pegasus_authorization,
            record_rep_returncodes=True,
            qualification_policy=policy, log=lambda *_: None,
            build_context=context,
        )
    finally:
        pipeline.source_digest = original_source_digest
        pipeline.buildcache.build_v2 = original_build_v2
    assert result.aborted and not result.certified
    assert builds == []
    records = load_jsonl_strict(
        layout.attempt_dir / "rounds/0001/subject/evaluation-events.jsonl"
    )
    assert [row["evaluation_stage"] for row in records] == [
        "qualification_build_start",
        "qualification_evaluation_rejected",
    ]
    abort_payload = json.loads(records[-1]["payload"]["canonical_json"])
    assert abort_payload["reason"] == "admission-error"
    assert abort_payload["error"].startswith("BuildAdmissionError:")


def test_qualification_policy_missing_context_is_separate_signature_error(tmp_path):
    _, capability, layout, _ = _fsm(tmp_path)
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(
        QualificationEventSink(
            capability, layout, round_index=1, role="subject",
        )
    )
    pegasus_authorization = env_contract.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    perf = pipeline.PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        },
    )
    with pytest.raises(TypeError, match="build_context"):
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), layout, "pegasus", "deadbeef",
            perf, 2100, numactl=(), env_contract=pegasus,
            authorization_contract=pegasus_authorization,
            qualification_policy=policy, build_context=None,
        )
    assert not (
        layout.attempt_dir / "rounds/0001/subject/evaluation-events.jsonl"
    ).exists()


def test_qualification_stock_source_reaches_build_with_exact_class(
        tmp_path, monkeypatch):
    _, capability, layout, _ = _fsm(tmp_path)
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(
        QualificationEventSink(
            capability, layout, round_index=1, role="subject",
        )
    )
    pegasus_authorization = env_contract.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    genome = Genome("silo", {"BACK_OFF": 1})
    perf = pipeline.PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        }, extime=3, reps=5,
    )
    stock = campaign_fixtures._source_evidence(
        genome, "511c953", source_root=str(tmp_path / "clean-stock-source"),
    )
    seen = []

    monkeypatch.setattr(
        pipeline.source_digest, "resolve_evidence",
        lambda *_args, **_kwargs: stock,
    )

    def stop_at_build(*_args, **kwargs):
        seen.append(kwargs["admission"].provenance)
        raise RuntimeError("stop after stock admission")

    monkeypatch.setattr(pipeline.buildcache, "build_v2", stop_at_build)
    # resolve_evidence seam は下の任意 token を読まず、stock evidence の commit だけが
    # build_admission.CURRENT_PIN 比較へ届く。
    result = pipeline.evaluate(
        genome, layout, "pegasus", "d706650", perf, 2100, numactl=(),
        extra_correctness=[
            (pipeline.S2_TAG, pipeline.s2_correctness_workload())
        ],
        do_bench=True, do_settle=True, src_token=stock.src_token,
        cache_root=str(tmp_path / "cache"), bench_max_rounds=1,
        env_contract=pegasus, authorization_contract=pegasus_authorization,
        record_rep_returncodes=True,
        qualification_policy=policy, log=lambda *_: None,
        build_context=build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP),
    )
    assert result.aborted and not result.certified
    assert seen == [BuildProvenance.STOCK_BASELINE]


def _fsm(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    root = QualificationRoot(repo)
    capability = root.issue()
    layout = create_attempt(
        root, capability, series_id="a" * 64, attempt_id="b" * 64)
    identity = {
        "qualification_series_id": "a" * 64,
        "qualification_attempt_id": "b" * 64,
        "pbs_job_id": "123.server",
        "host": "pegasus",
        "boot_id": "boot",
        "controller_pid": 123,
    }
    protocol = load_protocol()
    return protocol, capability, layout, SeriesFSM(
        capability, layout.ledger_relpath, identity, protocol,
        wall_clock_ns=iter(range(1000, 2000)).__next__,
        monotonic_ns=iter(range(2000, 3000)).__next__,
    )


def _evidence(role: str):
    return {"path": f"{role}.jsonl", "size": 1, "sha256": "c" * 64}


def test_fsm_replay_rejects_mixed_identity_and_terminal_suffix(tmp_path):
    protocol, _, _, fsm = _fsm(tmp_path)
    fsm.open()
    order = fsm.open_round(1)
    for role in order:
        fsm.member_terminal(
            1, role, 90.0 if role == "subject" else 100.0, _evidence(role))
    assert fsm.round_terminal(
        1, subject_median_tps=90.0, reference_median_tps=100.0) == "continuing"
    events = list(fsm.events)
    mixed = [dict(row) for row in events]
    mixed[-1] = dict(mixed[-1])
    mixed[-1]["identity"] = dict(mixed[-1]["identity"], host="other")
    with pytest.raises(SeriesStateError, match="mixed"):
        replay_ledger(mixed, protocol)

    fsm.wait_satisfied(1, 1800.0)
    order = fsm.open_round(2)
    for role in order:
        fsm.member_terminal(
            2, role, 90.0 if role == "subject" else 100.0, _evidence(role))
    assert fsm.round_terminal(
        2, subject_median_tps=90.0, reference_median_tps=100.0
    ) == "lower_boundary"
    fsm.terminal(2)
    with pytest.raises(SeriesStateError, match="suffix"):
        fsm.terminal(2)


def test_driver_enforces_round_gap_attestation_and_reservation_order(tmp_path):
    protocol, _, _, fsm = _fsm(tmp_path)
    calls = []

    def member(round_index, role):
        calls.append(("member", round_index, role))
        return {
            "median_tps": 90.0 if role == "subject" else 100.0,
            "evidence_ref": _evidence(role),
            "terminal_monotonic": 0.0,
        }

    monotonic = iter((0.0, 1800.0))
    outcome = run_series(
        fsm=fsm, protocol=protocol, member_runner=member,
        attestation_fn=lambda stage, round_index: calls.append(
            ("attest", stage, round_index)) or {"status": "accepted"},
        reservation_recheck=lambda required: calls.append(("reserve", required)),
        sleep_fn=lambda seconds: calls.append(("sleep", seconds)),
        monotonic_fn=monotonic.__next__,
    )
    assert outcome["terminal"] == "lower_boundary"
    assert outcome["bits"] == [0, 0]
    assert ("sleep", 1800.0) in calls
    assert [row for row in calls if row[0] == "attest"] == [
        ("attest", "pre-round", 1),
        ("attest", "pre-round", 2),
        ("attest", "post-series", None),
    ]
    assert len([row for row in calls if row[0] == "reserve"]) == 2


def test_driver_rejects_immediately_without_running_second_member(tmp_path):
    protocol, _, _, fsm = _fsm(tmp_path)
    roles = []

    def reject_first(round_index, role):
        roles.append(role)
        raise MemberRunError("anomaly", {"anomalies": 1})

    with pytest.raises(MemberRunError, match="anomaly"):
        run_series(
            fsm=fsm, protocol=protocol, member_runner=reject_first,
            attestation_fn=lambda *_: {"status": "accepted"},
            reservation_recheck=lambda _: None,
        )
    assert len(roles) == 1
    assert fsm.replay.state == "rejected"
    assert fsm.replay.observations_recorded == 0


@pytest.mark.parametrize(
    ("bits", "terminal"),
    [
        ((0, 0), "lower_boundary"),
        ((1, 1, 1, 1), "upper_boundary"),
        ((0, 1, 1, 0, 1, 1, 1, 0), "indeterminate"),
    ],
)
def test_fsm_clean_terminal_positive_controls(tmp_path, bits, terminal):
    protocol, _, _, fsm = _fsm(tmp_path)

    def member(round_index, role):
        bit = bits[round_index - 1]
        return {
            "median_tps": (104.0 if bit else 100.0)
            if role == "subject" else 100.0,
            "evidence_ref": _evidence(role),
            "terminal_monotonic": 0.0,
        }

    outcome = run_series(
        fsm=fsm, protocol=protocol, member_runner=member,
        attestation_fn=lambda *_: {"status": "accepted"},
        reservation_recheck=lambda _: None,
        sleep_fn=lambda _: None,
        monotonic_fn=lambda: 1800.0,
    )
    assert outcome["terminal"] == terminal
    assert outcome["bits"] == list(bits)
    assert fsm.replay.state == "terminal"


def test_attestation_failure_is_terminal_reject_with_exact_rc(tmp_path):
    protocol, _, _, fsm = _fsm(tmp_path)

    def reject_attestation(*_):
        raise AttestationError("mismatch")

    with pytest.raises(AttestationError) as exc_info:
        run_series(
            fsm=fsm, protocol=protocol,
            member_runner=lambda *_: pytest.fail("member must not start"),
            attestation_fn=reject_attestation,
            reservation_recheck=lambda _: None,
        )
    assert exc_info.value.rc == RC_ATTESTATION
    assert fsm.replay.state == "rejected"
    assert fsm.replay.observations_recorded == 0


def test_exact_pegasus_empty_numactl_opt_in_emits_nonformal_evidence(tmp_path):
    protocol, capability, layout, _ = _fsm(tmp_path)
    sink = QualificationEventSink(
        capability, layout, round_index=1, role="subject")
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(sink)
    pegasus_authorization = env_contract.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    perf = pipeline.PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        },
        extime=3, reps=5,
    )
    with campaign_fixtures._mock_pipeline(certified=True) as calls:
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), layout, "pegasus", "deadbeef",
            perf, 2100, numactl=(),
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload())
            ],
            do_bench=True, do_settle=True, src_token="stock",
            cache_root=str(tmp_path / "cache"), bench_max_rounds=1,
            env_contract=pegasus, authorization_contract=pegasus_authorization,
            record_rep_returncodes=True,
            qualification_policy=policy, log=lambda *_: None,
            build_context=campaign_fixtures._BUILD_CONTEXT,
        )
    assert result.certified and not result.aborted
    records = load_jsonl_strict(
        layout.attempt_dir / "rounds/0001/subject/evaluation-events.jsonl")
    admitted = validate_member_evidence(
        records, expected_role="subject", expected_round=1)
    assert admitted["verify_order"] == ["legacy", "s2"]
    assert calls.lock_enters == 2
    assert calls.competition_probes == 2
    assert not (layout.attempt_dir / "runs/wal.jsonl").exists()


def test_m4a_producer_settled_gate_rejects_before_terminal_commit(
        tmp_path, monkeypatch):
    _, capability, layout, _ = _fsm(tmp_path)
    sink = QualificationEventSink(
        capability, layout, round_index=1, role="subject")
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(sink)
    pegasus_authorization = env_contract.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    perf = pipeline.PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        }, extime=3, reps=5,
    )
    with campaign_fixtures._mock_pipeline(certified=True):
        monkeypatch.setattr(pipeline, "settle", lambda: {"settled": False})
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), layout, "pegasus", "deadbeef",
            perf, 2100, numactl=(),
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload())
            ],
            do_bench=True, do_settle=True, src_token="stock",
            cache_root=str(tmp_path / "cache"), bench_max_rounds=1,
            env_contract=pegasus, authorization_contract=pegasus_authorization,
            record_rep_returncodes=True,
            qualification_policy=policy, log=lambda *_: None,
            build_context=campaign_fixtures._BUILD_CONTEXT,
        )
    assert result.aborted is True
    stages = [
        row["evaluation_stage"] for row in load_jsonl_strict(
            layout.attempt_dir
            / "rounds/0001/subject/evaluation-events.jsonl")
    ]
    assert "qualification_evaluation_terminal" not in stages
    assert stages[-1] == "qualification_evaluation_rejected"


@pytest.mark.parametrize(
    "bad_numactl",
    [None, [], ("numactl", "--interleave=all")],
)
def test_qualification_opt_in_rejects_nonexact_numactl_before_writes(
        tmp_path, bad_numactl):
    protocol, capability, layout, _ = _fsm(tmp_path)
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(
        QualificationEventSink(
            capability, layout, round_index=1, role="subject"))
    pegasus_authorization = env_contract.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    perf = pipeline.PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        },
    )
    with pytest.raises(ValueError, match="exactly match"):
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), layout, "pegasus", "deadbeef",
            perf, 2100, numactl=bad_numactl,
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload())
            ],
            src_token="stock", bench_max_rounds=1, env_contract=pegasus,
            authorization_contract=pegasus_authorization,
            record_rep_returncodes=True, qualification_policy=policy,
            build_context=campaign_fixtures._BUILD_CONTEXT,
        )
    assert not (
        layout.attempt_dir / "rounds/0001/subject/evaluation-events.jsonl"
    ).exists()


def test_exact_sink_layout_capability_chain_rejects_laundering_before_write(
        tmp_path):
    _, capability, layout, _ = _fsm(tmp_path)

    class DuckSink:
        def emit(self, *_args):
            raise AssertionError("duck sink must never receive a write")

    with pytest.raises(TypeError, match="exact QualificationEventSink"):
        pipeline.QualificationPipelinePolicy.t126_pegasus(DuckSink())
    with pytest.raises(TypeError, match="issued"):
        QualificationLayout(layout.root, layout.attempt_id, (1, 2), object(), object())
    with pytest.raises(AttributeError, match="immutable"):
        capability._root = tmp_path / "laundered"

    sink = QualificationEventSink(
        capability, layout, round_index=1, role="subject")
    for name, value in (
            ("_capability", object()), ("_layout", object()),
            ("_round_index", 2), ("_role", "reference"),
            ("_relative", "attempts/other/evaluation-events.jsonl")):
        with pytest.raises(AttributeError, match="immutable"):
            setattr(sink, name, value)
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(sink)
    pegasus_authorization = env_contract.authorize("pegasus")
    pegasus = pegasus_authorization.contract
    perf = pipeline.PerfConfig(
        records=1_000_000, threads=48,
        workload={
            "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
            "ycsb_rmw": "0", "ycsb_max_ope": "10",
        }, extime=3, reps=5,
    )
    with pytest.raises(QualificationArtifactError, match="layout"):
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}), object(), "pegasus", "deadbeef",
            perf, 2100, numactl=(),
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload())
            ],
            do_bench=True, do_settle=True, src_token="stock",
            bench_max_rounds=1, env_contract=pegasus,
            authorization_contract=pegasus_authorization,
            record_rep_returncodes=True, qualification_policy=policy,
            build_context=campaign_fixtures._BUILD_CONTEXT,
        )
    assert not (
        layout.attempt_dir / "rounds/0001/subject/evaluation-events.jsonl"
    ).exists()


def test_sink_rejects_capability_ancestor_replacement_before_first_write(
        tmp_path):
    _, capability, layout, _ = _fsm(tmp_path)
    sink = QualificationEventSink(
        capability, layout, round_index=1, role="subject")
    env_dir = layout.root.parents[2]
    moved = layout.root.parents[4] / "moved-env"
    env_dir.rename(moved)
    env_dir.symlink_to(moved, target_is_directory=True)
    with pytest.raises(QualificationArtifactError, match="ancestor"):
        sink.emit(
            layout, "variant", "build_start", "pegasus", {"genome": "g"})
    assert not (
        moved / "pegasus/qualification/t126/attempts"
        / layout.attempt_id / "rounds").exists()


def test_active_process_group_cleanup_kills_real_child_and_grandchild():
    pid = os.fork()
    if pid == 0:
        os.setsid()
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        grandchild = os.fork()
        if grandchild == 0:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            time.sleep(30)
            os._exit(0)
        time.sleep(30)
        os._exit(0)
    supervisor = ActiveProcessGroups(1.0)
    with pytest.raises(RuntimeError, match="fault"):
        with supervisor:
            supervisor.add(pid)
            time.sleep(0.05)
            raise RuntimeError("fault")
    with pytest.raises(ProcessLookupError):
        os.killpg(pid, 0)


@pytest.mark.parametrize("sig", [signal.SIGTERM, signal.SIGHUP])
def test_actual_term_hup_handler_cleans_descendant_process_group(sig):
    code = """
import os,signal,sys,time
from orchestrator.qualification.t126_driver import ActiveProcessGroups
signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGTERM,signal.SIGHUP})
ready_fd=int(sys.argv[2])
with ActiveProcessGroups(0.2) as groups:
    child=os.fork()
    if child==0:
        os.setsid()
        grandchild=os.fork()
        if grandchild==0:
            time.sleep(30)
            os._exit(0)
        os.write(ready_fd,b'1')
        time.sleep(30)
        os._exit(0)
    groups.add(child)
    print(child,flush=True)
    signal.pause()
"""
    ready_read, ready_write = os.pipe()
    process = subprocess.Popen(
        [sys.executable, "-c", code, str(int(sig)), str(ready_write)],
        cwd=_ROOT, env={**os.environ, "PYTHONPATH": str(_ROOT)},
        pass_fds=(ready_write,), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True)
    os.close(ready_write)
    pgid = None
    cleanup_verified = False
    try:
        readable, _, _ = select.select([ready_read], [], [], 5.0)
        assert readable, "process group readiness handshake timed out"
        assert os.read(ready_read, 1) == b"1"
        assert process.stdout is not None
        pgid = int(process.stdout.readline().strip())
        os.kill(process.pid, sig)
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode != 0, stderr
        assert stdout == ""
        with pytest.raises(ProcessLookupError):
            os.killpg(pgid, 0)
        cleanup_verified = True
    finally:
        os.close(ready_read)
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
        if not cleanup_verified and pgid is not None:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def test_single_monotonic_envelope_rejects_gap_that_exceeds_wmax(tmp_path):
    protocol, _, _, fsm = _fsm(tmp_path)
    now = {"ns": 0}
    envelope = MonotonicEnvelope(
        started_ns=0, deadline_ns=29100 * 1_000_000_000,
        wmax_s=29100, monotonic_ns=lambda: now["ns"])

    def member(_round_index, role):
        now["ns"] = (29100 - 600 - 10) * 1_000_000_000
        return {
            "median_tps": 90.0 if role == "subject" else 100.0,
            "evidence_ref": _evidence(role),
            "terminal_monotonic": 0.0,
        }

    with pytest.raises(QualificationDriverError, match="gap|deadline"):
        run_series(
            fsm=fsm, protocol=protocol, member_runner=member,
            attestation_fn=lambda *_: {"status": "accepted"},
            reservation_recheck=lambda _: None,
            sleep_fn=lambda _: pytest.fail("sleep must not exceed Wmax"),
            monotonic_fn=lambda: 0.0,
            envelope=envelope,
        )


def test_live_envelope_cannot_be_reissued_by_driver_and_rejects_overrun():
    with pytest.raises(QualificationDriverError, match="external"):
        MonotonicEnvelope.from_environ({}, 29100)
    envelope = MonotonicEnvelope(
        started_ns=1, deadline_ns=29100 * 1_000_000_000 + 1,
        wmax_s=29100,
        monotonic_ns=lambda: 29100 * 1_000_000_000 + 2)
    with pytest.raises(QualificationDriverError, match="exceeded"):
        envelope.receipt()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
