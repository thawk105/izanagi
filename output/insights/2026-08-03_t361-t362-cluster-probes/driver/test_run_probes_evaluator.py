from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

import run_probes as subject
import signal_observer


def _split(
    *,
    observation: bool = True,
    hygiene: bool = True,
    accounting_available: bool = False,
    accounting_integrity_valid: bool | None = True,
    termination_cause_consistent: bool | None = True,
    accounting_unavailable_reason: str | None = None,
    termination_cause_evidence_source: str | None = None,
    cleanup_outcome: str = "safe",
    unsafe_reason: str | None = None,
) -> dict[str, object]:
    return subject._compose_split_v2_evaluation(
        observation_predicates={"fixture_observation": observation},
        hygiene_predicates={"fixture_hygiene": hygiene},
        accounting_available=accounting_available,
        accounting_integrity_valid=accounting_integrity_valid,
        termination_cause_consistent=termination_cause_consistent,
        accounting_unavailable_reason=accounting_unavailable_reason,
        termination_cause_evidence_source=termination_cause_evidence_source,
        probe_cleanup_outcome=cleanup_outcome,
        unsafe_reason=unsafe_reason,
    )


def _record(evaluation: dict[str, object], *, terminal: bool = True) -> dict[str, object]:
    return {
        **evaluation,
        "external_root_terminal_proven": terminal,
        "admissible": evaluation["observation_valid"],
    }


def _natural_qwait(request_id: str, *, returncode: int = 0) -> dict[str, object]:
    return {
        "argv": ["qwait", "-t", "4080", request_id],
        "returncode": returncode,
        "stdout": "",
        "stderr": "",
        "timed_out": False,
        "terminated_by_controller": False,
    }


def _write_saved_command(
    controller_root: Path,
    *,
    sequence: int,
    purpose: str,
    argv: list[str],
    returncode: int,
    stdout: bytes,
    stderr: bytes = b"",
    event: str | None = None,
) -> None:
    raw_root = controller_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    stdout_path = raw_root / f"{sequence:05d}-{purpose}.stdout.raw"
    stderr_path = raw_root / f"{sequence:05d}-{purpose}.stderr.raw"
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    receipt = {
        "schema": subject.SCHEMA,
        "sequence": sequence,
        "purpose": purpose,
        "argv": argv,
        "returncode": returncode,
        "timed_out": False,
        "terminated_by_controller": False,
        "stdout_path": str(stdout_path.relative_to(controller_root)),
        "stderr_path": str(stderr_path.relative_to(controller_root)),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
    }
    if event is not None:
        receipt["event"] = event
    with (controller_root / "commands.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, sort_keys=True) + "\n")


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(value, sort_keys=True) + "\n" for value in records),
        encoding="utf-8",
    )


