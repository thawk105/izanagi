from __future__ import annotations
from copy import deepcopy
import pytest
from tools.pegasus import t810_harness_schema as S
H = "a" * 64

def _intent() -> dict:
    slots = []
    for index in range(S.NODE_COUNT):
        out = f"/var/tmp/t810/out/slot-{index:02d}.out"
        err = f"/var/tmp/t810/out/slot-{index:02d}.err"
        slots.append({
            "slot_id": f"slot-{index:02d}", "logical_request_id": f"logical-{index}",
            "job_name": f"t810-{index}", "qsub_argv": ["qsub", "-o", out, "-e", err],
            "wrapper_argv": ["python3.10", "/var/tmp/t810/package/wrapper.py"],
            "pbs_stdout_path": out, "pbs_stderr_path": err,
            "binary_source_path": "/var/tmp/t810/package/CCBench",
            "binary_sha256": H, "wrapper_path": "/var/tmp/t810/package/wrapper.py",
            "wrapper_sha256": H, "runner_policy_path": "/var/tmp/t810/package/policy.py",
            "runner_policy_sha256": H,
        })
    return {
        "schema_version": S.LAUNCH_INTENT_SCHEMA, "group_id": "group-1",
        "run_kind": "liveness", "attempt_ordinal": 1, "policy_sha256": H,
        "preregistration_sha256": H, "prereg_approval_id": "approval-1",
        "created_at": "2026-08-12T00:00:00Z", "node_count": S.NODE_COUNT,
        "round_count": S.ROUND_COUNT, "ready_timeout_seconds": 1200,
        "start_spread_max_ns": 5_000_000_000, "work_root": "/var/tmp/t810/work",
        "output_root": "/var/tmp/t810/out", "slots": slots,
    }

def _manifest() -> dict:
    return {
        "schema_version": S.GROUP_MANIFEST_SCHEMA, "group_id": "group-1",
        "created_at": "2026-08-12T00:00:01Z", "launch_intent_sha256": H,
        "guard_receipt_sha256": H, "budget_receipt_sha256": H,
        "release_token_commitment": S.release_token_commitment("secret"),
    }

def _launch_authorization() -> dict:
    return {
        "schema_version": S.LAUNCH_AUTHORIZATION_SCHEMA, "approval_id": "approval-1",
        "preregistration_sha256": H, "policy_sha256": H,
        "run_kinds": ["builder", "liveness", "main"],
        "issued_on": "2026-08-12", "nonce": "authorization-nonce",
    }

def _node(event: str, payload: dict) -> dict:
    return {
        "schema_version": S.NODE_EVENT_SCHEMA, "group_manifest_sha256": H,
        "group_id": "group-1", "slot_id": "slot-00", "logical_request_id": "logical-0",
        "pbs_request_id": "123.server", "sequence": 0, "event": event,
        "observed_at": "2026-08-12T00:00:02Z", "previous_event_sha256": None,
        "payload": payload,
    }

def _preflight() -> dict:
    return {
        "assigned_hostname": "node01", "actual_hostname": "node01",
        "hardware": {"cpu_model": "x", "physical_cores": 48, "hyperthreading": False,
                     "memory": "128GiB", "numa_nodes": 4, "cache": ["L3"],
                     "frequency_policy": "performance"},
        "interpreter": {"executable": "/usr/bin/python3.10", "version": "3.10.1"},
        "competing_processes": [],
        "quiet_samples": [{"observed_at": f"t{i}", "load_average_1m": 0.2} for i in range(3)],
        "binary_source_sha256": H, "binary_copy_sha256": H,
        "dependency_manifest_sha256": H, "module_list_sha256": H, "trace_symbols": [],
        "isolation_before": {"inventory_sha256": H, "competing_processes_sha256": H},
        "observed_submission_argv": ["qsub", "-q", "default", "job.sh"],
        "repo_absence": {"package_repo_free": True, "roots_repo_external": True,
                         "git_ancestor_absent": True, "pbs_workdir_repo_external": True},
        "passed": True, "reason_codes": [],
    }

