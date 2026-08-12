from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from orchestrator.campaign.t810_preregistration import (
    APPROVAL_RECEIPT_SCHEMA_VERSION,
    PREREG_PATH,
    ApprovalReceipt,
    load_t810_preregistration,
)
from orchestrator.campaign.t810_validator import ValidationLineage
from tools.pegasus import t810_coordinator as C
from tools.pegasus import t810_harness_schema as S


H = "a" * 64
PREREG_SHA256 = "3052af20993481730a826ce08ee26289948f29836d43afb2d7c743cfdd12e404"
APPROVAL_ID = "fixture-stage1-review-t810-v1"
FIXTURE = Path(__file__).parent / "fixtures" / "t810" / "coordinator_qsub_success.json"


def _preregistration():
    return load_t810_preregistration(
        PREREG_PATH,
        approval_receipt=ApprovalReceipt(
            artifact_sha256=PREREG_SHA256,
            approval_id=APPROVAL_ID,
            schema_version=APPROVAL_RECEIPT_SCHEMA_VERSION,
        ),
    )
def _policy(hosts: list[str] | None = None, status: str = "ratified") -> dict:
    return {
        "schema_version": "t810-admission-policy/v1",
        "approved_hostnames": {
            "status": status,
            "hostnames": hosts or [f"node{i:02d}" for i in range(S.NODE_COUNT)],
        },
        "qsub": {"status": "ratified"},
        "budget": {"status": "ratified"},
        "limitations": ["fixture-policy-has-no-trust-root"],
    }
def _config(tmp_path: Path, *, ordinal: int = 1) -> dict:
    prereg = _preregistration()
    output = tmp_path / "output"
    work = tmp_path / "work"
    policy = _policy()
    slots = []
    for index in range(S.NODE_COUNT):
        slot_id = f"slot-{index:02d}"
        stdout = output / slot_id / "pbs.stdout.log"
        stderr = output / slot_id / "pbs.stderr.log"
        qsub = [
            "qsub", "-N", f"t810-{index:02d}", "-o", str(stdout),
            "-e", str(stderr), f"job-{index:02d}.pbs",
        ]
        slots.append({
            "slot_id": slot_id,
            "logical_request_id": f"logical-{index:02d}",
            "job_name": f"t810-{index:02d}", "qsub_argv": qsub,
            "wrapper_argv": ["python3.10", "/var/tmp/t810/package/wrapper.py"],
            "pbs_stdout_path": str(stdout), "pbs_stderr_path": str(stderr),
            "binary_source_path": "/var/tmp/t810/package/CCBench", "binary_sha256": H,
            "wrapper_path": "/var/tmp/t810/package/wrapper.py", "wrapper_sha256": H,
            "runner_policy_path": "/var/tmp/t810/package/policy.py",
            "runner_policy_sha256": H,
        })
    intent = {
        "schema_version": S.LAUNCH_INTENT_SCHEMA, "group_id": f"group-{ordinal}",
        "run_kind": "liveness", "attempt_ordinal": ordinal,
        "policy_sha256": S.canonical_sha256(policy),
        "preregistration_sha256": prereg.sha256, "prereg_approval_id": prereg.approval_id,
        "created_at": "2026-08-12T00:00:00Z", "node_count": S.NODE_COUNT,
        "round_count": S.ROUND_COUNT, "ready_timeout_seconds": S.READY_TIMEOUT_SECONDS,
        "start_spread_max_ns": S.START_SPREAD_MAX_NS,
        "work_root": str(work), "output_root": str(output), "slots": slots,
    }
    intent_sha = S.canonical_sha256(intent)
    return {
        "launch_intent": intent, "admission_policy": policy,
        "guard_receipt": {
            "schema_version": "guard/v1", "launch_intent_sha256": intent_sha,
            "decision": "allow",
        },
        "budget_receipt": {
            "schema_version": "budget/v1", "launch_intent_sha256": intent_sha,
            "admitted": True,
        },
        "release_nonce": "fixture-release-nonce",
        "manifest_created_at": "2026-08-12T00:00:01Z",
        "validator_kwargs": {},
    }
def _witness(config: dict, prereg=None, *, run_kinds=None) -> dict:
    prereg = prereg or _preregistration()
    return {
        "schema_version": S.LAUNCH_AUTHORIZATION_SCHEMA,
        "approval_id": prereg.approval_id,
        "preregistration_sha256": prereg.sha256,
        "policy_sha256": config["launch_intent"]["policy_sha256"],
        "run_kinds": run_kinds or ["liveness"],
        "issued_on": "2026-08-12", "nonce": "human-issued-fixture-witness",
    }
