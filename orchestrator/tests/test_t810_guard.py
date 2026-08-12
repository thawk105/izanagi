from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess

import pytest

from tools.pegasus import t810_guard as G
from tools.pegasus import t810_harness_schema as S


FIXTURES = Path(__file__).parent / "fixtures" / "t810"
H = "a" * 64
PREREG = "b" * 64


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _policy(*, resolved: bool = True) -> dict:
    return {
        "parallel_guard": {
            "a_series_identity": {
                "status": "resolved" if resolved else "unresolved",
                "field": "Job_Name",
                "pilot_patterns": [r"^t139-pilot-[0-9]+$"] if resolved else [],
                "main_patterns": [r"^t139-main-[0-9]+$"] if resolved else [],
            }
        }
    }


def _transcript(
    request_id: str, *, job_name: str, state: str = "Q", owner: str = "alice",
    host: str = "--",
) -> dict:
    return {
        "schema_version": S.QSTAT_F_TRANSCRIPT_SCHEMA,
        "captured_at": "2026-08-12T02:00:00Z",
        "request_id": request_id,
        "command_argv": ["qstat", "-f", request_id],
        "rc": 0,
        "stdout": (
            f"Job Id: {request_id}\n"
            f"    Job_Name = {job_name}\n"
            f"    Job_Owner = {owner}@nqsv\n"
            f"    job_state = {state}\n"
            "    queue = gen_S\n"
            f"    exec_host = {host}\n"
        ),
        "stderr": "",
    }


def _identity(request_id: str, job_name: str) -> dict:
    return {"pbs_request_id": request_id, "owner": "alice", "job_name": job_name}


def _evaluate(transcripts, *, phase="pre-submission", policy=None, identities=()):
    return G.evaluate_parallel_guard(
        transcripts, policy=policy or _policy(), phase=phase,
        launch_intent_sha256=H, expected_owner="alice",
        b_manifest_jobs=identities, created_at="2026-08-12T02:00:01Z",
    )


def _witness(policy_sha256: str, run_kind: str = "main") -> dict:
    return {
        "schema_version": S.LAUNCH_AUTHORIZATION_SCHEMA,
        "approval_id": "human-approval", "preregistration_sha256": PREREG,
        "policy_sha256": policy_sha256, "run_kinds": [run_kind],
        "issued_on": "2026-08-12", "nonce": "test-only-literal-witness",
    }


def test_saved_qstat_q_h_r_and_wrapped_exec_host():
    jobs = G.parse_qstat_f_transcripts(_load("guard_qhr.json"), expected_owner="alice")
    assert [job.state for job in jobs] == ["QUE", "HLD", "RUN"]
    assert jobs[2].execution_hosts == ("node01",)
    assert jobs[2].exec_host == "node01/0+node01/1+node01/2"


def test_saved_multiple_blocks_are_parsed_in_order():
    raw = _load("guard_cases.json")["multiple_blocks"]
    jobs = G.parse_qstat_jobs(
        raw, expected_owner="alice", expected_request_ids=["81011.nqsv", "81012.nqsv"],
    )
    assert [(job.request_id, job.state) for job in jobs] == [
        ("81011.nqsv", "QUE"), ("81012.nqsv", "RUN"),
    ]


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("duplicate_state", "duplicate-critical-field"),
        ("different_owner", "owner-mismatch"),
        ("missing_job_name", "missing-critical-field"),
    ],
)
def test_critical_ambiguity_invalidates_the_whole_snapshot(case: str, reason: str):
    with pytest.raises(G.T810GuardError, match=reason):
        G.parse_qstat_jobs(_load("guard_cases.json")[case], expected_owner="alice")


def test_request_id_mismatch_invalidates_snapshot():
    transcript = _transcript("81011.nqsv", job_name="t810")
    transcript["stdout"] = transcript["stdout"].replace("81011.nqsv", "99999.nqsv", 1)
    decision = _evaluate([transcript])
    assert decision.decision == "deny"
    assert decision.reason_codes == ("request-id-mismatch",)


def test_unknown_state_has_dedicated_deny_reason():
    raw = _load("guard_cases.json")["unknown_state"]
    transcript = _transcript("81011.nqsv", job_name="ordinary")
    transcript["stdout"] = raw
    decision = _evaluate([transcript])
    assert decision.decision == "deny"
    assert "unknown-job-state" in decision.reason_codes


def test_qstat_q_uses_its_separate_transcript_parser():
    queue = G.parse_qstat_queue(_load("guard_queue.json"), expected_queue="gen_S")
    assert queue.available
    assert (queue.queued, queue.running) == (2, 2)
    wrong = deepcopy(_load("guard_queue.json"))
    wrong["command_argv"] = ["qstat", "-f", "gen_S"]
    with pytest.raises(G.T810GuardError, match="invalid-transcript"):
        G.parse_qstat_queue(wrong, expected_queue="gen_S")


def test_unresolved_identity_denies_even_an_empty_snapshot():
    decision = _evaluate([], policy=_policy(resolved=False))
    assert decision.decision == "deny"
    assert decision.reason_codes == ("priority-identity-unresolved",)


@pytest.mark.parametrize(
    ("name", "is_a"),
    [("t139-pilot-7", True), ("t139-main-12", True), ("x-t139-main-12", False),
     ("t139-main-12-extra", False), ("t810-main-12", False)],
)
def test_resolved_identity_uses_only_anchored_pilot_and_main_names(name: str, is_a: bool):
    decision = _evaluate([_transcript("81011.nqsv", job_name=name)])
    assert ("a-series-active" in decision.reason_codes) is is_a
    assert bool(decision.a_series_jobs) is is_a