def _terminal(state: str = "valid", ordinal: int = 1) -> dict:
    slots = [f"slot-{index:02d}" for index in range(S.NODE_COUNT)]
    completed, dropped, reason = slots, [], "all_jobs_complete"
    if state == "terminal_reduced":
        completed, dropped, reason = slots[:-1], slots[-1:], "single_job_dropped"
    elif state == "pre_release_invalid":
        completed, dropped, reason = [], slots, "ready_timeout"
    elif state == "post_release_pre_measurement_invalid":
        completed, dropped, reason = [], slots, "ack-missing"
    expected = {slot: [f"nodes/{slot}.json"] for slot in slots}
    actual = deepcopy(expected)
    if state == "terminal_reduced":
        actual[dropped[0]] = ["nodes/dropout.json"]
    return {
        "schema_version": S.TERMINAL_STATE_SCHEMA, "group_manifest_sha256": H,
        "attempt_ordinal": ordinal, "state": state, "reason_codes": [reason],
        "release_event_sha256": None if state == "pre_release_invalid" else H,
        "start_spread_ns": None if state == "pre_release_invalid" else 10,
        "completed_slot_ids": completed, "dropped_slot_ids": dropped,
        "node_receipt_sha256_by_slot": {slot: None if state == "pre_release_invalid" else H for slot in slots},
        "expected_presence": expected, "actual_presence": actual, "presence_valid": True,
        "pre_validator_receipt_sha256": H,
        "post_validator_receipt_sha256": H,
        "retry_allowed": state == "pre_release_invalid" and ordinal == 1,
    }

def test_positive_dag_documents_and_scheduler_schemas() -> None:
    S.validate_launch_intent(_intent())
    S.validate_launch_authorization(_launch_authorization())
    S.validate_group_manifest(_manifest())
    requests = [{
        "slot_id": f"slot-{i:02d}", "logical_request_id": f"logical-{i}",
        "job_name": f"t810-{i}", "qsub_argv": ["qsub"], "qsub_rc": 0,
        "qsub_stdout": "", "qsub_stderr": "", "pbs_request_id": f"{i}.server",
    } for i in range(S.NODE_COUNT)]
    S.validate_submission_receipt({"schema_version": S.SUBMISSION_RECEIPT_SCHEMA,
        "group_manifest_sha256": H, "created_at": "now", "requests": requests})
    S.validate_control_marker({"schema_version": S.CONTROL_MARKER_SCHEMA,
        "group_manifest_sha256": H, "group_id": "group-1", "kind": "release",
        "published_at": "now", "nonce": "secret"},
        expected_release_token_commitment=_manifest()["release_token_commitment"])
    S.validate_control_marker({"schema_version": S.CONTROL_MARKER_SCHEMA,
        "group_manifest_sha256": H, "group_id": "group-1", "kind": "cancel",
        "published_at": "now", "reason_codes": ["ready_timeout"]})
    S.validate_qstat_f_transcript({"schema_version": S.QSTAT_F_TRANSCRIPT_SCHEMA,
        "captured_at": "now", "request_id": "1.server", "command_argv": ["qstat", "-f", "1.server"],
        "rc": 0, "stdout": "job_state = R", "stderr": ""})
    S.validate_qstat_q_transcript({"schema_version": S.QSTAT_Q_TRANSCRIPT_SCHEMA,
        "captured_at": "now", "command_argv": ["qstat", "-Q"], "rc": 0,
        "stdout": "queue", "stderr": ""})
    S.validate_qsub_transcript({"schema_version": S.QSUB_TRANSCRIPT_SCHEMA,
        "captured_at": "now", "slot_id": "slot-00", "command_argv": ["qsub", "job.sh"],
        "rc": 0, "stdout": "1.server", "stderr": "", "pbs_request_id": "1.server"})