def _preview(config: dict, prereg):
    intent = config["launch_intent"]
    manifest = {
        "schema_version": S.GROUP_MANIFEST_SCHEMA, "group_id": intent["group_id"],
        "created_at": config["manifest_created_at"],
        "launch_intent_sha256": S.canonical_sha256(intent),
        "guard_receipt_sha256": S.canonical_sha256(config["guard_receipt"]),
        "budget_receipt_sha256": S.canonical_sha256(config["budget_receipt"]),
        "release_token_commitment": S.release_token_commitment(config["release_nonce"]),
    }
    return SimpleNamespace(
        manifest_sha256=S.canonical_sha256(manifest), launch_intent=intent,
        release_nonce=config["release_nonce"], preregistration=prereg,
    )
class RecordedScheduler:
    def __init__(self, fixture_path: Path, output_root: Path, manifest_path: Path):
        value = json.loads(fixture_path.read_text(encoding="utf-8"))
        assert value["schema_version"] == "t810-coordinator-fixture/v1"
        self.transcripts = []
        for raw in value["transcripts"]:
            item = deepcopy(raw)
            item["command_argv"] = [
                token.replace("$OUTPUT_ROOT", str(output_root)) for token in item["command_argv"]
            ]
            self.transcripts.append(item)
        self.manifest_path = manifest_path
        self.calls: list[list[str]] = []

    def __call__(self, argv, *, cwd, env):
        assert self.manifest_path.is_file(), "manifest must precede the first scheduler effect"
        assert cwd.endswith("/work")
        assert env == {}
        expected = self.transcripts[len(self.calls)]
        assert argv == expected["command_argv"]
        self.calls.append(list(argv))
        return subprocess.CompletedProcess(argv, expected["rc"], expected["stdout"], expected["stderr"])
def _prepared(tmp_path: Path):
    prereg = _preregistration()
    config = _config(tmp_path)
    prepared = C.prepare_group(config, prereg)
    scheduler = RecordedScheduler(FIXTURE, prepared.output_root, prepared.manifest_path)
    submission = C.submit_group(
        prepared, _witness(config, prereg), scheduler_run=scheduler,
        wall_clock=lambda: "2026-08-12T00:00:02Z",
    )
    return prereg, config, prepared, submission, scheduler
def _node_event(prepared, slot_id: str, event: str, payload: dict, sequence: int = 0) -> dict:
    index = int(slot_id[-2:])
    return {
        "schema_version": S.NODE_EVENT_SCHEMA,
        "group_manifest_sha256": prepared.manifest_sha256,
        "group_id": prepared.launch_intent["group_id"], "slot_id": slot_id,
        "logical_request_id": f"logical-{index:02d}",
        "pbs_request_id": f"810{index:02d}.server", "sequence": sequence,
        "event": event, "observed_at": "2026-08-12T00:00:03Z",
        "previous_event_sha256": None if sequence == 0 else H, "payload": payload,
    }
def _ready_events(prepared) -> list[dict]:
    events = []
    for index in range(S.NODE_COUNT):
        slot_id = f"slot-{index:02d}"
        qsub = prepared.launch_intent["slots"][index]["qsub_argv"]
        payload = {
            "assigned_hostname": f"node{index:02d}", "actual_hostname": f"node{index:02d}",
            "hardware": {"cpu_model": "x", "physical_cores": 48,
                         "hyperthreading": False, "memory": "128GiB", "numa_nodes": 4,
                         "cache": ["L3"], "frequency_policy": "performance"},
            "interpreter": {"executable": "/usr/bin/python3.10", "version": "3.10.1"},
            "competing_processes": [],
            "quiet_samples": [
                {"observed_at": f"sample-{sample}", "load_average_1m": 0.5}
                for sample in range(3)
            ],
            "binary_source_sha256": H, "binary_copy_sha256": H,
            "dependency_manifest_sha256": H, "module_list_sha256": H,
            "trace_symbols": [],
            "isolation_before": {"inventory_sha256": H, "competing_processes_sha256": H},
            "observed_submission_argv": list(qsub),
            "repo_absence": {"package_repo_free": True, "roots_repo_external": True,
                             "git_ancestor_absent": True, "pbs_workdir_repo_external": True},
            "passed": False, "reason_codes": [],
        }
        events.append(_node_event(prepared, slot_id, "preflight", payload))
    return events
def _release_sha(prepared) -> str:
    marker = {
        "schema_version": S.CONTROL_MARKER_SCHEMA,
        "group_manifest_sha256": prepared.manifest_sha256,
        "group_id": prepared.launch_intent["group_id"], "kind": "release",
        "published_at": "2026-08-12T00:00:04Z", "nonce": prepared.release_nonce,
    }
    return S.canonical_sha256(marker)