def _production_chain_fixture(
    tmp_path: Path,
    monkeypatch,
    *,
    case: str,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    leg = subject.LEG_BY_KEY["t362-mitigation"]
    request_id = f"123-{case}.nqsv"
    attempt_id = f"attempt-{case}"
    work_root = tmp_path / case
    work_root.mkdir()
    monkeypatch.setenv("T362_RUN_NONCE", attempt_id)
    monkeypatch.setenv("T362_ATTEMPT_ID", attempt_id)
    observer = signal_observer.Observer(
        work_root,
        "mitigation",
        request_id,
        180,
    )

    marker = {
        "schema_version": signal_observer.MARKER_SCHEMA,
        "mode": "mitigation",
        "normalized_request_id": request_id,
        "pbs_jobid": request_id,
        "run_nonce": attempt_id,
        "hostname": "compute01",
        "pid": 42,
    }
    marker_raw = (json.dumps(marker, sort_keys=True) + "\n").encode()
    (work_root / "run_marker.json").write_bytes(marker_raw)
    marker_hash = hashlib.sha256(marker_raw).hexdigest()
    ready = {
        "schema_version": signal_observer.MARKER_SCHEMA,
        "mode": "mitigation",
        "normalized_request_id": request_id,
        "run_nonce": attempt_id,
        "compute_marker_sha256": marker_hash,
        "canary_sha256": hashlib.sha256(signal_observer.MUTATED).hexdigest(),
        "state": "READY_AFTER_LOGIN_READBACK_ACK",
    }
    (work_root / "ready.json").write_text(
        json.dumps(ready, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    observer.inspect_markers()

    common = {
        "schema_version": signal_observer.EVENT_SCHEMA,
        "mode": "mitigation",
        "run_nonce": attempt_id,
        "normalized_request_id": request_id,
        "compute_marker_sha256": marker_hash,
    }
    parent_events: list[dict[str, object]] = [
        {**common, "event": "parent_started"},
        {**common, "event": "grandchild_alive_immediately_before_ready"},
        {**common, "event": "ready_after_login_readback_ack"},
    ]
    if case != "sigkill":
        parent_events.extend(
            [
                {**common, "event": "signal", "signal_name": "SIGTERM"},
                {
                    **common,
                    "event": "signal_abort_caught",
                    "signal_name": "SIGTERM",
                },
                {
                    **common,
                    "event": "cleanup_signal_sent",
                    "signal_name": "SIGTERM",
                },
                {
                    **common,
                    "event": "cleanup_term_wait_timeout",
                    "waited_ns": (
                        4_000_000_000
                        if case == "term-wait"
                        else signal_observer.MIN_TERM_WAIT_NS
                    ),
                },
                {
                    **common,
                    "event": "cleanup_signal_sent",
                    "signal_name": "SIGKILL",
                },
                {**common, "event": "cleanup_kill_wait_finished"},
                {
                    **common,
                    "event": "canary_restore_verified",
                    "byte_match": True,
                },
                {
                    **common,
                    "event": "finally_exit",
                    "canary_byte_match": True,
                },
            ]
        )
    layer_events = {
        "job-script": [{**common, "event": "run_marker_persisted"}],
        "parent": parent_events,
        "grandchild": [{**common, "event": "grandchild_started"}],
    }
    compute_paths: list[Path] = [work_root / "run_marker.json", work_root / "ready.json"]
    for layer, events in layer_events.items():
        event_path = work_root / f"events-{layer}.jsonl"
        control_path = work_root / f"control-{layer}.jsonl"
        heartbeat_path = work_root / f"heartbeats-{layer}.jsonl"
        _write_jsonl(event_path, events)
        _write_jsonl(
            control_path,
            [
                {**common, "event": "control_start"},
                {**common, "event": "control_normal_exit"},
            ],
        )
        _write_jsonl(
            heartbeat_path,
            [{**common, "event": "heartbeat"}],
        )
        compute_paths.extend([event_path, control_path, heartbeat_path])
    canary = work_root / "canary.txt"
    canary.write_bytes(
        signal_observer.MUTATED if case == "sigkill" else signal_observer.ORIGINAL
    )
    compute_paths.append(canary)
    inventory_records = [
        {
            "schema_version": signal_observer.INVENTORY_SCHEMA,
            "relative_path": path.relative_to(work_root).as_posix(),
            "purpose": "production-chain fixture",
            "cleanup": False,
            "producer": "fixture",
        }
        for path in compute_paths
    ]
    _write_jsonl(work_root / "artifact-inventory.jsonl", inventory_records)

    fixture_root = work_root / "scheduler-fixtures"
    fixture_root.mkdir()
    normal = case != "sigkill"
    qwait_returncode = 9 if case in {"a1", "mixed", "sigkill"} else 0
    accounting_text = (
        f"Request ID: {request_id}\nStarted Request Time: x\n"
        f"Ended Request Time: y\nElapse: 180\n"
        + ("Exit Status: 0\n" if normal else "wall time limit exceeded\n")
    )
    qwait_stdout = (
        "ELAPSE time limit exceeded\n" if qwait_returncode == 9 else ""
    )
    raw_files = {
        "qwait.stdout": qwait_stdout,
        "qwait.stderr": "",
        "racctjob.stdout": accounting_text,
        "racctjob.stderr": "",
        "racctreq.stdout": accounting_text,
        "racctreq.stderr": "",
    }
    for name, content in raw_files.items():
        (fixture_root / name).write_text(content, encoding="utf-8")
    tail = {
        "qstat": {
            "classification": "OK",
            "state": "END",
            "visible": False,
            "stdout": "",
            "stderr": "",
        },
        "racctjob": {
            "classification": "OK",
            "stdout": (fixture_root / "racctjob.stdout").read_text(),
            "stderr": (fixture_root / "racctjob.stderr").read_text(),
        },
        "racctreq": {
            "classification": "OK",
            "stdout": (fixture_root / "racctreq.stdout").read_text(),
            "stderr": (fixture_root / "racctreq.stderr").read_text(),
        },
    }
    observer.request_ever_visible = True
    final, observer_valid = observer.build_final_observation(
        tail=tail,
        terminal_reason="QSTAT_TERMINAL_END",
        permission_error=False,
        active_at_stop=False,
    )
    observer.write_final(final)
    observer_rc = 0 if observer_valid else 3

    scheduler_root = work_root / "scheduler"
    scheduler_root.mkdir()
    scheduler_signal = "SIGKILL" if case == "sigkill" else "SIGTERM"
    remaining_elapse = 0 if case in {"mixed", "sigkill"} else 46
    scheduler_stderr = (
        "%NQSV(INFO): Batch job received signal "
        f"{scheduler_signal}. (Exceeded per-req elapse time limit)\n\n"
        "============================================================\n"
        f"Request ID: {request_id}\n"
        "Started Request Time: x\n"
        "Ended Request Time: y\n"
        "Elapse: 134S\n"
        f"Remaining Elapse: {remaining_elapse}S\n"
        "============================================================\n"
    ).encode()
    scheduler_stderr_name = "fixture.stderr.raw"
    (scheduler_root / scheduler_stderr_name).write_bytes(scheduler_stderr)
    (work_root / "controller").mkdir(exist_ok=True)
    (work_root / "controller" / "job-output-manifest.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "stream": "stderr",
                        "original_name": f"fixture.{request_id}.000.e",
                        "saved_name": scheduler_stderr_name,
                        "original_sha256": hashlib.sha256(
                            scheduler_stderr
                        ).hexdigest(),
                        "original_size": len(scheduler_stderr),
                    }
                ]
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    collected: dict[str, dict[str, object]] = {}
    for name in ("racctjob", "racctreq"):
        stdout = (fixture_root / f"{name}.stdout").read_text()
        stderr = (fixture_root / f"{name}.stderr").read_text()
        collected[name] = {
            "returncode": 0,
            "stdout": stdout,
            "stderr": stderr,
            "accounting_validation": subject._accounting_valid(
                stdout,
                request_id,
                1,
                stderr=stderr,
            ),
        }
    accounting = subject._accounting_snapshot_from_results(collected)
    qwait = {
        "argv": ["qwait", "-t", "4080", request_id],
        "returncode": qwait_returncode,
        "stdout": (fixture_root / "qwait.stdout").read_text(),
        "stderr": (fixture_root / "qwait.stderr").read_text(),
        "timed_out": False,
        "terminated_by_controller": False,
    }
    evaluation = subject._evaluate_attempt_evidence(
        leg=leg,
        work_root=work_root,
        attempt_id=attempt_id,
        request_id=request_id,
        qsub_returncode=0,
        qsub_receipt_valid=True,
        preflight_valid=True,
        monitor={
            "qstat_visible": True,
            "qstat_transient_error_seen": False,
            "qstat_permission_error": False,
            "active_at_execution_deadline": False,
            "terminal_reason": "VISIBLE_REQUEST_DISAPPEARED",
        },
        qwait=qwait,
        observer_returncode=observer_rc,
        accounting=accounting,
        outputs={"errors": [], "observed_counts": {"stdout": 1, "stderr": 1}},
        budget_before={"returncode": 0},
        budget_after={"returncode": 0},
    )

    controller = subject.Controller.__new__(subject.Controller)
    controller.request_count = 1
    controller.cumulative_node_min = leg.requested_node_min
    controller.initial_budget = None
    controller.latest_budget = None
    controller.authoritative = {}
    controller.wave_state_path = tmp_path / f"{case}-wave-state.json"
    controller.wave_state = {
        "schema": subject.WAVE_STATE_SCHEMA,
        "request_limit": subject.REQUEST_LIMIT,
        "requested_node_min_limit": subject.REQUESTED_NODE_MIN_LIMIT,
        "request_count": 1,
        "cumulative_requested_node_min": leg.requested_node_min,
        "requests": [
            {
                "request_ordinal": 1,
                "leg": leg.key,
                "attempt_id": attempt_id,
                "requested_node_min": leg.requested_node_min,
                "cumulative_requested_node_min": leg.requested_node_min,
                "qsub_argv": ["qsub", leg.script],
                "qsub_returncode": 0,
                "request_id": request_id,
                "completed": False,
                "admissible": None,
                "evaluation_model": subject.EVALUATION_MODEL,
                "observation_valid": False,
                "attempt_safe": None,
                "accounting_available": False,
                "accounting_integrity_valid": False,
                "termination_cause_consistent": False,
                "probe_cleanup_outcome": "unknown",
                "unsafe_reason": None,
            }
        ],
        "authoritative_attempts": {},
        "initial_budget": None,
        "initial_four_budget_after": None,
        "latest_budget_after_request": None,
    }
    terminal = subject._qwait_terminal_receipt_valid(qwait, request_id)["valid"]
    controller._record_attempt_outcome(
        leg=leg,
        attempt_id=attempt_id,
        request_id=request_id,
        evaluation=evaluation,
        terminal_proven=bool(terminal),
        budget_after={"returncode": 0},
        retry_reason=None,
        safety_content_present=True,
    )
    completion = subject._completion_status(
        controller.authoritative,
        [leg.key],
        0,
    )
    return evaluation, completion, final


def _write_staged_tracking_receipt(attempt_root: Path) -> None:
    files = []
    for path in sorted(attempt_root.rglob("*")):
        if path.is_file() and path.name != "tracking-receipt.json":
            payload = path.read_bytes()
            files.append(
                {
                    "path": str(path.relative_to(attempt_root)),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "size": len(payload),
                }
            )
    receipt = {
        "schema": subject.TRACKING_SCHEMA,
        "evidence_root": str(attempt_root),
        "file_count": len(files),
        "inventory": {
            "root": str(attempt_root),
            "directories": ["."],
            "files": files,
        },
        "git_check_ignore_all_not_ignored": True,
        "git_add_returncode": 0,
        "git_ls_files_all_matched": True,
        "time_ns": 1,
    }
    (attempt_root / "tracking-receipt.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _staged_reevaluation_fixture(
    tmp_path: Path, monkeypatch
) -> tuple[subject.Controller, dict[str, object], Path]:
    session_id = "session-fixture"
    leg = subject.LEG_BY_KEY["t362-mitigation"]
    attempt_id = "attempt-work"
    request_id = "123-work.nqsv"
    attempt_root = (
        tmp_path
        / subject.EVIDENCE_RELATIVE
        / session_id
        / "attempts"
        / leg.key
        / attempt_id
    )
    attempt_root.mkdir(parents=True)
    _evaluation, _completion, observer_final = _production_chain_fixture(
        attempt_root,
        monkeypatch,
        case="work",
    )
    work_root = attempt_root / "work"
    home_root = attempt_root / "home"
    home_root.mkdir()
    (home_root / "home-read-write.probe.raw").write_bytes(b"home-probe")
    controller_root = work_root / "controller"
    scheduler_root = work_root / "scheduler"
    scheduler_root.mkdir(exist_ok=True)
    qsub_argv = ["qsub", "-v", f"T362_ATTEMPT_ID={attempt_id}", leg.script]
    _write_saved_command(
        controller_root,
        sequence=1,
        purpose="qsub",
        argv=qsub_argv,
        returncode=0,
        stdout=f"Request {request_id} submitted\n".encode(),
    )
    _write_saved_command(
        controller_root,
        sequence=2,
        purpose="lifecycle-qstat-attempt-1",
        argv=["qstat", "-J", "-f", request_id],
        returncode=0,
        stdout=(
            f"Request ID: {request_id}\nRequest State = RUN\n"
        ).encode(),
    )
    _write_saved_command(
        controller_root,
        sequence=3,
        purpose="qwait",
        argv=["qwait", "-t", "4080", request_id],
        returncode=0,
        stdout=b"",
        event="background_finished",
    )
    _write_saved_command(
        controller_root,
        sequence=4,
        purpose="signal-observer",
        argv=[sys.executable, "signal_observer.py"],
        returncode=(
            0 if observer_final["valid_for_safety_conclusion"] is True else 3
        ),
        stdout=b"",
        event="background_finished",
    )
    accounting_text = (
        f"Request ID: {request_id}\nStarted Request Time: x\n"
        "Ended Request Time: y\nElapse: 120\nExit Status: 0\n"
    ).encode()
    for sequence, command in ((5, "racctjob"), (6, "racctreq")):
        _write_saved_command(
            controller_root,
            sequence=sequence,
            purpose=f"final-{command}-attempt-1",
            argv=[command, "-I", request_id],
            returncode=0,
            stdout=accounting_text,
        )
    budget_raw = b"fixture 20 1 30\n"
    _write_saved_command(
        controller_root,
        sequence=7,
        purpose="rbudgetcheck-before-qsub",
        argv=["rbudgetcheck"],
        returncode=0,
        stdout=budget_raw,
    )
    _write_saved_command(
        controller_root,
        sequence=8,
        purpose="rbudgetcheck-after-request",
        argv=["rbudgetcheck"],
        returncode=0,
        stdout=budget_raw,
    )
    stdout_payload = b"fixture stdout\n"
    stderr_payload = (
        "%NQSV(INFO): Batch job received signal SIGTERM. "
        "(Exceeded per-req elapse time limit)\n\n"
        f"Request ID: {request_id}\nStarted Request Time: x\n"
        "Ended Request Time: y\nElapse: 120S\nRemaining Elapse: 60S\n"
        "Exit Status: 0\n"
    ).encode()
    stdout_name = "fixture.stdout.raw"
    stderr_name = "fixture.stderr.raw"
    (scheduler_root / stdout_name).write_bytes(stdout_payload)
    (scheduler_root / stderr_name).write_bytes(stderr_payload)
    (controller_root / "job-output-manifest.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "stream": "stdout",
                        "original_name": f"fixture.{request_id}.000.o",
                        "saved_name": stdout_name,
                        "original_sha256": hashlib.sha256(stdout_payload).hexdigest(),
                        "original_size": len(stdout_payload),
                    },
                    {
                        "stream": "stderr",
                        "original_name": f"fixture.{request_id}.000.e",
                        "saved_name": stderr_name,
                        "original_sha256": hashlib.sha256(stderr_payload).hexdigest(),
                        "original_size": len(stderr_payload),
                    },
                ]
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    old_evaluation = _split(
        observation=False,
        accounting_available=False,
        accounting_integrity_valid=False,
        termination_cause_consistent=False,
    )
    request: dict[str, object] = {
        "request_ordinal": 1,
        "leg": leg.key,
        "attempt_id": attempt_id,
        "requested_node_min": leg.requested_node_min,
        "cumulative_requested_node_min": leg.requested_node_min,
        "qsub_argv": qsub_argv,
        "qsub_returncode": 0,
        "request_id": request_id,
        "completed": True,
        "budget_after": {"returncode": 0},
        "external_root_terminal_proven": True,
        "safety_content_present": True,
        "selected_as_authoritative": False,
        **old_evaluation,
        "admissible": False,
    }
    attempt_result = {
        "schema": subject.ATTEMPT_SCHEMA,
        "session_id": session_id,
        "request_ordinal": 1,
        "leg": leg.key,
        "attempt_id": attempt_id,
        "request_id": request_id,
        **old_evaluation,
        "admissible": False,
        "validity_conjunction": {"frozen_evaluator_bug": False},
    }
    (controller_root / "attempt-result.json").write_text(
        json.dumps(attempt_result, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_staged_tracking_receipt(attempt_root)

    controller = subject.Controller.__new__(subject.Controller)
    controller.repo_root = tmp_path
    controller.request_count = 1
    controller.cumulative_node_min = leg.requested_node_min
    controller.authoritative = {}
    controller.initial_budget = None
    controller.latest_budget = None
    controller.stale_sessions = []
    controller.wave_state_path = tmp_path / "_controller" / "wave-state.json"
    controller.wave_state = {
        "schema": subject.WAVE_STATE_SCHEMA,
        "request_limit": subject.REQUEST_LIMIT,
        "requested_node_min_limit": subject.REQUESTED_NODE_MIN_LIMIT,
        "request_count": 1,
        "cumulative_requested_node_min": leg.requested_node_min,
        "requests": [request],
        "authoritative_attempts": {},
        "initial_budget": None,
        "initial_four_budget_after": None,
        "latest_budget_after_request": None,
    }
    return controller, request, attempt_root


def test_safe_mitigation_is_authoritative_without_accounting() -> None:
    evaluation = _split(accounting_available=False)

    assert evaluation["observation_valid"] is True
    assert evaluation["attempt_safe"] is True
    assert subject._record_is_authoritative(_record(evaluation)) is True


def test_unsafe_mitigation_remains_authoritative(tmp_path: Path) -> None:
    observer = signal_observer.Observer.__new__(signal_observer.Observer)
    observer.run_root = tmp_path
    observer.request_id = "123.nqsv"
    observer.normalized_request_id = "123.nqsv"
    observer.expected_run_nonce = "attempt-1"
    (tmp_path / "canary.txt").write_bytes(signal_observer.MUTATED)
    cleanup = observer.validate_cleanup_order(
        [
            {"event": "grandchild_alive_immediately_before_ready"},
            {"event": "ready_after_login_readback_ack"},
        ]
    )
    cleanup_outcome, unsafe_reason = observer.classify_probe_cleanup(
        cleanup, observer.readback_restored_canary()
    )
    evaluation = _split(
        cleanup_outcome=cleanup_outcome,
        unsafe_reason=unsafe_reason,
    )

    assert evaluation["observation_valid"] is True
    assert evaluation["attempt_safe"] is False
    assert subject._record_is_authoritative(_record(evaluation)) is True


def test_sigkill_cleanup_absence_is_classified_from_event_log_and_root(
    tmp_path: Path,
) -> None:
    observer = signal_observer.Observer.__new__(signal_observer.Observer)
    observer.run_root = tmp_path
    observer.mode = "mitigation"
    observer.request_id = "123.nqsv"
    observer.normalized_request_id = "123.nqsv"
    observer.expected_run_nonce = "attempt-1"
    observer.run_marker = None
    events = [
        {
            "schema_version": signal_observer.EVENT_SCHEMA,
            "mode": "mitigation",
            "event": "grandchild_alive_immediately_before_ready",
        },
        {
            "schema_version": signal_observer.EVENT_SCHEMA,
            "mode": "mitigation",
            "event": "ready_after_login_readback_ack",
        },
    ]
    (tmp_path / "events-parent.jsonl").write_text(
        "".join(json.dumps(value) + "\n" for value in events),
        encoding="utf-8",
    )
    parsed, parse_errors = observer._read_jsonl("events-parent.jsonl")
    (tmp_path / "canary.txt").write_bytes(signal_observer.MUTATED)

    cleanup = observer.validate_cleanup_order(parsed)
    readback = observer.readback_restored_canary()
    outcome, reason = observer.classify_probe_cleanup(cleanup, readback)

    assert parse_errors == []
    assert cleanup["control_prefix_valid"] is True
    assert cleanup["restore_outcome_valid"] is False
    assert (outcome, reason) == (
        "unsafe",
        "post_restore_canary_mismatch",
    )


def test_short_term_wait_is_cleanup_order_unsafe(tmp_path: Path) -> None:
    observer = signal_observer.Observer.__new__(signal_observer.Observer)
    observer.run_root = tmp_path
    observer.request_id = "123.nqsv"
    observer.normalized_request_id = "123.nqsv"
    observer.expected_run_nonce = "attempt-1"
    events = [
        {"event": "grandchild_alive_immediately_before_ready"},
        {"event": "ready_after_login_readback_ack"},
        {"event": "cleanup_signal_sent", "signal_name": "SIGTERM"},
        {"event": "cleanup_term_wait_timeout", "waited_ns": 4_000_000_000},
        {"event": "cleanup_signal_sent", "signal_name": "SIGKILL"},
        {"event": "cleanup_kill_wait_finished"},
        {"event": "canary_restore_verified", "byte_match": True},
        {"event": "finally_exit", "canary_byte_match": True},
    ]
    (tmp_path / "canary.txt").write_bytes(signal_observer.ORIGINAL)

    cleanup = observer.validate_cleanup_order(events)
    outcome, reason = observer.classify_probe_cleanup(
        cleanup, observer.readback_restored_canary()
    )

    assert cleanup["control_prefix_valid"] is True
    assert (outcome, reason) == ("unsafe", "cleanup_order_invalid")


def test_accounting_mixed_request_is_rejected() -> None:
    value = subject._accounting_valid(
        "Request ID: 999.nqsv\n"
        "Started Request Time: x\nEnded Request Time: y\nElapse: 1\n",
        "123.nqsv",
        1,
    )

    assert value["valid"] is False
    assert value["exact_request_record_count_valid"] is True
    assert value["exclusive_request_ids_valid"] is False


def test_accounting_extra_job_is_rejected() -> None:
    value = subject._accounting_valid(
        "Request ID: 123.nqsv\nRequest ID: 123.nqsv\n"
        "Started Request Time: x\nEnded Request Time: y\nElapse: 1\n",
        "123.nqsv",
        1,
    )

    assert value["valid"] is False
    assert value["exact_request_record_count_valid"] is False
    assert value["exclusive_request_ids_valid"] is True


def test_accounting_termination_cause_contradiction_is_rejected() -> None:
    evaluation = _split(
        accounting_available=True,
        accounting_integrity_valid=True,
        termination_cause_consistent=False,
    )

    assert evaluation["observation_valid"] is False


def test_available_accounting_null_integrity_is_rejected_by_envelope() -> None:
    evaluation = _split(accounting_available=True)
    evaluation["accounting_integrity_valid"] = None

    with pytest.raises(
        subject.ControllerError,
        match="available accounting requires non-null integrity and cause",
    ):
        subject._validate_split_v2_envelope(evaluation)


def test_available_accounting_null_integrity_fails_closed_in_composer() -> None:
    evaluation = _split(
        accounting_available=True,
        accounting_integrity_valid=None,
    )

    assert evaluation["accounting_integrity_valid"] is False
    assert evaluation["observation_valid"] is False
    assert (
        subject._snapshot_integrity_value(
            {"available": True, "integrity_valid": None}
        )
        is False
    )


def test_later_integrity_snapshot_supplies_its_own_termination_cause() -> None:
    selected = subject._select_accounting_snapshot(
        {
            "available": True,
            "integrity_valid": False,
            "termination_cause_classification": "WALLTIME_RESOURCE_LIMIT",
        },
        {
            "available": True,
            "integrity_valid": True,
            "termination_cause_classification": "NORMAL_COMPLETION",
        },
    )

    assert selected == {
        "source": "controller-later",
        "available": True,
        "integrity_valid": True,
        "termination_cause_classification": "NORMAL_COMPLETION",
    }


def test_observer_accounting_rejects_foreign_request_snapshot() -> None:
    observer = signal_observer.Observer.__new__(signal_observer.Observer)
    observer.normalized_request_id = "123.nqsv"
    observer.requested_seconds = 180
    tail = {
        "qstat": {"classification": "OK", "stdout": "", "stderr": ""},
        "racctjob": {
            "classification": "OK",
            "stdout": (
                "Request ID: 999.nqsv\nElapse: 180\n"
                "wall time limit exceeded\n"
            ),
            "stderr": "",
        },
        "racctreq": {
            "classification": "OK",
            "stdout": "Request ID: 123.nqsv\nElapse: 180\n",
            "stderr": "",
        },
    }

    value = observer.validate_accounting(tail)

    assert value["available"] is True
    assert value["integrity_valid"] is False
    assert any("foreign request" in error for error in value["integrity_errors"])


def test_observer_timeout_counts_all_qstat_phases_and_local_caps() -> None:
    command_part = (
        signal_observer.FINALIZATION_QSTAT_PHASES
        * signal_observer._bounded_command_upper_seconds(
            signal_observer.QSTAT_ATTEMPTS,
            signal_observer.QSTAT_RETRY_SECONDS,
        )
        + 2
        * signal_observer._bounded_command_upper_seconds(
            signal_observer.ACCOUNTING_ATTEMPTS,
            signal_observer.ACCOUNTING_RETRY_SECONDS,
        )
    )

    assert signal_observer.FINALIZATION_QSTAT_PHASES == 3
    assert signal_observer.POST_MONITOR_FINALIZATION_TIMEOUT_SECONDS == (
        command_part
        + signal_observer._bounded_local_finalization_upper_seconds()
    )
    assert signal_observer.MAX_CLEANUP_TARGETS > 0


def test_observer_local_bound_accounts_for_signal_raw_and_fsync_caps() -> None:
    bounded_bytes = (
        signal_observer.INVENTORY_FILE_COUNT
        * signal_observer.MAX_INVENTORY_BYTES_PER_FILE
        + signal_observer.MAX_CANARY_BYTES
        + signal_observer.SIGNAL_LOG_FILE_COUNT
        * signal_observer.MAX_SIGNAL_LOG_BYTES_PER_FILE
        + signal_observer.MAX_WRITER_FAILURE_BYTES
        + signal_observer.FINALIZATION_COMMAND_INVOCATIONS
        * 2
        * signal_observer.MAX_COMMAND_RAW_BYTES_PER_STREAM
        + signal_observer.MAX_OBSERVER_EVENT_BYTES
    )
    bounded_records = (
        signal_observer.INVENTORY_FILE_COUNT
        * signal_observer.MAX_INVENTORY_RECORDS_PER_FILE
        + signal_observer.SIGNAL_LOG_FILE_COUNT
        * signal_observer.MAX_SIGNAL_LOG_RECORDS_PER_FILE
        + signal_observer.MAX_OBSERVER_EVENT_RECORDS
    )
    expected = (
        (
            bounded_bytes
            + signal_observer.LOCAL_IO_BYTES_PER_SECOND_FLOOR
            - 1
        )
        // signal_observer.LOCAL_IO_BYTES_PER_SECOND_FLOOR
        + (
            bounded_records * signal_observer.LOCAL_RECORD_UPPER_MILLISECONDS
            + signal_observer.MAX_DISCOVERY_ENTRIES
            * signal_observer.LOCAL_DIRECTORY_ENTRY_UPPER_MILLISECONDS
            + signal_observer.MAX_CLEANUP_TARGETS
            * signal_observer.LOCAL_UNLINK_UPPER_MILLISECONDS
            + 999
        )
        // 1000
        + signal_observer.LOCAL_FSYNC_COUNT
        * signal_observer.LOCAL_FSYNC_UPPER_SECONDS
    )

    assert signal_observer.LOCAL_FSYNC_COUNT == (
        signal_observer.FINALIZATION_COMMAND_INVOCATIONS * 7 + 6
    )
    assert signal_observer._bounded_local_finalization_upper_seconds() == expected


def test_accounting_integrity_failure_blocks_observation() -> None:
    evaluation = _split(
        accounting_available=True,
        accounting_integrity_valid=False,
    )

    assert evaluation["observation_valid"] is False


def test_permission_accounting_unavailable_is_neutral_to_observation_gate() -> None:
    stderr = "sudo: パスワードが必要です\n"
    collected: dict[str, dict[str, object]] = {}
    for name in ("racctjob", "racctreq"):
        validation = subject._accounting_valid(
            "",
            "123.nqsv",
            1,
            stderr=stderr,
            returncode=1,
        )
        collected[name] = {
            "returncode": 1,
            "stdout": "",
            "stderr": stderr,
            "accounting_validation": validation,
        }
    accounting = subject._accounting_snapshot_from_results(collected)
    selected = subject._select_accounting_snapshot(
        {
            "available": False,
            "integrity_valid": False,
            "termination_cause_classification": "UNKNOWN_NOT_RESOURCE_LIMIT",
        },
        accounting,
    )
    evaluation = _split(
        accounting_available=selected["available"],
        accounting_integrity_valid=selected["integrity_valid"],
        termination_cause_consistent=None,
        accounting_unavailable_reason=selected["unavailable_reason"],
    )
    observer = signal_observer.Observer.__new__(signal_observer.Observer)
    observer.normalized_request_id = "123.nqsv"
    observer.requested_seconds = 180
    observer_accounting = observer.validate_accounting(
        {
            "qstat": {"classification": "OK", "stdout": "", "stderr": ""},
            **{
                name: {
                    "classification": "COMMAND_ERROR",
                    "stdout": "",
                    "stderr": stderr,
                }
                for name in ("racctjob", "racctreq")
            },
        }
    )

    assert accounting["available"] is False
    assert accounting["unavailable_reason"] == "permission"
    assert accounting["integrity_valid"] is None
    assert selected["integrity_valid"] is None
    assert evaluation["accounting_evidence"] is False
    assert evaluation["observation_valid"] is True
    assert observer_accounting["valid"] is None
    assert observer_accounting["integrity_valid"] is None
    assert observer_accounting["unavailable_reason"] == "permission"


def test_recorded_foreign_accounting_still_blocks_observation() -> None:
    request_id = "123.nqsv"
    clean = (
        f"Request ID: {request_id}\nStarted Request Time: x\n"
        "Ended Request Time: y\nElapse: 180\nExit Status: 0\n"
    )
    mixed = clean + (
        "Request ID: 999.nqsv\nStarted Request Time: x\n"
        "Ended Request Time: y\nElapse: 180\nExit Status: 0\n"
    )
    collected = {
        name: {
            "returncode": 0,
            "stdout": text,
            "stderr": "",
            "accounting_validation": subject._accounting_valid(
                text,
                request_id,
                1,
            ),
        }
        for name, text in (("racctjob", mixed), ("racctreq", clean))
    }
    accounting = subject._accounting_snapshot_from_results(collected)
    evaluation = _split(
        accounting_available=accounting["available"],
        accounting_integrity_valid=accounting["integrity_valid"],
    )

    assert accounting["available"] is True
    assert accounting["integrity_valid"] is False
    assert evaluation["observation_valid"] is False


def test_accounting_fields_without_request_id_are_malformed() -> None:
    text = "Started Request Time: x\nEnded Request Time: y\nElapse: 180\n"
    controller_validation = subject._accounting_valid(
        text,
        "123.nqsv",
        1,
        returncode=0,
    )
    snapshot = subject._accounting_snapshot_from_results(
        {
            name: {
                "returncode": 0,
                "stdout": text,
                "stderr": "",
                "accounting_validation": controller_validation,
            }
            for name in ("racctjob", "racctreq")
        }
    )
    observer = signal_observer.Observer.__new__(signal_observer.Observer)
    observer.normalized_request_id = "123.nqsv"
    observer.requested_seconds = 180
    observer_validation = observer.validate_accounting(
        {
            "qstat": {"classification": "OK", "stdout": "", "stderr": ""},
            **{
                name: {
                    "classification": "OK",
                    "stdout": text,
                    "stderr": "",
                }
                for name in ("racctjob", "racctreq")
            },
        }
    )

    assert controller_validation["available"] is True
    assert controller_validation["valid"] is False
    assert snapshot["integrity_valid"] is False
    assert observer_validation["available"] is True
    assert observer_validation["integrity_valid"] is False


def test_manifest_bound_scheduler_accounting_rejects_outside_block_cause(
    tmp_path: Path,
) -> None:
    request_id = "123.nqsv"
    scheduler_root = tmp_path / "scheduler"
    controller_root = tmp_path / "controller"
    scheduler_root.mkdir()
    controller_root.mkdir()
    payload = (
        "%NQSV(INFO): Exceeded per-req elapse time limit\n"
        "Request ID: 123.nqsv\n"
        "Ended Request Time: y\n"
        "Elapse: 184S\n"
        "Remaining Elapse: 0S\n"
    ).encode()
    saved_name = "fixture.stderr.raw"
    (scheduler_root / saved_name).write_bytes(payload)
    (controller_root / "job-output-manifest.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "stream": "stderr",
                        "original_name": "fixture.123.nqsv.000.e",
                        "saved_name": saved_name,
                        "original_sha256": hashlib.sha256(payload).hexdigest(),
                        "original_size": len(payload),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    saved = subject._saved_nqsv_stderr_accounting(tmp_path, request_id)

    assert saved["termination_cause_evidence_available"] is False
    assert saved["termination_cause_classification"] == (
        "UNKNOWN_NOT_RESOURCE_LIMIT"
    )


def test_manifest_bound_scheduler_accounting_rejects_foreign_filename(
    tmp_path: Path,
) -> None:
    scheduler_root = tmp_path / "scheduler"
    controller_root = tmp_path / "controller"
    scheduler_root.mkdir()
    controller_root.mkdir()
    payload = (
        "Request ID: 123.nqsv\nEnded Request Time: y\n"
        "Remaining Elapse: 0S\nwall time limit exceeded\n"
    ).encode()
    saved_name = "fixture.stderr.raw"
    (scheduler_root / saved_name).write_bytes(payload)
    (controller_root / "job-output-manifest.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "stream": "stderr",
                        "original_name": "fixture.999.nqsv.000.e",
                        "saved_name": saved_name,
                        "original_sha256": hashlib.sha256(payload).hexdigest(),
                        "original_size": len(payload),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    saved = subject._saved_nqsv_stderr_accounting(tmp_path, "123.nqsv")

    assert saved["termination_cause_evidence_available"] is False
    assert any("name binding is malformed" in error for error in saved["errors"])


def test_manifest_bound_scheduler_accounting_supplies_cause(
    tmp_path: Path,
) -> None:
    request_id = "123.nqsv"
    scheduler_root = tmp_path / "scheduler"
    controller_root = tmp_path / "controller"
    scheduler_root.mkdir()
    controller_root.mkdir()
    payload = (
        "Request ID: 123.nqsv\n"
        "Started Request Time: x\n"
        "Ended Request Time: y\n"
        "Elapse: 184S\n"
        "Remaining Elapse: 0S\n"
        "%NQSV(INFO): Batch job received signal SIGKILL. "
        "(Exceeded per-req elapse time limit)\n"
    ).encode()
    saved_name = "fixture.stderr.raw"
    (scheduler_root / saved_name).write_bytes(payload)
    (controller_root / "job-output-manifest.json").write_text(
        json.dumps(
            {
                "files": [
                    {
                        "stream": "stderr",
                        "original_name": "fixture.123.nqsv.000.e",
                        "saved_name": saved_name,
                        "original_sha256": hashlib.sha256(payload).hexdigest(),
                        "original_size": len(payload),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    saved = subject._saved_nqsv_stderr_accounting(tmp_path, request_id)
    consistency = subject._termination_cause_consistency(
        qwait_validation={
            "valid": True,
            "returncode_raw": 9,
            "expected_outcome": "elapse-signal",
        },
        accounting_snapshot={"available": False},
        saved_nqsv_stderr=saved,
        signal_leg=True,
    )

    assert saved["termination_cause_evidence_available"] is True
    assert saved["termination_cause_classification"] == (
        "WALLTIME_RESOURCE_LIMIT"
    )
    assert consistency == {
        "consistent": True,
        "evidence_source": (
            "qwait-receipt+manifest-bound-scheduler-stderr"
        ),
        "observed_cause": "WALLTIME_RESOURCE_LIMIT",
    }


def test_post_restore_canary_mismatch_is_the_only_unsafe_reason() -> None:
    evaluation = _split(
        cleanup_outcome="unsafe",
        unsafe_reason="post_restore_canary_mismatch",
    )

    assert evaluation["attempt_safe"] is False
    assert evaluation["unsafe_reason"] == "post_restore_canary_mismatch"


def test_controller_recomputes_canary_outcome_from_bound_bytes() -> None:
    request_id = "123.nqsv"
    attempt_id = "attempt-1"
    conditions = {key: True for key in subject.OBSERVER_OBSERVATION_KEYS}
    mutated = b"MUTATED\n"
    expected = subject.EXPECTED_CANARY_BYTES
    observation = {
        "schema_version": subject.T362_OBSERVER_SCHEMA,
        "mode": "mitigation",
        "request_id": request_id,
        "run_marker": {
            "run_nonce": attempt_id,
            "normalized_request_id": request_id,
            "mode": "mitigation",
        },
        "acceptance_conditions": {"fixture": True},
        "valid_for_safety_conclusion": True,
        "observation_conditions": conditions,
        "probe_cleanup_outcome": "safe",
        "unsafe_reason": None,
        "post_restore_canary_readback": {
            "request_id": request_id,
            "run_nonce": attempt_id,
            "outcome": "safe",
            "observed_bytes_hex": mutated.hex(),
            "observed_sha256": hashlib.sha256(mutated).hexdigest(),
            "expected_bytes_hex": expected.hex(),
            "expected_sha256": hashlib.sha256(expected).hexdigest(),
        },
        "signal_observations": {"parent": ["SIGTERM"]},
    }

    validation = subject._validate_signal_observation_payload(
        observation,
        0,
        leg=subject.LEG_BY_KEY["t362-mitigation"],
        request_id=request_id,
        attempt_id=attempt_id,
    )

    assert validation["valid"] is False
    assert any("declared outcome" in error for error in validation["errors"])


def test_final_absence_reads_raw_canary_before_retry(tmp_path: Path) -> None:
    (tmp_path / "canary.txt").write_bytes(b"MUTATED\n")

    value = subject._raw_signal_safety_content(tmp_path)

    assert value["present"] is True
    assert value["sources"] == ["canary.txt:state-present"]


def test_saved_qsub_receipt_is_revalidated_on_normal_shape(tmp_path: Path) -> None:
    request_id = "123.nqsv"
    argv = ["qsub", "probe.pbs"]
    _write_saved_command(
        tmp_path / "controller",
        sequence=1,
        purpose="qsub",
        argv=argv,
        returncode=0,
        stdout=f"Request {request_id} submitted\n".encode(),
    )

    value = subject._saved_submission_validation(
        tmp_path,
        {
            "qsub_argv": argv,
            "qsub_returncode": 0,
            "request_id": request_id,
        },
    )

    assert value["valid"] is True


def test_nonzero_qsub_with_request_id_is_not_retryable(tmp_path: Path) -> None:
    request_id = "123.nqsv"
    argv = ["qsub", "probe.pbs"]
    _write_saved_command(
        tmp_path / "controller",
        sequence=1,
        purpose="qsub",
        argv=argv,
        returncode=1,
        stdout=f"Request {request_id} submitted\n".encode(),
    )
    validation = subject._saved_submission_validation(
        tmp_path,
        {
            "qsub_argv": argv,
            "qsub_returncode": 1,
            "request_id": request_id,
        },
    )

    assert validation["valid"] is False
    assert subject._retry_reason(
        qsub_returncode=1,
        request_id=request_id,
        monitor={},
    ) is None


def test_hygiene_failure_does_not_create_false_danger() -> None:
    evaluation = _split(hygiene=False)

    assert evaluation["attempt_safe"] is None
    assert evaluation["unsafe_reason"] is None


def test_legacy_false_is_never_promoted_to_authority() -> None:
    legacy = {"admissible": False, "external_root_terminal_proven": True}

    assert (
        subject._record_is_authoritative(
            legacy, preserve_legacy_authority=True
        )
        is False
    )


def test_unknown_evaluation_model_is_rejected() -> None:
    with pytest.raises(subject.ControllerError, match="unknown evaluation_model"):
        subject._record_is_authoritative({"evaluation_model": "split-v3"})


def test_explicit_null_evaluation_model_is_rejected() -> None:
    with pytest.raises(subject.ControllerError, match="unknown evaluation_model"):
        subject._record_is_authoritative({"evaluation_model": None})


def test_terminal_false_split_v2_is_not_authoritative() -> None:
    evaluation = _split()

    assert subject._record_is_authoritative(_record(evaluation, terminal=False)) is False


def test_safe_mitigation_accepts_request_bound_normal_qwait() -> None:
    leg = subject.LEG_BY_KEY["t362-mitigation"]
    request_id = "123.nqsv"
    observer = {
        "payload_validation": {
            "probe_cleanup_outcome": "safe",
            "acceptance_conditions": {"python_parent_sigterm_caught": True},
        },
        "observation_raw": {"signal_observations": {"parent": ["SIGTERM"]}},
    }
    qwait = _natural_qwait(request_id)

    assert subject._qwait_valid(leg, qwait, request_id, observer)["valid"] is True


def test_qwait_missing_natural_completion_flags_is_rejected() -> None:
    request_id = "123.nqsv"
    qwait = {
        "argv": ["qwait", "-t", "4080", request_id],
        "returncode": 0,
        "stdout": "",
        "stderr": "",
    }

    assert subject._qwait_terminal_receipt_valid(qwait, request_id)["valid"] is False


def test_qwait_controller_termination_is_rejected() -> None:
    request_id = "123.nqsv"
    qwait = _natural_qwait(request_id)
    qwait["terminated_by_controller"] = True

    assert subject._qwait_terminal_receipt_valid(qwait, request_id)["valid"] is False


def test_signal_only_target_is_a_closed_two_leg_set() -> None:
    assert subject.SIGNAL_LEG_KEYS == (
        "t362-mitigation",
        "t362-split-warning",
    )


def test_per_leg_retry_cap_is_exactly_two_attempts() -> None:
    common = {
        "reason": "qsub_rc_nonzero",
        "terminal_proven": True,
        "safety_content_present": False,
        "attempt_safe": None,
    }

    assert subject._retry_allowed(attempts_for_leg=1, **common) is True
    assert subject._retry_allowed(attempts_for_leg=2, **common) is False


def test_reserve_request_enforces_production_per_leg_cap() -> None:
    controller = subject.Controller.__new__(subject.Controller)
    controller.request_count = 2
    controller.cumulative_node_min = 6
    controller.leg_attempt_counts = {
        "t362-mitigation": subject.PER_LEG_ATTEMPT_CAP
    }
    controller.wave_state = {"requests": []}
    leg = subject.LEG_BY_KEY["t362-mitigation"]

    with pytest.raises(subject.ControllerError, match="per-leg attempt cap"):
        controller._reserve_request(leg, "attempt-3", ["qsub"], 1)


def test_prequeued_first_leg_outcome_updates_its_own_reservation() -> None:
    controller = subject.Controller.__new__(subject.Controller)
    controller.wave_state = {
        "requests": [
            {
                "request_ordinal": 1,
                "cumulative_requested_node_min": 3,
                "leg": "t362-mitigation",
                "attempt_id": "mitigation-a1",
                "request_id": "123.nqsv",
                "completed": False,
            },
            {
                "request_ordinal": 2,
                "cumulative_requested_node_min": 6,
                "leg": "t362-split-warning",
                "attempt_id": "split-a1",
                "request_id": "124.nqsv",
                "completed": False,
            },
        ],
        "initial_four_budget_after": None,
    }
    controller.authoritative = {}
    controller.latest_budget = None
    controller._persist_wave_state = lambda: None
    evaluation = _split()

    controller._record_attempt_outcome(
        leg=subject.LEG_BY_KEY["t362-mitigation"],
        attempt_id="mitigation-a1",
        request_id="123.nqsv",
        evaluation=evaluation,
        terminal_proven=True,
        budget_after={"returncode": 0},
        retry_reason=None,
        safety_content_present=True,
    )

    first, second = controller.wave_state["requests"]
    assert first["completed"] is True
    assert first["request_ordinal"] == 1
    assert first["cumulative_requested_node_min"] == 3
    assert second["completed"] is False


def test_prequeued_terminal_request_skips_visibility_timeout(monkeypatch) -> None:
    monkeypatch.setattr(
        subject,
        "_bounded_qstat",
        lambda *_args, **_kwargs: {
            "classification": "ok",
            "visible": False,
            "returncode": 0,
            "execution_hosts": [],
            "state": None,
        },
    )

    value = subject._monitor_request(
        object(),
        "123.nqsv",
        180,
        submission_receipt_valid=True,
        qwait_already_finished=True,
    )

    assert value["terminal_reason"] == "PREQUEUED_REQUEST_ALREADY_TERMINAL"


def test_migration_requires_bound_raw_revalidation() -> None:
    request = {
        "attempt_id": "attempt-1",
        "request_id": "123.nqsv",
        "completed": True,
        "qsub_returncode": 0,
        "external_root_terminal_proven": False,
        "admissible": False,
    }
    raw = {"attempt_id": "attempt-1", "request_id": "123.nqsv", "valid": True}

    assert subject._migration_terminal_upgrade_allowed(request, raw) is True


def test_migration_without_raw_revalidation_is_rejected() -> None:
    request = {
        "attempt_id": "attempt-1",
        "request_id": "123.nqsv",
        "completed": True,
        "qsub_returncode": 0,
        "external_root_terminal_proven": False,
        "admissible": False,
    }
    raw = {"attempt_id": "attempt-1", "request_id": "123.nqsv", "valid": False}

    assert subject._migration_terminal_upgrade_allowed(request, raw) is False


def test_sessionless_migration_reads_saved_qsub_and_qwait_raw(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(subject, "WORK_BASE", tmp_path)
    leg = subject.LEG_BY_KEY["t362-default"]
    attempt_id = "attempt-1"
    request_id = "123.nqsv"
    work_root = tmp_path / leg.key / attempt_id
    controller_root = work_root / "controller"
    qsub_argv = ["qsub", "-v", f"T362_RUN_ROOT={work_root}", leg.script]
    _write_saved_command(
        controller_root,
        sequence=1,
        purpose="qsub",
        argv=qsub_argv,
        returncode=0,
        stdout=f"Request {request_id} submitted\n".encode(),
    )
    _write_saved_command(
        controller_root,
        sequence=2,
        purpose="qwait",
        argv=["qwait", "-t", "4080", request_id],
        returncode=9,
        stdout=b"ELAPSE time limit exceeded\n",
        event="background_finished",
    )
    request = {
        "request_ordinal": 1,
        "leg": leg.key,
        "attempt_id": attempt_id,
        "requested_node_min": leg.requested_node_min,
        "cumulative_requested_node_min": leg.requested_node_min,
        "qsub_argv": qsub_argv,
        "qsub_returncode": 0,
        "request_id": request_id,
        "completed": True,
        "admissible": False,
        "budget_after": {"returncode": 0},
        "external_root_terminal_proven": False,
    }
    controller = subject.Controller.__new__(subject.Controller)
    controller.wave_state = {
        "schema": subject.LEGACY_WAVE_STATE_SCHEMA,
        "request_limit": subject.REQUEST_LIMIT,
        "requested_node_min_limit": subject.REQUESTED_NODE_MIN_LIMIT,
        "request_count": 1,
        "cumulative_requested_node_min": leg.requested_node_min,
        "requests": [request],
        "authoritative_attempts": {},
        "initial_budget": None,
        "initial_four_budget_after": None,
        "latest_budget_after_request": None,
    }
    controller.wave_state_path = tmp_path / "_controller" / "wave-state.json"
    controller.request_count = 1
    controller.cumulative_node_min = leg.requested_node_min
    controller.authoritative = {}
    controller.initial_budget = None
    controller.latest_budget = None
    controller.stale_sessions = []

    assert controller._migrate_sessionless_completed_requests() == 1
    assert request["external_root_terminal_proven"] is True
    receipt = Path(request["terminal_migration"]["receipt_path"])
    assert receipt.is_file()


def test_completed_split_v2_staged_raw_is_reevaluated_and_preserves_old_evaluation(
    tmp_path: Path, monkeypatch
) -> None:
    controller, request, attempt_root = _staged_reevaluation_fixture(
        tmp_path, monkeypatch
    )
    monkeypatch.setattr(
        subject,
        "_saved_staged_preflight_validation",
        lambda **_kwargs: {"valid": True, "errors": [], "source_commit": "fixture"},
    )

    def reject_external_command(*_args, **_kwargs):
        raise AssertionError("reevaluation must not launch qsub or another command")

    monkeypatch.setattr(subject.subprocess, "run", reject_external_command)

    assert controller._reevaluate_completed_staged_requests() == 1
    assert request["observation_valid"] is True
    assert request["superseded_evaluation"]["observation_valid"] is False
    assert request["selected_as_authoritative"] is True
    assert controller.authoritative == {request["leg"]: request["attempt_id"]}
    saved_result = json.loads(
        (attempt_root / "work" / "controller" / "attempt-result.json").read_text()
    )
    assert saved_result["observation_valid"] is True
    assert saved_result["superseded_evaluation"]["observation_valid"] is False
    receipt = json.loads(
        (attempt_root / "reevaluation-receipt.json").read_text()
    )
    assert receipt["target_attempt_id"] == request["attempt_id"]
    assert receipt["evaluator_tool_sha256"] == hashlib.sha256(
        Path(subject.__file__).read_bytes()
    ).hexdigest()
    assert receipt["qsub_submitted"] is False
    assert receipt["attempt_result_sha256_after"] == hashlib.sha256(
        (attempt_root / "work" / "controller" / "attempt-result.json").read_bytes()
    ).hexdigest()


def test_completed_split_v2_reevaluation_rejects_staged_raw_hash_mismatch(
    tmp_path: Path, monkeypatch
) -> None:
    controller, request, attempt_root = _staged_reevaluation_fixture(
        tmp_path, monkeypatch
    )
    monkeypatch.setattr(
        subject,
        "_saved_staged_preflight_validation",
        lambda **_kwargs: {"valid": True, "errors": [], "source_commit": "fixture"},
    )
    raw_path = next((attempt_root / "work" / "controller" / "raw").glob("*.raw"))
    raw_path.write_bytes(raw_path.read_bytes() + b"tampered")
    result_path = attempt_root / "work" / "controller" / "attempt-result.json"
    result_before = result_path.read_bytes()

    with pytest.raises(subject.ControllerError, match="hash validation failed"):
        controller._reevaluate_completed_staged_requests()

    assert "superseded_evaluation" not in request
    assert controller.authoritative == {}
    assert result_path.read_bytes() == result_before
    assert not (attempt_root / "reevaluation-receipt.json").exists()


def test_sync_recorder_emits_both_qwait_termination_flags(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            ["qwait"], 0, stdout=b"", stderr=b""
        ),
    )
    recorder = subject.Recorder(tmp_path / "controller")

    receipt = recorder.record(
        ["qwait", "-t", "4080", "123.nqsv"],
        "qwait",
    )

    assert receipt["timed_out"] is False
    assert receipt["terminated_by_controller"] is False


def test_accounting_foreign_stderr_invalidates_the_same_snapshot() -> None:
    value = subject._accounting_valid(
        "Request ID: 123.nqsv\nStarted Request Time: x\n"
        "Ended Request Time: y\nElapse: 180\nExit Status: 0\n",
        "123.nqsv",
        1,
        stderr="Request ID: 999.nqsv\nwall time limit exceeded\n",
    )

    assert value["stream_provenance_valid"] is False
    assert value["exclusive_request_ids_valid"] is False
    assert value["valid"] is False


def test_accounting_unbound_stderr_cause_is_not_extracted() -> None:
    stdout = (
        "Request ID: 123.nqsv\nStarted Request Time: x\n"
        "Ended Request Time: y\nElapse: 180\n"
    )
    validation = subject._accounting_valid(
        stdout,
        "123.nqsv",
        1,
        stderr="wall time limit exceeded\n",
    )
    snapshot = subject._accounting_snapshot_from_results(
        {
            name: {
                "returncode": 0,
                "stdout": stdout,
                "stderr": "wall time limit exceeded\n",
                "accounting_validation": validation,
            }
            for name in ("racctjob", "racctreq")
        }
    )

    assert validation["stderr_cause_request_bound"] is False
    assert snapshot["integrity_valid"] is False
    assert snapshot["termination_cause_classification"] == (
        "UNKNOWN_NOT_RESOURCE_LIMIT"
    )


def test_observer_accounting_rejects_unbound_stderr_cause() -> None:
    observer = signal_observer.Observer.__new__(signal_observer.Observer)
    observer.normalized_request_id = "123.nqsv"
    observer.requested_seconds = 180
    stdout = "Request ID: 123.nqsv\nElapse: 180\n"
    tail = {
        "qstat": {"classification": "OK", "stdout": "", "stderr": ""},
        "racctjob": {
            "classification": "OK",
            "stdout": stdout,
            "stderr": "wall time limit exceeded\n",
        },
        "racctreq": {
            "classification": "OK",
            "stdout": stdout,
            "stderr": "",
        },
    }

    value = observer.validate_accounting(tail)

    assert value["integrity_valid"] is False
    assert value["explicit_walltime_cause"] is False
    assert any("not bound" in error for error in value["integrity_errors"])


def test_signal_log_caps_fail_closed_without_becoming_parse_errors(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(signal_observer, "MAX_SIGNAL_LOG_BYTES_PER_FILE", 32)
    (tmp_path / "events-parent.jsonl").write_bytes(b"x" * 33)
    observer = signal_observer.Observer.__new__(signal_observer.Observer)
    observer.run_root = tmp_path
    observer.mode = "mitigation"
    observer.run_marker = None

    records, errors, parse_errors = observer._read_jsonl_detailed(
        "events-parent.jsonl"
    )

    assert records == []
    assert any("byte cap" in error for error in errors)
    assert parse_errors == []


def test_parse_error_predicate_is_independent_of_structure_errors(
    tmp_path: Path,
) -> None:
    _write_jsonl(
        tmp_path / "events-parent.jsonl",
        [{"schema_version": "wrong", "mode": "mitigation", "event": "x"}],
    )
    observer = signal_observer.Observer.__new__(signal_observer.Observer)
    observer.run_root = tmp_path
    observer.mode = "mitigation"
    observer.run_marker = None

    _records, errors, parse_errors = observer._read_jsonl_detailed(
        "events-parent.jsonl"
    )

    assert any("schema or mode mismatch" in error for error in errors)
    assert parse_errors == []


def test_observer_raw_output_cap_is_fail_closed(
    tmp_path: Path, monkeypatch
) -> None:
    attempt_id = "attempt-cap"
    monkeypatch.setenv("T362_RUN_NONCE", attempt_id)
    monkeypatch.setenv("T362_ATTEMPT_ID", attempt_id)
    monkeypatch.setattr(signal_observer, "MAX_COMMAND_RAW_BYTES_PER_STREAM", 8)
    observer = signal_observer.Observer(
        tmp_path,
        "mitigation",
        "123.nqsv",
        180,
    )

    result = observer.command(
        [sys.executable, "-c", "import os; os.write(1, b'x' * 9)"],
        "cap-fixture",
    )

    assert result["classification"] == "OUTPUT_CAP_EXCEEDED"
    assert result["output_cap_exceeded"] is True
    assert len((observer.raw_root / "0001-cap-fixture.stdout.raw").read_bytes()) == 8


def test_observer_marker_and_canary_reads_fail_closed_at_byte_caps(
    tmp_path: Path, monkeypatch
) -> None:
    attempt_id = "attempt-cap"
    monkeypatch.setenv("T362_RUN_NONCE", attempt_id)
    monkeypatch.setenv("T362_ATTEMPT_ID", attempt_id)
    monkeypatch.setattr(signal_observer, "MAX_MARKER_BYTES_PER_FILE", 8)
    monkeypatch.setattr(signal_observer, "MAX_CANARY_BYTES", 8)
    observer = signal_observer.Observer(
        tmp_path,
        "mitigation",
        "123.nqsv",
        180,
    )
    observer.run_marker = {"run_nonce": attempt_id}
    observer.run_marker_hash = "0" * 64
    (tmp_path / "run_marker.json").write_bytes(b"x" * 9)
    (tmp_path / "canary.txt").write_bytes(b"x" * 9)

    with pytest.raises(signal_observer.ObserverError, match="byte cap"):
        observer._validate_identity_marker("run_marker.json", ready=False)
    observer.acknowledge_canary()
    observer.canary_read_attempts = signal_observer.MAX_CANARY_READ_ATTEMPTS
    observer.acknowledge_canary()

    assert any("canary readback exceeds" in error for error in observer.local_io_cap_errors)
    assert any("canary read attempt count" in error for error in observer.local_io_cap_errors)
    assert not (tmp_path / "canary_readback_ack.json").exists()


def test_observer_qstat_count_cap_returns_fail_closed_without_command(
    tmp_path: Path, monkeypatch
) -> None:
    attempt_id = "attempt-cap"
    monkeypatch.setenv("T362_RUN_NONCE", attempt_id)
    monkeypatch.setenv("T362_ATTEMPT_ID", attempt_id)
    observer = signal_observer.Observer(
        tmp_path,
        "mitigation",
        "123.nqsv",
        180,
    )
    observer.qstat_invocations = signal_observer.MAX_OBSERVER_QSTAT_INVOCATIONS

    result = observer.qstat("cap-fixture")

    assert result["classification"] == "OUTPUT_CAP_EXCEEDED"
    assert result["launch_error"] == "CommandCountCapExceeded"
    assert observer.command_sequence == 0
    assert any("qstat invocation count" in error for error in observer.local_io_cap_errors)


def test_observer_outer_poll_stops_after_bounded_transient_retries(
    tmp_path: Path, monkeypatch
) -> None:
    attempt_id = "attempt-transient"
    monkeypatch.setenv("T362_RUN_NONCE", attempt_id)
    monkeypatch.setenv("T362_ATTEMPT_ID", attempt_id)
    observer = signal_observer.Observer(
        tmp_path,
        "mitigation",
        "123.nqsv",
        180,
    )
    qstat_purposes: list[str] = []

    def qstat(purpose: str, attempts: int = signal_observer.QSTAT_ATTEMPTS):
        qstat_purposes.append(purpose)
        if purpose == "initial-visibility":
            return {"classification": "OK", "visible": True, "state": "QUE"}
        assert purpose == "poll"
        return {
            "classification": "TRANSIENT",
            "visible": False,
            "state": None,
        }

    captured: dict[str, object] = {}
    observer.qstat = qstat
    observer.record = lambda *_args, **_kwargs: None
    observer.inspect_markers = lambda: None
    observer.acknowledge_canary = lambda: None
    observer.collect_scheduler_tail = lambda: {"qstat": {"state": None}}

    def build_final_observation(**kwargs):
        captured.update(kwargs)
        return {}, False

    observer.build_final_observation = build_final_observation
    observer.write_final = lambda _value: None

    assert observer.run() == 3
    assert qstat_purposes == ["initial-visibility", "poll"]
    assert captured["terminal_reason"] == "QSTAT_TRANSIENT"


def test_observer_timeout_still_publishes_capped_raw_files(
    tmp_path: Path, monkeypatch
) -> None:
    attempt_id = "attempt-timeout"
    monkeypatch.setenv("T362_RUN_NONCE", attempt_id)
    monkeypatch.setenv("T362_ATTEMPT_ID", attempt_id)
    observer = signal_observer.Observer(
        tmp_path,
        "mitigation",
        "123.nqsv",
        180,
    )

    def timeout_run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(["qstat"], signal_observer.COMMAND_TIMEOUT_SECONDS)

    monkeypatch.setattr(signal_observer.subprocess, "run", timeout_run)

    result = observer.command(["qstat"], "timeout-fixture")

    assert result["timed_out"] is True
    assert result["returncode"] == 124
    assert (observer.raw_root / "0001-timeout-fixture.stdout.raw").read_bytes() == b""
    assert (observer.raw_root / "0001-timeout-fixture.stderr.raw").read_bytes() == b""


def test_observer_fsync_watchdog_fails_closed(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(signal_observer, "LOCAL_FSYNC_UPPER_SECONDS", 0.01)

    def blocking_fsync(_descriptor: int) -> None:
        time.sleep(1)

    monkeypatch.setattr(signal_observer.os, "fsync", blocking_fsync)

    with pytest.raises(signal_observer.ObserverError, match="fsync exceeds"):
        signal_observer._atomic_publish(
            tmp_path / "bounded.raw",
            b"bounded",
            max_bytes=8,
        )

    assert not (tmp_path / "bounded.raw").exists()


def test_parse_only_error_has_independent_signal_log_predicate(
    tmp_path: Path,
) -> None:
    common = {
        "schema_version": signal_observer.EVENT_SCHEMA,
        "mode": "mitigation",
    }
    required_starts = {
        "job-script": "run_marker_persisted",
        "parent": "parent_started",
        "grandchild": "grandchild_started",
    }
    for layer, required_start in required_starts.items():
        _write_jsonl(
            tmp_path / f"events-{layer}.jsonl",
            [{**common, "event": required_start}],
        )
        _write_jsonl(
            tmp_path / f"control-{layer}.jsonl",
            [
                {**common, "event": "control_start"},
                {**common, "event": "control_normal_exit"},
            ],
        )
        _write_jsonl(
            tmp_path / f"heartbeats-{layer}.jsonl",
            [{**common, "event": "heartbeat"}],
        )
    with (tmp_path / "events-parent.jsonl").open("a", encoding="utf-8") as stream:
        stream.write("{malformed\n")
    observer = signal_observer.Observer.__new__(signal_observer.Observer)
    observer.run_root = tmp_path
    observer.mode = "mitigation"
    observer.run_marker = None

    validation = observer.validate_layers()

    assert validation["valid"] is True
    assert validation["parse_error_free"] is False
    assert validation["parse_errors"]
    assert any("JSONDecodeError" in error for error in validation["errors"])


def test_production_observer_wait_accounts_for_all_count_and_size_caps() -> None:
    command_seconds = (
        signal_observer.FINALIZATION_QSTAT_PHASES
        * signal_observer._bounded_command_upper_seconds(
            signal_observer.QSTAT_ATTEMPTS,
            signal_observer.QSTAT_RETRY_SECONDS,
        )
        + 2
        * signal_observer._bounded_command_upper_seconds(
            signal_observer.ACCOUNTING_ATTEMPTS,
            signal_observer.ACCOUNTING_RETRY_SECONDS,
        )
    )

    assert signal_observer.SIGNAL_LOG_FILE_COUNT == (
        signal_observer.EVENT_LOG_FILE_COUNT
        + signal_observer.CONTROL_LOG_FILE_COUNT
        + signal_observer.HEARTBEAT_LOG_FILE_COUNT
    )
    assert signal_observer.MAX_COMMAND_RAW_FILE_COUNT == (
        signal_observer.MAX_SCHEDULER_COMMANDS * 2
    )
    assert signal_observer.MAX_FINALIZATION_COMMAND_RAW_FILE_COUNT == (
        signal_observer.FINALIZATION_COMMAND_INVOCATIONS * 2
    )
    assert signal_observer.OBSERVER_TERMINATION_TIMEOUT_SECONDS == (
        command_seconds
        + signal_observer._bounded_observer_termination_local_upper_seconds()
    )
    assert subject.OBSERVER_TERMINATION_TIMEOUT_SECONDS == (
        signal_observer.OBSERVER_TERMINATION_TIMEOUT_SECONDS
    )


def test_wave_state_validator_rejects_third_signal_attempt_without_patch(
    tmp_path: Path,
) -> None:
    controller = subject.Controller.__new__(subject.Controller)
    leg = subject.LEG_BY_KEY["t362-mitigation"]
    requests = []
    for ordinal in range(1, 4):
        requests.append(
            {
                "request_ordinal": ordinal,
                "leg": leg.key,
                "attempt_id": f"attempt-{ordinal}",
                "requested_node_min": leg.requested_node_min,
                "cumulative_requested_node_min": ordinal * leg.requested_node_min,
                "qsub_argv": ["qsub", leg.script],
                "qsub_returncode": None,
                "request_id": None,
                "completed": False,
                "admissible": None,
                "evaluation_model": subject.EVALUATION_MODEL,
                "observation_valid": False,
                "attempt_safe": None,
                "accounting_available": False,
                "accounting_integrity_valid": False,
                "termination_cause_consistent": False,
                "probe_cleanup_outcome": "unknown",
                "unsafe_reason": None,
            }
        )
    controller.request_count = 3
    controller.cumulative_node_min = 3 * leg.requested_node_min
    controller.authoritative = {}
    controller.initial_budget = None
    controller.latest_budget = None
    controller.wave_state_path = tmp_path / "wave-state.json"
    controller.wave_state = {
        "schema": subject.WAVE_STATE_SCHEMA,
        "request_limit": subject.REQUEST_LIMIT,
        "requested_node_min_limit": subject.REQUESTED_NODE_MIN_LIMIT,
        "request_count": 3,
        "cumulative_requested_node_min": 3 * leg.requested_node_min,
        "requests": requests,
        "authoritative_attempts": {},
        "initial_budget": None,
        "initial_four_budget_after": None,
        "latest_budget_after_request": None,
    }

    with pytest.raises(subject.ControllerError, match="fixed per-leg cap"):
        controller._persist_wave_state()


def test_end_to_end_sigkill_walltime_unsafe_reaches_summary_rc(
    tmp_path: Path, monkeypatch
) -> None:
    evaluation, completion, final = _production_chain_fixture(
        tmp_path,
        monkeypatch,
        case="sigkill",
    )

    assert final["probe_cleanup_outcome"] == "unsafe"
    assert set(final["signal_observations"].values()) == {"UNKNOWN"}
    assert final["post_restore_canary_readback"]["observed_bytes_hex"] == (
        signal_observer.MUTATED.hex()
    )
    assert evaluation["qwait_validation"]["returncode_raw"] == 9
    assert evaluation["termination_cause_consistent"] is True
    assert evaluation["observation_valid"] is True
    assert evaluation["attempt_safe"] is False
    assert completion["transaction_complete"] is True
    assert completion["returncode"] == 0


def test_erratum2_sigterm_positive_remaining_rc9_is_authoritative(
    tmp_path: Path, monkeypatch
) -> None:
    evaluation, completion, final = _production_chain_fixture(
        tmp_path,
        monkeypatch,
        case="a1",
    )

    assert final["probe_cleanup_outcome"] == "safe"
    assert any(
        value.get("event") == "finally_exit"
        for value in final["cleanup_order"]["matched_events"]
    )
    assert evaluation["qwait_validation"]["returncode_raw"] == 9
    assert evaluation["qwait_validation"]["expected_outcome"] == "elapse-signal"
    assert evaluation["saved_nqsv_stderr_accounting"]["scheduler_signal_name"] == (
        "SIGTERM"
    )
    assert evaluation["saved_nqsv_stderr_accounting"][
        "remaining_elapse_seconds"
    ] == 46
    assert evaluation["termination_cause_consistent"] is True
    assert evaluation["observation_valid"] is True
    assert evaluation["attempt_safe"] is True
    assert completion["transaction_complete"] is True
    assert completion["returncode"] == 0


def test_erratum2_sigterm_zero_remaining_is_cause_inconsistent(
    tmp_path: Path, monkeypatch
) -> None:
    evaluation, completion, _final = _production_chain_fixture(
        tmp_path,
        monkeypatch,
        case="mixed",
    )

    assert evaluation["saved_nqsv_stderr_accounting"]["scheduler_signal_name"] == (
        "SIGTERM"
    )
    assert evaluation["saved_nqsv_stderr_accounting"][
        "remaining_elapse_seconds"
    ] == 0
    assert evaluation["termination_cause_consistent"] is False
    assert evaluation["observation_valid"] is False
    assert completion["transaction_complete"] is False


def test_end_to_end_term_wait_natural_unsafe_reaches_summary_rc(
    tmp_path: Path, monkeypatch
) -> None:
    evaluation, completion, final = _production_chain_fixture(
        tmp_path,
        monkeypatch,
        case="term-wait",
    )

    assert final["unsafe_reason"] == "cleanup_order_invalid"
    assert evaluation["qwait_validation"]["expected_outcome"] == "normal"
    assert evaluation["observation_valid"] is True
    assert evaluation["attempt_safe"] is False
    assert completion["returncode"] == 0


def test_end_to_end_safe_natural_reaches_summary_rc(
    tmp_path: Path, monkeypatch
) -> None:
    evaluation, completion, final = _production_chain_fixture(
        tmp_path,
        monkeypatch,
        case="safe",
    )

    assert final["probe_cleanup_outcome"] == "safe"
    assert evaluation["qwait_validation"]["expected_outcome"] == "normal"
    assert evaluation["observation_valid"] is True
    assert evaluation["attempt_safe"] is True
    assert completion["returncode"] == 0