def test_positive_node_event_payloads() -> None:
    isolation = {"inventory_sha256": H, "competing_processes_sha256": H}
    rounds = [{"index": 1, "started_at": "a", "ended_at": "b",
               "effective_clock": 2.1, "throughput": 3.2, "exit_code": 0}]
    payloads = {
        "preflight": _preflight(),
        "ready": {"preflight_event_sha256": H, "ready": True, "reason_codes": []},
        "start_ack": {"release_marker_sha256": H, "cancel_marker_absent": True, "ack_nonce": "ack"},
        "measurement": {"rounds": rounds, "benchmark_rc": 0, "binary_after_sha256": H,
                        "isolation_after": isolation},
        "terminal": {"state": "valid", "reason_codes": ["all_jobs_complete"],
                     "measurement_started": True, "completed_rounds": 10},
    }
    for event, payload in payloads.items():
        S.validate_node_event(_node(event, payload))

def test_positive_coordinator_event_payloads() -> None:
    details = {
        "manifest_committed": {"manifest_sha256": H},
        "ready_received": {"receipt_sha256": H, "accepted": True, "reason_codes": []},
        "release_published": {"marker_sha256": H},
        "start_ack_received": {"receipt_sha256": H, "received_monotonic_ns": 20,
                               "latency_ns": 10, "accepted": True, "reason_codes": []},
        "cancel_published": {"marker_sha256": H, "reason_codes": ["ready_timeout"]},
        "completion_received": {"receipt_sha256": H, "accepted": True, "reason_codes": []},
        "terminal_decided": {"terminal_state_sha256": H},
    }
    for event, payload in details.items():
        S.validate_coordinator_event({"schema_version": S.COORDINATOR_EVENT_SCHEMA,
            "group_manifest_sha256": H, "sequence": 0, "event": event, "wall_time": "now",
            "coordinator_monotonic_ns": 10,
            "slot_id": "slot-00" if event in {"ready_received", "start_ack_received", "completion_received"} else None,
            "previous_event_sha256": None, "details": payload})

def test_terminal_states_retry_and_dropped_exclusion() -> None:
    S.validate_terminal_state(_terminal())
    S.validate_terminal_state(_terminal("terminal_reduced"))
    S.validate_terminal_state(_terminal("pre_release_invalid", 1))
    S.validate_terminal_state(_terminal("pre_release_invalid", 2))
    assert S.retry_allowed("pre_release_invalid", 1)
    assert not S.retry_allowed("pre_release_invalid", 2)
    assert not S.retry_allowed("valid", 1)

def test_post_validator_receipt_is_required_for_pre_release_invalid() -> None:
    value = _terminal("pre_release_invalid")
    value["post_validator_receipt_sha256"] = None
    with pytest.raises(S.T810SchemaError, match="post_validator_receipt_sha256"):
        S.validate_terminal_state(value)

@pytest.mark.parametrize("reason", [
    "release-marker-mismatch", "ack-missing", "ack-unknown-slot", "ack-duplicate",
])
def test_ack_reason_codes_are_post_release_only(reason: str) -> None:
    value = _terminal("post_release_pre_measurement_invalid")
    value["reason_codes"] = [reason]
    S.validate_terminal_state(value)
    assert S.classify_terminal_state("post_release_pre_measurement", reason) == value["state"]
    with pytest.raises(S.T810SchemaError, match=r"\$\.reason_code"):
        S.classify_terminal_state("pre_release", reason)

def test_frozen_state_classification_all_rows() -> None:
    for (boundary, reason), state in S.BOUNDARY_REASON_TO_STATE.items():
        assert S.classify_terminal_state(boundary, reason) == state
    with pytest.raises(S.T810SchemaError, match=r"\$\.reason_code"):
        S.classify_terminal_state("pre_release", "trace_symbols_present")

@pytest.mark.parametrize("mutation", ["unknown", "missing", "nested_unknown", "bool_int",
                                      "noncanonical_path", "ordinal_zero", "ordinal_three", "non_str_key"])
def test_launch_intent_exact_rejections(mutation: str) -> None:
    value = _intent()
    if mutation == "unknown": value["extra"] = 1
    elif mutation == "missing": del value["group_id"]
    elif mutation == "nested_unknown": value["slots"][0]["extra"] = 1
    elif mutation == "bool_int": value["node_count"] = True
    elif mutation == "noncanonical_path": value["work_root"] = "/var/tmp/../tmp/t810"
    elif mutation == "ordinal_zero": value["attempt_ordinal"] = 0
    elif mutation == "ordinal_three": value["attempt_ordinal"] = 3
    else: value[1] = "bad"
    with pytest.raises(S.T810SchemaError, match=r"^\$"):
        S.validate_launch_intent(value)