def _ack_events(prepared, release_sha: str) -> list[dict]:
    return [
        _node_event(prepared, f"slot-{index:02d}", "start_ack", {
            "release_marker_sha256": release_sha, "cancel_marker_absent": True,
            "ack_nonce": f"ack-{index:02d}",
        })
        for index in range(S.NODE_COUNT)
    ]
def _presence(prereg, state: str, completed: set[str] | None = None) -> dict[str, list[str]]:
    completed = completed or {f"slot-{i:02d}" for i in range(S.NODE_COUNT)}
    artifacts = prereg.projection["artifacts"]
    result = {}
    for index in range(S.NODE_COUNT):
        slot = f"slot-{index:02d}"
        paths = [f"{slot}/{name}" for name in artifacts["slots"]["always_files"]]
        paths.append(f"{slot}/{artifacts['slots']['conditional_node_receipt_file']}")
        if state in {"valid", "terminal_reduced"} or (
            state == "incomplete_after_start" and slot in completed
        ):
            paths.append(f"{slot}/{artifacts['slots']['conditional_measurements_file']}")
        result[slot] = sorted(paths)
    return result
def _completion_receipts(prepared, prereg, *, dropped: set[str] | None = None) -> list[dict]:
    dropped = dropped or set()
    actual = _presence(prereg, "terminal_reduced" if dropped else "valid")
    receipts = []
    for index in range(S.NODE_COUNT):
        slot = f"slot-{index:02d}"
        terminal_payload = {
            "state": "incomplete_after_start" if slot in dropped else "valid",
            "reason_codes": ["insufficient_completions"] if slot in dropped else ["all_jobs_complete"],
            "measurement_started": slot not in dropped,
            "completed_rounds": 0 if slot in dropped else S.ROUND_COUNT,
        }
        measurement = None
        if slot not in dropped:
            rounds = [
                {"index": round_id, "started_at": "a", "ended_at": "b",
                 "effective_clock": 2.0, "throughput": 3.0, "exit_code": 0}
                for round_id in range(1, S.ROUND_COUNT + 1)
            ]
            measurement = _node_event(prepared, slot, "measurement", {
                "rounds": rounds, "benchmark_rc": 0, "binary_after_sha256": H,
                "isolation_after": {"inventory_sha256": H, "competing_processes_sha256": H},
            })
        receipts.append({
            "slot_id": slot,
            "terminal_event": _node_event(prepared, slot, "terminal", terminal_payload),
            "measurement_event": measurement,
            "node_receipt_sha256": hashlib.sha256(slot.encode()).hexdigest(),
            "actual_presence": actual[slot],
        })
    return receipts
def test_prepare_group_dag_is_create_only_and_policy_hosts_are_ratified(tmp_path: Path) -> None:
    prereg, config, prepared, _, scheduler = _prepared(tmp_path)
    assert prepared.intent_path.is_file()
    assert prepared.manifest_path.is_file()
    assert len(scheduler.calls) == S.NODE_COUNT
    assert prepared.manifest["launch_intent_sha256"] == S.canonical_sha256(config["launch_intent"])
    assert prepared.manifest["release_token_commitment"] == S.release_token_commitment(config["release_nonce"])
    with pytest.raises(C.T810CoordinatorError, match="create-only"):
        C.prepare_group(config, prereg)
    denied = _config(tmp_path / "unratified")
    denied["admission_policy"]["approved_hostnames"]["status"] = "unratified"
    denied["launch_intent"]["policy_sha256"] = S.canonical_sha256(denied["admission_policy"])
    with pytest.raises(C.T810CoordinatorError, match="not ratified"):
        C.prepare_group(denied, prereg)
def test_cli_and_effect_entries_deny_missing_or_wrong_witness(tmp_path: Path) -> None:
    assert C.main(["--config", "absent", "--approval-receipt", "absent"]) == 2
    prereg = _preregistration()
    config = _config(tmp_path)
    prepared = C.prepare_group(config, prereg)
    bomb = lambda *args, **kwargs: pytest.fail("scheduler reached")
    with pytest.raises(C.T810CoordinatorError, match="witness"):
        C.submit_group(prepared, None, scheduler_run=bomb, wall_clock=lambda: "now")
    wrong = _witness(config, prereg, run_kinds=["main"])
    with pytest.raises(C.T810CoordinatorError, match="run_kind"):
        C.submit_group(prepared, wrong, scheduler_run=bomb, wall_clock=lambda: "now")