def test_second_phase_detects_a_series_arrival_after_first_phase_passed():
    first = _evaluate([])
    second = _evaluate(
        [_transcript("13901.nqsv", job_name="t139-main-1", state="R", host="node09/0")],
        phase="pre-release",
    )
    assert first.decision == "allow"
    assert second.decision == "deny"
    assert second.reason_codes == ("a-series-active",)


def test_pre_release_detects_b_identity_and_host_collisions():
    identities = [_identity("81011.nqsv", "b-one"), _identity("81012.nqsv", "b-two")]
    decision = _evaluate([
        _transcript("81011.nqsv", job_name="b-one", state="R", host="node03/0"),
        _transcript("81012.nqsv", job_name="wrong", state="R", host="node03/1"),
    ], phase="pre-release", identities=identities)
    assert decision.decision == "deny"
    assert set(decision.reason_codes) == {"b-identity-mismatch", "co-location-conflict"}
    assert decision.co_location_conflicts == ({
        "hostname": "node03", "pbs_request_ids": ["81011.nqsv", "81012.nqsv"],
    },)


def test_guard_receipt_exact_fields_bind_intent_and_machine_limitations():
    receipt = _evaluate([]).to_dict()
    assert set(receipt) == {
        "schema_version", "launch_intent_sha256", "phase", "policy_sha256",
        "snapshot_sha256", "a_series_identity_status", "a_series_jobs",
        "co_location_conflicts", "decision", "reason_codes", "b_request_ids",
        "withdrawal_actions", "limitations", "created_at",
    }
    assert receipt["launch_intent_sha256"] == H
    assert "snapshot-to-release-race-not-eliminated" in receipt["limitations"]
    assert "group_manifest_sha256" not in receipt


def _withdraw(
    decision, transcripts, identities, *, witness=True, rc=0, events=None,
):
    events = [] if events is None else events

    def cancel():
        events.append("cancel")

    def scheduler(argv):
        events.append(tuple(argv))
        return subprocess.CompletedProcess(argv, rc, "", "failure" if rc else "")

    receipt = G.withdraw_b_group(
        decision, fresh_transcripts=transcripts, b_manifest_jobs=identities,
        expected_owner="alice",
        authorization_witness=_witness(decision.policy_sha256) if witness else None,
        approval_id="human-approval", preregistration_sha256=PREREG,
        run_kind="main", publish_cancel=cancel, scheduler_run=scheduler,
        created_at="2026-08-12T02:00:02Z",
    )
    return receipt, events


def test_cancel_precedes_qdel_and_only_exact_queued_or_held_b_ids_are_withdrawn():
    identities = [_identity("81011.nqsv", "b-one"), _identity("81012.nqsv", "b-two")]
    transcripts = [
        _transcript("81011.nqsv", job_name="b-one", state="Q"),
        _transcript("81012.nqsv", job_name="b-two", state="H"),
    ]
    decision = _evaluate(transcripts, phase="pre-release", identities=identities)
    receipt, events = _withdraw(decision, transcripts, identities)
    assert events == ["cancel", ("qdel", "81011.nqsv"), ("qdel", "81012.nqsv")]
    assert receipt.decision == "withdrawn"
    assert all(item["identity_match"] and item["qdel_rc"] == 0
               for item in receipt.withdrawal_actions)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ("name", "qdel-identity-mismatch"),
        ("unknown", "qdel-identity-mismatch"),
        ("running", "qdel-identity-mismatch"),
    ],
)
def test_qdel_identity_or_state_mismatch_never_reaches_scheduler(change: str, reason: str):
    identity = [_identity("81011.nqsv", "b-one")]
    transcript = _transcript(
        "81011.nqsv", job_name="different" if change == "name" else "b-one",
        state="E" if change == "unknown" else "R" if change == "running" else "Q",
    )
    decision = _evaluate([transcript], phase="pre-release", identities=identity)
    receipt, events = _withdraw(decision, [transcript], identity)
    assert events == ["cancel"]
    assert reason in receipt.reason_codes
    assert receipt.withdrawal_actions[0]["qdel_argv"] == []


def test_qdel_owner_mismatch_invalidates_fresh_snapshot_without_scheduler_effect():
    identity = [_identity("81011.nqsv", "b-one")]
    transcript = _transcript("81011.nqsv", job_name="b-one", owner="mallory")
    decision = _evaluate([transcript], phase="pre-release", identities=identity)
    receipt, events = _withdraw(decision, [transcript], identity)
    assert events == ["cancel"]
    assert "qdel-identity-mismatch" in receipt.reason_codes
    assert receipt.withdrawal_actions == ()


def test_nonzero_qdel_rc_is_not_a_successful_withdrawal():
    identity = [_identity("81011.nqsv", "b-one")]
    transcript = _transcript("81011.nqsv", job_name="b-one", state="Q")
    decision = _evaluate([transcript], phase="pre-release", identities=identity)
    receipt, events = _withdraw(decision, [transcript], identity, rc=1)
    assert events[-1] == ("qdel", "81011.nqsv")
    assert receipt.decision == "deny"
    assert "qdel-failed" in receipt.reason_codes


def test_qdel_requires_launch_authorization_witness_at_effect_entry():
    identity = [_identity("81011.nqsv", "b-one")]
    transcript = _transcript("81011.nqsv", job_name="b-one", state="Q")
    decision = _evaluate([transcript], phase="pre-release", identities=identity)
    receipt, events = _withdraw(decision, [transcript], identity, witness=False)
    assert events == ["cancel"]
    assert receipt.decision == "deny"
    assert "launch-authorization-required" in receipt.reason_codes