@pytest.mark.parametrize("mutation", ["unknown", "missing", "unknown_run_kind", "duplicate_run_kind"])
def test_launch_authorization_exact_rejections(mutation: str) -> None:
    value = _launch_authorization()
    if mutation == "unknown": value["extra"] = 1
    elif mutation == "missing": del value["approval_id"]
    elif mutation == "unknown_run_kind": value["run_kinds"] = ["main", "other"]
    else: value["run_kinds"] = ["main", "main"]
    with pytest.raises(S.T810SchemaError, match=r"^\$"):
        S.validate_launch_authorization(value)

@pytest.mark.parametrize("argv", [[], ["qsub", 1]])
def test_observed_submission_argv_rejects_empty_or_non_string(argv: list) -> None:
    value = _node("preflight", _preflight())
    value["payload"]["observed_submission_argv"] = argv
    with pytest.raises(S.T810SchemaError, match="observed_submission_argv"):
        S.validate_node_event(value)

def test_legacy_submission_argv_match_is_an_unknown_field() -> None:
    value = _node("preflight", _preflight())
    value["payload"]["submission_argv_match"] = True
    with pytest.raises(S.T810SchemaError, match=r"submission_argv_match: unknown field"):
        S.validate_node_event(value)

@pytest.mark.parametrize(("field", "invalid"), [("accepted", 1), ("reason_codes", [1])])
def test_start_ack_received_rejects_invalid_decision_details(field: str, invalid: object) -> None:
    details = {"receipt_sha256": H, "received_monotonic_ns": 20, "latency_ns": 10,
               "accepted": True, "reason_codes": []}
    details[field] = invalid
    value = {"schema_version": S.COORDINATOR_EVENT_SCHEMA, "group_manifest_sha256": H,
             "sequence": 0, "event": "start_ack_received", "wall_time": "now",
             "coordinator_monotonic_ns": 10, "slot_id": "slot-00",
             "previous_event_sha256": None, "details": details}
    with pytest.raises(S.T810SchemaError, match=field):
        S.validate_coordinator_event(value)

@pytest.mark.parametrize("field", ["accepted", "reason_codes"])
def test_start_ack_received_requires_decision_details(field: str) -> None:
    details = {"receipt_sha256": H, "received_monotonic_ns": 20, "latency_ns": 10,
               "accepted": False, "reason_codes": ["ack-duplicate"]}
    del details[field]
    value = {"schema_version": S.COORDINATOR_EVENT_SCHEMA, "group_manifest_sha256": H,
             "sequence": 0, "event": "start_ack_received", "wall_time": "now",
             "coordinator_monotonic_ns": 10, "slot_id": "slot-00",
             "previous_event_sha256": None, "details": details}
    with pytest.raises(S.T810SchemaError, match=field):
        S.validate_coordinator_event(value)


def test_duplicate_key_commitment_and_start_permit_rejected() -> None:
    with pytest.raises(S.T810SchemaError, match="duplicate key"):
        S.parse_json('{"schema_version":"x","schema_version":"y"}')
    value = _manifest()
    value["release_token_commitment"] = "a" * 63
    with pytest.raises(S.T810SchemaError, match="release_token_commitment"):
        S.validate_group_manifest(value)
    with pytest.raises(S.T810SchemaError, match="kind"):
        S.validate_control_marker({"schema_version": S.CONTROL_MARKER_SCHEMA,
            "group_manifest_sha256": H, "group_id": "g", "kind": "start-permit",
            "published_at": "now"})


def test_canonical_digest_is_stable_and_bool_is_not_number() -> None:
    assert S.canonical_json_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}'
    assert S.canonical_sha256({"a": 1}) == S.sha256_bytes(b'{"a":1}')
    node = _node("preflight", _preflight())
    node["payload"]["quiet_samples"][0]["load_average_1m"] = True
    with pytest.raises(S.T810SchemaError, match="load_average_1m"):
        S.validate_node_event(node)