@pytest.mark.parametrize(
    ("mutation", "reason"),
    [("duplicate_host", "duplicate_hostname"), ("binary", "binary_copy_hash_mismatch"),
     ("argv", "submission_argv_mismatch"), ("quiet", "quiet_gate_failed")],
)
def test_ready_barrier_recomputes_raw_evidence(tmp_path: Path, mutation: str, reason: str) -> None:
    _, _, prepared, _, _ = _prepared(tmp_path)
    events = _ready_events(prepared)
    if mutation == "duplicate_host":
        events[-1]["payload"]["assigned_hostname"] = "node00"
        events[-1]["payload"]["actual_hostname"] = "node00"
    elif mutation == "binary":
        events[-1]["payload"]["binary_copy_sha256"] = "b" * 64
    elif mutation == "argv":
        events[-1]["payload"]["observed_submission_argv"].append("--extra")
    else:
        events[-1]["payload"]["quiet_samples"][-1]["load_average_1m"] = 1.0000001
    decision = C.evaluate_ready_barrier(prepared, events, elapsed_seconds=1199)
    assert decision.status == "cancel"
    assert reason in decision.reason_codes
def test_submission_must_be_complete_before_barrier_and_timeout_boundary(tmp_path: Path) -> None:
    prereg = _preregistration()
    config = _config(tmp_path)
    prepared = C.prepare_group(config, prereg)
    with pytest.raises(C.T810CoordinatorError, match="submission receipt"):
        C.evaluate_ready_barrier(prepared, [], elapsed_seconds=1200)
    scheduler = RecordedScheduler(FIXTURE, prepared.output_root, prepared.manifest_path)
    C.submit_group(prepared, _witness(config), scheduler_run=scheduler, wall_clock=lambda: "now")
    assert C.evaluate_ready_barrier(prepared, [], elapsed_seconds=1199.999).status == "waiting"
    timed_out = C.evaluate_ready_barrier(prepared, [], elapsed_seconds=1200)
    assert timed_out.status == "cancel" and timed_out.reason_codes == ("ready_timeout",)
def test_release_commitment_cancel_recheck_and_create_only(tmp_path: Path) -> None:
    prereg, config, prepared, _, _ = _prepared(tmp_path)
    witness = _witness(config, prereg)
    _, release_sha = C.publish_release(
        prepared, witness, wall_clock=lambda: "2026-08-12T00:00:04Z",
    )
    assert C.release_is_still_active(prepared, release_sha)
    C.publish_cancel(prepared, witness, ["cancel_marker_observed"], wall_clock=lambda: "later")
    assert not C.release_is_still_active(prepared, release_sha)
    with pytest.raises(C.T810CoordinatorError, match="create-only"):
        C.publish_cancel(prepared, witness, ["cancel_marker_observed"], wall_clock=lambda: "again")
    marker = json.loads(prepared.release_path.read_text())
    marker["nonce"] = "not-the-preimage"
    with pytest.raises(S.T810SchemaError, match="preimage"):
        S.validate_control_marker(
            marker, expected_release_token_commitment=prepared.manifest["release_token_commitment"],
        )
@pytest.mark.parametrize(
    ("latency", "accepted"),
    [(S.START_SPREAD_MAX_NS - 1, True), (S.START_SPREAD_MAX_NS, True),
     (S.START_SPREAD_MAX_NS + 1, False)],
)
def test_start_spread_boundary_uses_only_coordinator_receipt_times(
    tmp_path: Path, latency: int, accepted: bool,
) -> None:
    _, _, prepared, _, _ = _prepared(tmp_path)
    release_sha = _release_sha(prepared)
    events = _ack_events(prepared, release_sha)
    received = [(event, 100 + (latency if index == S.NODE_COUNT - 1 else 0))
                for index, event in enumerate(events)]
    decision = C.evaluate_start_acks(
        prepared, received, release_marker_sha256=release_sha, release_published_ns=100,
    )
    assert decision.accepted is accepted
    assert decision.spread_ns == latency
    assert decision.latency_ns_by_slot["slot-12"] == latency
def test_ack_marker_mismatch_duplicate_unknown_and_missing_are_rejected(tmp_path: Path) -> None:
    _, _, prepared, _, _ = _prepared(tmp_path)
    release_sha = _release_sha(prepared)
    events = _ack_events(prepared, release_sha)
    events[0]["payload"]["release_marker_sha256"] = "b" * 64
    duplicate = deepcopy(events[1])
    unknown = deepcopy(events[2])
    unknown["slot_id"] = "slot-99"
    decision = C.evaluate_start_acks(
        prepared,
        [(event, 100) for event in events[:-1] + [duplicate, unknown]],
        release_marker_sha256=release_sha, release_published_ns=100,
    )
    assert {"release-marker-mismatch", "ack-duplicate", "ack-unknown-slot", "ack-missing"} <= set(decision.reason_codes)
@pytest.mark.parametrize(
    ("drop_count", "state"),
    [(0, "valid"), (1, "terminal_reduced"), (2, "incomplete_after_start")],
)
def test_completion_state_rows_and_exact_n_receipts(tmp_path: Path, drop_count: int, state: str) -> None:
    prereg, _, prepared, _, _ = _prepared(tmp_path)
    dropped = {f"slot-{S.NODE_COUNT - index - 1:02d}" for index in range(drop_count)}
    receipts = _completion_receipts(prepared, prereg, dropped=dropped)
    terminal = C.verify_completion(
        prepared, receipts, release_event_sha256=H, start_spread_ns=1,
        pre_validator_receipt_sha256=H, post_validator_receipt_sha256=H,
    )
    assert terminal["state"] == state
    assert terminal["retry_allowed"] is False
def test_completion_rejects_orphan_unknown_duplicate_and_receiptless_submission(tmp_path: Path) -> None:
    prereg, _, prepared, _, _ = _prepared(tmp_path)
    receipts = _completion_receipts(prepared, prereg)
    receipts.pop()
    receipts.append(deepcopy(receipts[0]))
    receipts.append({**deepcopy(receipts[1]), "slot_id": "slot-99"})
    with pytest.raises(C.T810CoordinatorError, match="orphan, duplicate, unknown, or missing"):
        C.verify_completion(
            prepared, receipts, release_event_sha256=H, start_spread_ns=1,
            pre_validator_receipt_sha256=H, post_validator_receipt_sha256=H,
        )
def test_frozen_boundary_reason_table_and_retry_rows_are_all_used() -> None:
    for (boundary, reason), expected in S.BOUNDARY_REASON_TO_STATE.items():
        assert S.classify_terminal_state(boundary, reason) == expected
    for state in S.TERMINAL_STATES:
        assert S.retry_allowed(state, 1) is (state == "pre_release_invalid")
        assert S.retry_allowed(state, 2) is False
def test_authorized_production_core_uses_same_validator_twice_and_dormant_prereg(
    tmp_path: Path,
) -> None:
    prereg = _preregistration()
    config = _config(tmp_path)
    preview = _preview(config, prereg)
    ready = _ready_events(preview)
    release_sha = _release_sha(preview)
    acks = _ack_events(preview, release_sha)
    completions = _completion_receipts(preview, prereg)
    config.update({
        "ready_events": ready, "ready_elapsed_seconds": 10,
        "ack_events": acks, "completion_receipts": completions,
        "validator_kwargs": {"attempt_nonce": "attempt-1", "pre_invocation_nonce": "pre-1"},
    })
    calls = []

    def validator(**kwargs):
        assert kwargs["preregistration"] is prereg
        assert prereg.run_authorized is False
        if calls:
            assert kwargs["previous_baseline"] is not None
        calls.append(kwargs["claimed_state"])
        if len(calls) == 1:
            lineage = ValidationLineage(prereg.sha256, prereg.approval_id, "attempt-1", "pre-1", H, H, H)
            return SimpleNamespace(ok=True, baseline="baseline", baseline_digest=H,
                                   lineage=lineage, terminal_state="pre_release_invalid")
        return {"ok": True, "call": 2}

    actual_output = Path(config["launch_intent"]["output_root"])
    scheduler = RecordedScheduler(
        FIXTURE, actual_output, actual_output / "group-manifest.json",
    )
    times = iter([0, 100] + [100 + (i * S.START_SPREAD_MAX_NS // 12) for i in range(13)])
    result = C._coordinate_authorized(
        config, prereg, _witness(config, prereg), scheduler_run=scheduler,
        clock_ns=lambda: next(times),
        wall_clock=lambda: "2026-08-12T00:00:04Z", validator=validator,
    )
    assert result.terminal_state["state"] == "valid"
    assert calls == ["pre_release_invalid", "valid"]
    assert len(scheduler.calls) == S.NODE_COUNT
    assert result.prepared.terminal_path.is_file()
    events = [S.parse_json(line) for line in result.prepared.coordinator_receipt_path.read_bytes().splitlines()]
    acks_recorded = [event for event in events if event["event"] == "start_ack_received"]
    assert len(acks_recorded) == S.NODE_COUNT
    assert max(event["details"]["latency_ns"] for event in acks_recorded) == S.START_SPREAD_MAX_NS
