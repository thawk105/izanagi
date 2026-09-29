from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from types import SimpleNamespace

import pytest

from orchestrator.campaign.t810_preregistration import (
    APPROVAL_RECEIPT_SCHEMA_VERSION,
    PREREG_PATH,
    ApprovalReceipt,
    load_t810_preregistration,
)
from orchestrator.campaign.t810_validator import (
    GitIdentity,
    ValidationLineage,
    git_identity_digest,
    resolve_git_identity,
)
from tools.pegasus import t810_coordinator as C
from tools.pegasus import t810_harness_schema as S
from tools.pegasus import t810_pbs_wrapper as W
from tools.pegasus import t810_runner_policy as R


H = "a" * 64
PREREG_SHA256 = "3052af20993481730a826ce08ee26289948f29836d43afb2d7c743cfdd12e404"
APPROVAL_ID = "fixture-stage1-review-t810-v1"
FIXTURE = Path(__file__).parent / "fixtures" / "t810" / "coordinator_qsub_success.json"
LIMITATIONS = [
    "approval_receipt_trust_root_absent",
    "budget_ledger_trust_root_absent",
    "execution_mediation_incomplete",
    "guard_snapshot_to_release_race_not_eliminated",
    "repository_absence_not_proven_from_node",
    "shared_mount_repository_reachability_not_eliminated",
]
_LIVE_AUTHORITY_NODES = frozenset({
    "test_prepare_group_rejects_forged_git_identity_before_any_mkdir",
    "test_prepare_group_rejects_self_consistent_foreign_git_identity_before_any_mkdir",
    "test_prepare_group_accepts_external_root_with_anchor_union",
})
# These nodes intentionally call the authority scanner with a GitIdentity whose
# complete common-dir/worktree registration graph they construct under tmp_path.
# Keeping this ledger separate from the live allowlist distinguishes direct tests
# of the scanner from callers that must use the patched hermetic authority seam.
_HERMETIC_DIRECT_AUTHORITY_NODES = frozenset({
    "test_git_common_dir_skips_unlocked_missing_registration_file",
    "test_git_common_dir_rejects_locked_missing_registration_file",
    "test_git_common_dir_rejects_non_enoent_registration_open_error",
    "test_git_common_dir_rejects_lock_stat_error",
    "test_git_common_dir_rejects_symlink_registration_file",
    "test_git_common_dir_rejects_non_regular_registration_file",
    "test_git_common_dir_rejects_registration_changed_during_read",
    "test_git_common_dir_derives_main_and_sibling_worktree_roots",
    "test_git_common_dir_preserves_missing_registered_worktree_claim",
})


def _registration_identity(tmp_path: Path) -> tuple[GitIdentity, Path]:
    main = tmp_path / "registration-case" / "main"
    common = main / ".git"
    admin = common / "worktrees" / "subject"
    admin.mkdir(parents=True)
    return GitIdentity(str(main), str(common), str(common)), admin


@pytest.fixture
def hermetic_git_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> GitIdentity:
    main = tmp_path / "authority" / "main"
    common = main / ".git"
    linked = tmp_path / "authority" / "linked"
    admin = common / "worktrees" / "linked"
    admin.mkdir(parents=True)
    linked.mkdir(parents=True)
    linked_gitdir = linked / ".git"
    linked_gitdir.write_text("gitdir: fixture\n", encoding="utf-8")
    (admin / "gitdir").write_text(str(linked_gitdir) + "\n", encoding="utf-8")
    identity = GitIdentity(
        str(main.resolve(strict=True)),
        str(common.resolve(strict=True)),
        str(common.resolve(strict=True)),
    )
    assert C.repository_roots_from_git_identity(identity) == frozenset({
        main.resolve(strict=True), linked.resolve(strict=True),
    })
    monkeypatch.setattr(C, "resolve_git_identity", lambda _source: identity)
    return identity


def _with_live_authority_retry(operation):
    for attempt in range(3):
        try:
            return operation()
        except C.T810CoordinatorError as exc:
            if "worktree registration" not in str(exc) or attempt == 2:
                raise
    raise AssertionError("unreachable live-authority retry state")


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
    ratified = status == "ratified"
    return {
        "schema_version": "t810-admission-policy/v1",
        "parallel_guard": {"a_series_identity": {
            "status": "resolved" if ratified else "unresolved", "field": "Job_Name",
            "pilot_patterns": ["^pilot$"] if ratified else [],
            "main_patterns": ["^main$"] if ratified else [],
        }},
        "approved_hostnames": {
            "status": status,
            "hostnames": hosts or ([f"node{i:02d}" for i in range(S.NODE_COUNT)] if ratified else []),
        },
        "qsub": {
            "status": status, "project": "project" if ratified else None,
            "queue": "queue" if ratified else None,
            "walltime_by_run_kind": {
                kind: "00:10:00" if ratified else None
                for kind in ("builder", "liveness", "main")
            },
        },
        "budget": {
            "status": status, "accounting_unit": "node-seconds",
            "total_node_seconds": 100000 if ratified else None,
            "estimates": {
                kind: {
                    "walltime_seconds": 10 if ratified else None,
                    "jobs_per_attempt": S.NODE_COUNT if ratified else None,
                    "node_seconds_per_attempt": 10 * S.NODE_COUNT if ratified else None,
                    "provisional_note": "fixture",
                } for kind in ("builder", "liveness", "main")
            },
            "attempt_policy": {
                "builder_attempts": 1 if ratified else None,
                "liveness_max_attempts": 2 if ratified else None,
                "main_max_attempts_ref": "preregistration.terminal.retry.max_attempts" if ratified else None,
            },
            "ledger": {
                "schema_version": "t810-budget-ledger-event/v1",
                "location": "repository-external", "lock_method": "flock",
                "counted_statuses": ["reserved", "consumed"], "genesis_sha256": H,
            },
            "admission": {
                "formula": "0 < required <= remaining", "integer_arithmetic": "exact",
                "max_node_seconds": 2**63 - 1,
            },
        },
        "limitations": LIMITATIONS,
    }


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(S.canonical_json_bytes(value) + b"\n")
def _config(tmp_path: Path, *, ordinal: int = 1) -> dict:
    prereg = _preregistration()
    output = tmp_path / "output"
    work = tmp_path / "work"
    package = tmp_path / "package"
    package.mkdir(parents=True, exist_ok=True)
    binary = package / "CCBench"
    binary.write_bytes(b"coordinator-production-route-fixture")
    binary.chmod(0o700)
    binary_sha256 = hashlib.sha256(binary.read_bytes()).hexdigest()
    shipped_package = Path(C.__file__).resolve().parent
    wrapper = package / "wrapper.py"
    wrapper.write_bytes((shipped_package / "t810_pbs_wrapper.py").read_bytes())
    wrapper_sha256 = hashlib.sha256(wrapper.read_bytes()).hexdigest()
    for dependency in ("t810_harness_schema.py", "t810_runner_policy.py"):
        (package / dependency).write_bytes((shipped_package / dependency).read_bytes())
    (package / "dependencies.json").write_bytes(b"dependencies")
    policy = _policy()
    runner_policy_sha256 = S.canonical_sha256(
        R.build_runner_policy(prereg, executable_sha256=binary_sha256),
    )
    slots = []
    for index in range(S.NODE_COUNT):
        slot_id = f"slot-{index:02d}"
        stdout = output / slot_id / "pbs.stdout.log"
        stderr = output / slot_id / "pbs.stderr.log"
        script = work / slot_id / "job.pbs"
        qsub = [
            "qsub", "-A", "project", "-q", "queue", "-b", "1",
            "-l", "elapstim_req=00:10:00", "-N", f"t810-{index:02d}",
            "-o", str(stdout), "-e", str(stderr), str(script),
        ]
        slots.append({
            "slot_id": slot_id,
            "logical_request_id": f"logical-{index:02d}",
            "job_name": f"t810-{index:02d}", "qsub_argv": qsub,
            "wrapper_argv": [
                "python3.10", str(package / "wrapper.py"), "--request",
                str(work / slot_id / "wrapper-request.json"),
            ],
            "pbs_stdout_path": str(stdout), "pbs_stderr_path": str(stderr),
            "binary_source_path": str(binary), "binary_sha256": binary_sha256,
            "wrapper_path": str(wrapper), "wrapper_sha256": wrapper_sha256,
            "runner_policy_path": str(work / slot_id / "runner-policy.json"),
            "runner_policy_sha256": runner_policy_sha256,
            "expected_dependency_manifest_sha256": H,
            "expected_module_list_sha256": H, "expected_numa_nodes": 4,
            "script_path": str(script),
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
    policy_path = tmp_path / "admission-policy.json"
    guard_path = tmp_path / "guard-receipt.json"
    budget_path = tmp_path / "budget-receipt.json"
    _write(policy_path, policy)
    guard = {
        "schema_version": "t810-guard-receipt/v1", "launch_intent_sha256": intent_sha,
        "phase": "pre-release", "policy_sha256": intent["policy_sha256"],
        "snapshot_sha256": H, "a_series_identity_status": "resolved",
        "a_series_jobs": [], "co_location_conflicts": [], "decision": "allow",
        "reason_codes": [], "b_request_ids": [], "withdrawal_actions": [],
        "limitations": LIMITATIONS, "created_at": "2026-08-12T00:00:00Z",
    }
    budget = {
        "schema_version": "t810-budget-receipt/v1", "launch_intent_sha256": intent_sha,
        "policy_sha256": intent["policy_sha256"], "estimates_sha256": H,
        "ledger_path": str(tmp_path / "ledger.jsonl"),
        "ledger_sha256_before": H, "ledger_sha256_after": "b" * 64,
        "reservation_id": H, "run_kind": "liveness", "requested_attempts": 1,
        "estimate_per_attempt_node_seconds": 130, "required_node_seconds": 130,
        "total_node_seconds": 100000, "counted_node_seconds": 0,
        "remaining_node_seconds": 99870, "admitted": True, "reason": "admitted",
        "created_at": "2026-08-12T00:00:00Z", "limitations": LIMITATIONS,
    }
    _write(guard_path, guard)
    _write(budget_path, budget)
    identity = C.resolve_git_identity(Path(C.__file__).resolve().parents[2])
    return {
        "launch_intent": intent, "admission_policy_path": str(policy_path),
        "guard_receipt_path": str(guard_path), "budget_receipt_path": str(budget_path),
        "release_nonce": "fixture-release-nonce",
        "manifest_created_at": "2026-08-12T00:00:01Z",
        "validator_kwargs": {
            "repo_root": identity.repo_realpath, "approved_git_identity": {
                "repo_realpath": identity.repo_realpath,
                "git_dir_realpath": identity.git_dir_realpath,
                "common_dir_realpath": identity.common_dir_realpath,
            },
            "approved_git_identity_sha256": git_identity_digest(identity),
            "writable_root": str(tmp_path / "writable"),
            "manifest_path": str(tmp_path / "frozen-manifest.json"),
            "manifest_root": str(tmp_path), "expected_manifest_sha256": H,
            "executable": str(binary), "expected_executable_sha256": binary_sha256,
            "attempt_root": str(tmp_path / "attempt"), "attempt_receipt": None,
            "attempt_nonce": "attempt-1", "pre_invocation_nonce": "pre-1",
        },
    }


def _rebind_work_root(config: dict, work_root: Path) -> None:
    intent = config["launch_intent"]
    intent["work_root"] = str(work_root)
    for slot in intent["slots"]:
        slot_root = work_root / slot["slot_id"]
        slot["script_path"] = str(slot_root / "job.pbs")
        slot["wrapper_argv"][3] = str(slot_root / "wrapper-request.json")
        slot["qsub_argv"][-1] = slot["script_path"]
    intent_sha256 = S.canonical_sha256(intent)
    for field in ("guard_receipt_path", "budget_receipt_path"):
        path = Path(config[field])
        receipt = json.loads(path.read_text(encoding="utf-8"))
        receipt["launch_intent_sha256"] = intent_sha256
        _write(path, receipt)


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
def _token(config: dict, prereg=None):
    prereg = prereg or _preregistration()
    return S.verify_launch_authorization(
        _witness(config, prereg), run_kind=config["launch_intent"]["run_kind"],
        preregistration_sha256=prereg.sha256,
        policy_sha256=config["launch_intent"]["policy_sha256"],
    )
def _preview(config: dict, prereg):
    intent = config["launch_intent"]
    manifest = {
        "schema_version": S.GROUP_MANIFEST_SCHEMA, "group_id": intent["group_id"],
        "created_at": config["manifest_created_at"],
        "launch_intent_sha256": S.canonical_sha256(intent),
        "guard_receipt_sha256": S.canonical_sha256(json.loads(Path(config["guard_receipt_path"]).read_text())),
        "budget_receipt_sha256": S.canonical_sha256(json.loads(Path(config["budget_receipt_path"]).read_text())),
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
                token.replace("$OUTPUT_ROOT", str(output_root)).replace(
                    "$WORK_ROOT", str(output_root.parent / "work"),
                ) for token in item["command_argv"]
            ]
            self.transcripts.append(item)
        self.manifest_path = manifest_path
        self.calls: list[list[str]] = []

    def __call__(self, token, prepared, argv, *, cwd, env):
        assert isinstance(token, S.AuthorizationToken)
        assert isinstance(prepared, C.PreparedGroup)
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
    prepared = C.prepare_group(
        config, prereg, S.verify_launch_authorization(
            _witness(config, prereg), run_kind="liveness",
            preregistration_sha256=prereg.sha256,
            policy_sha256=config["launch_intent"]["policy_sha256"],
        ), repository_roots={Path("/repository")},
    )
    scheduler = RecordedScheduler(FIXTURE, prepared.output_root, prepared.manifest_path)
    submission = C.submit_group(
        prepared, prepared.authorization, scheduler_run=scheduler,
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
        "previous_event_sha256": None if sequence == 0 else H,
        "limitations": {
            "shared_mount_repository_reachability_not_eliminated": True,
            "execution_mediation_incomplete": True,
            "guard_snapshot_to_release_race_not_eliminated": True,
            "approval_receipt_trust_root_absent": True,
            "repository_absence_not_proven_from_node": True,
            "budget_ledger_trust_root_absent": True,
        },
        "payload": payload,
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
            "binary_source_sha256": prepared.launch_intent["slots"][index]["binary_sha256"],
            "binary_copy_sha256": prepared.launch_intent["slots"][index]["binary_sha256"],
            "dependency_manifest_sha256": H, "module_list_sha256": H,
            "trace_symbols": [],
            "isolation_before": {"inventory_sha256": H, "competing_processes_sha256": H},
            "observed_submission_argv": list(qsub),
            "repo_absence": {"package_repo_free": False, "roots_repo_external": False,
                             "git_ancestor_absent": True, "pbs_workdir_repo_external": False},
            "passed": True, "reason_codes": [],
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
            "pre_measurement_process_scan": {
                "competing_processes": [], "unreadable": [],
            },
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
def _completion_receipts(prepared, prereg, *, dropped: set[str] | None = None) -> dict[str, C.NodeReceipt]:
    dropped = dropped or set()
    actual = _presence(prereg, "terminal_reduced" if dropped else "valid")
    receipts = {}
    for index in range(S.NODE_COUNT):
        slot = f"slot-{index:02d}"
        preflight = _ready_events(prepared)[index]
        ack = _node_event(prepared, slot, "start_ack", {
            "release_marker_sha256": H, "cancel_marker_absent": True,
            "ack_nonce": f"ack-{index:02d}",
            "pre_measurement_process_scan": {"competing_processes": [], "unreadable": []},
        }, sequence=1)
        ack["previous_event_sha256"] = S.canonical_sha256(preflight)
        terminal_payload = {
            "state": "terminal_reduced" if slot in dropped else "valid",
            "reason_codes": ["single_job_dropped"] if slot in dropped else ["all_jobs_complete"],
            "measurement_started": slot not in dropped,
            "completed_rounds": 0 if slot in dropped else S.ROUND_COUNT,
        }
        measurement = None
        events = [preflight, ack]
        if slot not in dropped:
            rounds = [
                {"index": round_id, "started_at": "a", "ended_at": "b",
                 "effective_clock": 2.0, "throughput": 3.0, "exit_code": 0}
                for round_id in range(1, S.ROUND_COUNT + 1)
            ]
            measurement = _node_event(prepared, slot, "measurement", {
                "rounds": rounds, "benchmark_rc": 0,
                "binary_after_sha256": prepared.launch_intent["slots"][index][
                    "binary_sha256"
                ],
                "isolation_after": {"inventory_sha256": H, "competing_processes_sha256": H},
            }, sequence=2)
            measurement["previous_event_sha256"] = S.canonical_sha256(ack)
            events.append(measurement)
        terminal = _node_event(
            prepared, slot, "terminal", terminal_payload,
            sequence=3 if measurement is not None else 2,
        )
        terminal["previous_event_sha256"] = S.canonical_sha256(events[-1])
        events.append(terminal)
        raw = b"".join(S.canonical_json_bytes(event) + b"\n" for event in events)
        work_path = prepared.work_root / slot / "node-receipt.jsonl"
        work_path.parent.mkdir(parents=True, exist_ok=True)
        work_path.write_bytes(raw)
        output_path = prepared.output_root / slot / "node-receipt.jsonl"
        output_path.write_bytes(raw)
        measurement_required = not dropped or len(dropped) == 1 or slot not in dropped
        if measurement_required:
            (output_path.parent / "measurements.jsonl").write_text("{}\n", encoding="utf-8")
        receipts[slot] = C.NodeReceipt(work_path, raw, S.sha256_bytes(raw), tuple(events))
    if len(dropped) <= 1:
        (prepared.output_root / "estimate.json").write_text("{}\n", encoding="utf-8")
    return receipts


def _publish_fixture_phase(prepared, phase: str, release_sha: str) -> None:
    for index in range(S.NODE_COUNT):
        slot = f"slot-{index:02d}"
        preflight = _ready_events(prepared)[index]
        events = [preflight]
        if phase in {"ack", "terminal"}:
            ack = _node_event(prepared, slot, "start_ack", {
                "release_marker_sha256": release_sha, "cancel_marker_absent": True,
                "ack_nonce": f"ack-{index:02d}",
                "pre_measurement_process_scan": {"competing_processes": [], "unreadable": []},
            }, sequence=1)
            ack["previous_event_sha256"] = S.canonical_sha256(preflight)
            events.append(ack)
        if phase == "terminal":
            measurement = _node_event(prepared, slot, "measurement", {
                "rounds": [
                    {"index": round_id, "started_at": "a", "ended_at": "b",
                     "effective_clock": 2.0, "throughput": 3.0, "exit_code": 0}
                    for round_id in range(1, S.ROUND_COUNT + 1)
                ],
                "benchmark_rc": 0,
                "binary_after_sha256": prepared.launch_intent["slots"][index][
                    "binary_sha256"
                ],
                "isolation_after": {"inventory_sha256": H, "competing_processes_sha256": H},
            }, sequence=2)
            measurement["previous_event_sha256"] = S.canonical_sha256(events[-1])
            events.append(measurement)
            terminal = _node_event(prepared, slot, "terminal", {
                "state": "valid", "reason_codes": ["all_jobs_complete"],
                "measurement_started": True, "completed_rounds": S.ROUND_COUNT,
            }, sequence=3)
            terminal["previous_event_sha256"] = S.canonical_sha256(events[-1])
            events.append(terminal)
        raw = b"".join(S.canonical_json_bytes(event) + b"\n" for event in events)
        work_path = Path(prepared.launch_intent["work_root"]) / slot / "node-receipt.jsonl"
        work_path.parent.mkdir(parents=True, exist_ok=True)
        work_path.write_bytes(raw)
        if phase == "terminal":
            output_path = Path(prepared.launch_intent["output_root"]) / slot / "node-receipt.jsonl"
            output_path.write_bytes(raw)
            (output_path.parent / "measurements.jsonl").write_text("{}\n", encoding="utf-8")
    if phase == "terminal":
        (Path(prepared.launch_intent["output_root"]) / "estimate.json").write_text(
            "{}\n", encoding="utf-8",
        )
def test_prepare_group_dag_is_create_only_and_policy_hosts_are_ratified(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    prereg, config, prepared, _, scheduler = _prepared(tmp_path)
    assert prepared.intent_path.is_file()
    assert prepared.manifest_path.is_file()
    assert len(scheduler.calls) == S.NODE_COUNT
    assert prepared.manifest["launch_intent_sha256"] == S.canonical_sha256(config["launch_intent"])
    assert prepared.manifest["release_token_commitment"] == S.release_token_commitment(config["release_nonce"])
    for slot in prepared.launch_intent["slots"]:
        script = Path(slot["script_path"])
        command = script.read_text(encoding="utf-8").splitlines()[-1]
        argv = shlex.split(command.removeprefix("exec "))
        assert argv == slot["wrapper_argv"]
        parsed = W._argument_parser().parse_args(argv[2:])
        request_path = Path(parsed.request)
        request = json.loads(request_path.read_text(encoding="utf-8"))
        assert request_path.is_absolute()
        assert request["request_path"] == str(request_path)
        assert {"pbs_request_id", "assigned_hostname", "allocated_cpus"}.isdisjoint(request)
        assert script.stat().st_mode & 0o700 == 0o700
    with pytest.raises(C.T810CoordinatorError, match="create-only"):
        C.prepare_group(config, prereg, _token(config, prereg), repository_roots={Path("/repository")})
    denied = _config(tmp_path / "unratified")
    denied_policy = json.loads(Path(denied["admission_policy_path"]).read_text())
    denied_policy["approved_hostnames"] = {"status": "unratified", "hostnames": []}
    _write(Path(denied["admission_policy_path"]), denied_policy)
    denied["launch_intent"]["policy_sha256"] = S.canonical_sha256(denied_policy)
    Path(denied["guard_receipt_path"]).unlink()
    with pytest.raises(C.T810CoordinatorError, match="not fully ratified"):
        C.prepare_group(denied, prereg, _token(denied, prereg), repository_roots={Path("/repository")})
def test_cli_and_effect_entries_deny_missing_or_wrong_witness(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    assert C.main(["--config", "absent", "--approval-receipt", "absent"]) == 2
    prereg = _preregistration()
    config = _config(tmp_path)
    prepared = C.prepare_group(config, prereg, _token(config, prereg), repository_roots={Path("/repository")})
    bomb = lambda *args, **kwargs: pytest.fail("scheduler reached")
    with pytest.raises(C.T810CoordinatorError, match="witness"):
        C.submit_group(prepared, None, scheduler_run=bomb, wall_clock=lambda: "now")
    wrong = _witness(config, prereg, run_kinds=["main"])
    with pytest.raises(C.T810CoordinatorError, match="AuthorizationToken"):
        C.submit_group(prepared, wrong, scheduler_run=bomb, wall_clock=lambda: "now")
@pytest.mark.parametrize(
    ("mutation", "reason"),
    [("duplicate_host", "duplicate_hostname"), ("binary", "binary_copy_hash_mismatch"),
     ("argv", "submission_argv_mismatch"), ("quiet", "quiet_gate_failed"),
     ("repo_positive", "preflight_failed")],
)
def test_ready_barrier_recomputes_raw_evidence(
    tmp_path: Path, mutation: str, reason: str,
    hermetic_git_identity: GitIdentity,
) -> None:
    _, _, prepared, _, _ = _prepared(tmp_path)
    events = _ready_events(prepared)
    if mutation == "duplicate_host":
        events[-1]["payload"]["assigned_hostname"] = "node00"
        events[-1]["payload"]["actual_hostname"] = "node00"
    elif mutation == "binary":
        events[-1]["payload"]["binary_copy_sha256"] = "b" * 64
    elif mutation == "argv":
        events[-1]["payload"]["observed_submission_argv"].append("--extra")
    elif mutation == "repo_positive":
        events[-1]["payload"]["repo_absence"]["package_repo_free"] = True
    else:
        events[-1]["payload"]["quiet_samples"][-1]["load_average_1m"] = 1.0000001
    decision = C.evaluate_ready_barrier(prepared, events, elapsed_seconds=1199)
    assert decision.status == "cancel"
    assert reason in decision.reason_codes


def test_canonical_wrapper_preflight_passes_ready_barrier(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    _, _, prepared, _, _ = _prepared(tmp_path)
    events = _ready_events(prepared)
    assert all(event["payload"]["repo_absence"] == {
        "package_repo_free": False,
        "roots_repo_external": False,
        "git_ancestor_absent": True,
        "pbs_workdir_repo_external": False,
    } for event in events)
    decision = C.evaluate_ready_barrier(prepared, events, elapsed_seconds=1199)
    assert decision.status == "release" and decision.reason_codes == ()
def test_submission_must_be_complete_before_barrier_and_timeout_boundary(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    prereg = _preregistration()
    config = _config(tmp_path)
    prepared = C.prepare_group(config, prereg, _token(config, prereg), repository_roots={Path("/repository")})
    with pytest.raises(C.T810CoordinatorError, match="submission receipt"):
        C.evaluate_ready_barrier(prepared, [], elapsed_seconds=1200)
    scheduler = RecordedScheduler(FIXTURE, prepared.output_root, prepared.manifest_path)
    C.submit_group(prepared, prepared.authorization, scheduler_run=scheduler, wall_clock=lambda: "now")
    assert C.evaluate_ready_barrier(prepared, [], elapsed_seconds=1199.999).status == "waiting"
    timed_out = C.evaluate_ready_barrier(prepared, [], elapsed_seconds=1200)
    assert timed_out.status == "cancel" and timed_out.reason_codes == ("ready_timeout",)
def test_release_commitment_cancel_recheck_and_create_only(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    prereg, config, prepared, _, _ = _prepared(tmp_path)
    witness = prepared.authorization
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
    hermetic_git_identity: GitIdentity,
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
def test_ack_marker_mismatch_duplicate_unknown_and_missing_are_rejected(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
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
    assert {"release_marker_mismatch", "ack_duplicate", "ack_unknown_slot", "ack_missing"} <= set(decision.reason_codes)


def test_start_ack_recomputes_pre_measurement_process_scan(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    _, _, prepared, _, _ = _prepared(tmp_path)
    release_sha = _release_sha(prepared)
    events = _ack_events(prepared, release_sha)
    events[0]["payload"]["pre_measurement_process_scan"]["competing_processes"] = [{
        "pid": 12, "uid": 1000, "cpu_affinity": [0], "command": "worker",
    }]
    events[1]["payload"]["pre_measurement_process_scan"]["unreadable"] = [{
        "pid": 13, "fields": ["uid", "cpu_affinity"],
    }]
    decision = C.evaluate_start_acks(
        prepared, [(event, 100) for event in events],
        release_marker_sha256=release_sha, release_published_ns=100,
    )
    assert decision.accepted is False
    assert {"competing_process_detected", "process_observation_unreadable"} <= set(
        decision.reason_codes
    )
@pytest.mark.parametrize(
    ("drop_count", "state"),
    [(0, "valid"), (1, "terminal_reduced"), (2, "incomplete_after_start")],
)
def test_completion_state_rows_and_exact_n_receipts(
    tmp_path: Path, drop_count: int, state: str,
    hermetic_git_identity: GitIdentity,
) -> None:
    prereg, _, prepared, _, _ = _prepared(tmp_path)
    dropped = {f"slot-{S.NODE_COUNT - index - 1:02d}" for index in range(drop_count)}
    receipts = _completion_receipts(prepared, prereg, dropped=dropped)
    terminal = C.verify_completion(
        prepared, receipts, release_event_sha256=H, start_spread_ns=1,
        pre_validator_receipt_sha256=H, post_validator_receipt_sha256=H,
    )
    assert terminal["state"] == state
    assert terminal["retry_allowed"] is False
def test_completion_rejects_orphan_unknown_duplicate_and_receiptless_submission(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    prereg, _, prepared, _, _ = _prepared(tmp_path)
    receipts = _completion_receipts(prepared, prereg)
    del receipts["slot-12"]
    receipts["slot-99"] = receipts["slot-00"]
    with pytest.raises(C.T810CoordinatorError, match="one file-backed terminal receipt per slot"):
        C.verify_completion(
            prepared, receipts, release_event_sha256=H, start_spread_ns=1,
            pre_validator_receipt_sha256=H, post_validator_receipt_sha256=H,
        )
def test_frozen_boundary_reason_table_and_retry_rows_are_all_used(
    hermetic_git_identity: GitIdentity,
) -> None:
    expected_rows = {
        ("pre_release", "ready_timeout"): "pre_release_invalid",
        ("pre_release", "hostname_count_mismatch"): "pre_release_invalid",
        ("post_release_pre_measurement", "start_spread_exceeded"):
            "post_release_pre_measurement_invalid",
        ("post_release_pre_measurement", "dependency_manifest_mismatch"):
            "post_release_pre_measurement_invalid",
        ("after_measurement_start", "insufficient_completions"): "incomplete_after_start",
        ("after_measurement_start", "presence_matrix_mismatch"): "incomplete_after_start",
        ("after_measurement_start", "single_job_dropped"): "terminal_reduced",
        ("after_measurement_start", "all_jobs_complete"): "valid",
    }
    for (boundary, reason), expected in expected_rows.items():
        assert S.classify_terminal_state(boundary, reason) == expected
    for state in {
        "pre_release_invalid", "post_release_pre_measurement_invalid",
        "incomplete_after_start", "terminal_reduced", "valid",
    }:
        assert S.retry_allowed(state, 1) is (state == "pre_release_invalid")
        assert S.retry_allowed(state, 2) is False


def test_node_receipt_hash_chain_and_actual_bytes_digest_are_enforced(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    prereg, _, prepared, _, _ = _prepared(tmp_path)
    receipts = _completion_receipts(prepared, prereg)
    receipt = receipts["slot-00"]
    assert receipt.sha256 == S.sha256_bytes(receipt.path.read_bytes())
    request = C._complete_submission(prepared)["requests"][0]
    lines = receipt.path.read_bytes().splitlines()
    second = S.parse_json(lines[1])
    second["previous_event_sha256"] = "b" * 64
    receipt.path.write_bytes(lines[0] + b"\n" + S.canonical_json_bytes(second) + b"\n")
    with pytest.raises(C.T810CoordinatorError, match="hash chain"):
        C._read_node_receipt(prepared, request)


def test_terminal_state_two_precedes_twelve_completion_reduction(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    prereg, _, prepared, _, _ = _prepared(tmp_path)
    receipts = _completion_receipts(prepared, prereg)
    dropped = receipts["slot-12"]
    preflight, ack = dropped.events[:2]
    terminal = _node_event(prepared, "slot-12", "terminal", {
        "state": "post_release_pre_measurement_invalid",
        "reason_codes": ["dependency_manifest_mismatch"],
        "measurement_started": False, "completed_rounds": 0,
    }, sequence=2)
    terminal["previous_event_sha256"] = S.canonical_sha256(ack)
    events = (preflight, ack, terminal)
    raw = b"".join(S.canonical_json_bytes(event) + b"\n" for event in events)
    dropped.path.write_bytes(raw)
    (prepared.output_root / "slot-12" / "node-receipt.jsonl").write_bytes(raw)
    (prepared.output_root / "slot-12" / "measurements.jsonl").unlink()
    (prepared.output_root / "estimate.json").unlink()
    receipts["slot-12"] = C.NodeReceipt(dropped.path, raw, S.sha256_bytes(raw), events)
    result = C.verify_completion(
        prepared, receipts, release_event_sha256=H, start_spread_ns=1,
        pre_validator_receipt_sha256=H, post_validator_receipt_sha256=H,
    )
    assert result["state"] == "post_release_pre_measurement_invalid"
    assert result["reason_codes"] == ["dependency_manifest_mismatch"]


def test_config_decoder_is_exact_and_restores_path_and_git_identity(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    config = _config(tmp_path)
    decoded = C.decode_config(config)
    assert isinstance(decoded["admission_policy_path"], Path)
    assert isinstance(decoded["validator_kwargs"]["repo_root"], Path)
    assert isinstance(decoded["validator_kwargs"]["approved_git_identity"], GitIdentity)
    config["ready_events"] = []
    with pytest.raises(C.T810CoordinatorError, match="unknown or missing"):
        C.decode_config(config)
    missing = _config(tmp_path / "missing")
    del missing["validator_kwargs"]["executable"]
    with pytest.raises(C.T810CoordinatorError, match="validator kwargs"):
        C.decode_config(missing)


def test_wait_for_node_files_uses_injected_clock_and_sleep(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    _, _, prepared, _, _ = _prepared(tmp_path)
    now = [0]
    calls = []
    def injected_sleep(seconds: float) -> None:
        calls.append(seconds)
        now[0] = S.READY_TIMEOUT_SECONDS * 1_000_000_000
    receipts, received = C._wait_for_phase(
        prepared, "preflight", clock_ns=lambda: now[0], sleep=injected_sleep,
        timeout_seconds=S.READY_TIMEOUT_SECONDS,
    )
    assert receipts == {} and received == {}
    assert calls


def test_subprocess_and_publication_effects_reject_raw_dict_token(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    prereg = _preregistration()
    config = _config(tmp_path)
    with pytest.raises(C.T810CoordinatorError, match="AuthorizationToken"):
        C.prepare_group(config, prereg, _witness(config), repository_roots={Path("/repo")})
    with pytest.raises(C.T810CoordinatorError, match="AuthorizationToken"):
        C._subprocess_scheduler({}, object(), ["qsub"], cwd=str(tmp_path), env={})
    prepared = C.prepare_group(
        config, prereg, _token(config, prereg), repository_roots={Path("/repo")},
    )
    with pytest.raises(C.T810CoordinatorError, match="witness"):
        C._append_coordinator_event(
            prepared, {}, "manifest_committed", {"manifest_sha256": H},
            wall_time="now", monotonic_ns=0,
        )


def test_arbitrary_qsub_is_rejected_before_scheduler_effect(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    prereg = _preregistration()
    config = _config(tmp_path)
    slot = config["launch_intent"]["slots"][0]
    slot["qsub_argv"] = [
        "/bin/sh", "-o", slot["pbs_stdout_path"], "-e", slot["pbs_stderr_path"],
        slot["script_path"],
    ]
    with pytest.raises(C.T810CoordinatorError, match="canonical form"):
        C.prepare_group(
            config, prereg, _token(config, prereg), repository_roots={Path("/repo")},
        )
    _, _, prepared, _, _ = _prepared(tmp_path / "adapter")
    with pytest.raises(C.T810CoordinatorError, match="canonical submission"):
        C._subprocess_scheduler(
            prepared.authorization, prepared, ["qsub"],
            cwd=str(prepared.work_root), env={},
        )


def test_modified_pbs_script_is_rejected_at_scheduler_effect(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    _, _, prepared, _, _ = _prepared(tmp_path)
    slot = prepared.launch_intent["slots"][0]
    Path(slot["script_path"]).write_text("#!/bin/sh\nexec /bin/false\n", encoding="utf-8")
    with pytest.raises(C.T810CoordinatorError, match="frozen wrapper argv"):
        C._subprocess_scheduler(
            prepared.authorization, prepared, slot["qsub_argv"],
            cwd=str(prepared.work_root), env={},
        )


def test_scheduler_adapter_rejects_wrapper_changed_after_prepare(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    hermetic_git_identity: GitIdentity,
) -> None:
    _, _, prepared, _, _ = _prepared(tmp_path)
    slot = prepared.launch_intent["slots"][0]
    Path(slot["wrapper_path"]).write_bytes(b"tampered-after-prepare")
    monkeypatch.setattr(
        C.subprocess, "run", lambda *args, **kwargs: pytest.fail("qsub effect reached"),
    )
    with pytest.raises(C.T810CoordinatorError, match="declared SHA-256"):
        C._subprocess_scheduler(
            prepared.authorization, prepared, slot["qsub_argv"],
            cwd=str(prepared.work_root), env={},
        )


def test_staged_wrapper_accepts_shipped_bytes_and_rejects_one_byte_change(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    prereg = _preregistration()
    accepted = _config(tmp_path / "accepted")
    prepared = C.prepare_group(
        accepted, prereg, _token(accepted, prereg),
        repository_roots={tmp_path / "caller-repository"},
    )
    assert prepared.launch_intent["slots"][0]["wrapper_sha256"] == hashlib.sha256(
        (Path(C.__file__).resolve().parent / "t810_pbs_wrapper.py").read_bytes()
    ).hexdigest()

    config = _config(tmp_path / "rejected")
    wrapper = Path(config["launch_intent"]["slots"][0]["wrapper_path"])
    changed = bytearray(wrapper.read_bytes())
    changed[-1] ^= 1
    wrapper.write_bytes(changed)
    wrapper_sha256 = hashlib.sha256(wrapper.read_bytes()).hexdigest()
    for slot in config["launch_intent"]["slots"]:
        slot["wrapper_sha256"] = wrapper_sha256
    intent_sha256 = S.canonical_sha256(config["launch_intent"])
    for field in ("guard_receipt_path", "budget_receipt_path"):
        path = Path(config[field])
        receipt = json.loads(path.read_text(encoding="utf-8"))
        receipt["launch_intent_sha256"] = intent_sha256
        _write(path, receipt)
    with pytest.raises(C.T810CoordinatorError, match="shipped wrapper bytes"):
        C.prepare_group(
            config, prereg, _token(config, prereg),
            repository_roots={tmp_path / "caller-repository"},
        )


def test_prepare_group_rejects_forged_git_identity_before_any_mkdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    prereg = _preregistration()
    config = _config(tmp_path)
    _rebind_work_root(config, Path(C.__file__).resolve().parents[2] / "orchestrator")

    def forbidden_mkdir(*args, **kwargs):
        pytest.fail("mkdir reached before the live repository anchor rejected work_root")

    monkeypatch.setattr(Path, "mkdir", forbidden_mkdir)
    with pytest.raises(C.T810CoordinatorError, match="work_root is not repository-external"):
        _with_live_authority_retry(
            lambda: C.prepare_group(
                config, prereg, _token(config, prereg),
                repository_roots={tmp_path / "forged-caller-repository"},
            ),
        )


def test_prepare_group_rejects_self_consistent_foreign_git_identity_before_any_mkdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    prereg = _preregistration()
    config = _config(tmp_path / "config")
    foreign_repository = tmp_path / "foreign-repository"
    subprocess.run(
        ["git", "init", "-q", str(foreign_repository)],
        check=True,
    )
    foreign_identity = resolve_git_identity(foreign_repository.resolve())
    config["validator_kwargs"]["repo_root"] = foreign_identity.repo_realpath
    config["validator_kwargs"]["approved_git_identity"] = {
        "repo_realpath": foreign_identity.repo_realpath,
        "git_dir_realpath": foreign_identity.git_dir_realpath,
        "common_dir_realpath": foreign_identity.common_dir_realpath,
    }
    config["validator_kwargs"]["approved_git_identity_sha256"] = (
        git_identity_digest(foreign_identity)
    )
    _rebind_work_root(
        config, Path(C.__file__).resolve().parents[2] / "orchestrator",
    )

    def forbidden_mkdir(*args, **kwargs):
        pytest.fail("mkdir reached before the live repository anchor rejected work_root")

    monkeypatch.setattr(Path, "mkdir", forbidden_mkdir)
    with pytest.raises(C.T810CoordinatorError, match="work_root is not repository-external"):
        _with_live_authority_retry(
            lambda: C.prepare_group(
                config, prereg, _token(config, prereg),
                repository_roots={foreign_repository},
            ),
        )


def test_prepare_group_accepts_external_root_with_anchor_union(tmp_path: Path) -> None:
    prereg = _preregistration()
    config = _config(tmp_path / "accepted")
    caller_repository = tmp_path / "unrelated-caller-repository"
    caller_repository.mkdir()
    prepared = _with_live_authority_retry(
        lambda: C.prepare_group(
            config, prereg, _token(config, prereg),
            repository_roots={caller_repository},
        ),
    )
    assert prepared.work_root == (tmp_path / "accepted/work").resolve()
    assert Path(C.__file__).resolve().parents[2] in prepared.repository_roots
    assert caller_repository.resolve() in prepared.repository_roots
    staged_wrapper = Path(prepared.launch_intent["slots"][0]["wrapper_path"])
    assert staged_wrapper.read_bytes() == Path(W.__file__).read_bytes()


def test_declared_identity_rejects_file_swapped_during_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    hermetic_git_identity: GitIdentity,
) -> None:
    target = tmp_path / "identity-target"
    original = b"before-read"
    replacement = b"after-read!"
    assert len(original) == len(replacement)
    target.write_bytes(original)
    declared_sha256 = hashlib.sha256(original).hexdigest()
    real_read = C.os.read
    changed = False

    def swapping_read(fd: int, count: int) -> bytes:
        nonlocal changed
        chunk = real_read(fd, count)
        if chunk and not changed:
            changed = True
            before = target.stat()
            target.write_bytes(replacement)
            os.utime(
                target,
                ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000),
            )
        return chunk

    monkeypatch.setattr(C.os, "read", swapping_read)
    with pytest.raises(C.T810CoordinatorError, match="changed while reading"):
        C._assert_declared_file_identity(target, declared_sha256, "swapped fixture")
    assert changed


def test_generated_script_executes_staged_wrapper_cli(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    _, _, prepared, _, _ = _prepared(tmp_path)
    slot = prepared.launch_intent["slots"][0]
    command = Path(slot["script_path"]).read_text(encoding="utf-8").splitlines()[-1]
    argv = shlex.split(command.removeprefix("exec "))
    assert argv == slot["wrapper_argv"]
    request_path = prepared.work_root / slot["slot_id"] / "wrapper-request.json"
    assert Path(argv[-1]) == request_path
    shim = tmp_path / "runtime-shim"
    shim.mkdir()
    (shim / "sitecustomize.py").write_text(
        "import os\n"
        "import time\n"
        "os.getloadavg = lambda: (0.0, 0.0, 0.0)\n"
        "time.sleep = lambda _seconds: None\n",
        encoding="utf-8",
    )
    repo_root = Path(C.__file__).resolve().parents[2]
    env = dict(os.environ)
    env.update({
        "PBS_JOBID": "81000.server",
        "PYTHONPATH": str(shim),
    })
    assert repo_root.resolve() not in {
        Path(entry).resolve() for entry in env["PYTHONPATH"].split(os.pathsep)
    }
    script_path = Path(slot["script_path"])
    result = subprocess.run(
        [str(script_path)], cwd=prepared.work_root, env=env, text=True,
        capture_output=True, check=False, timeout=30,
    )
    assert result.returncode == 2
    assert result.stdout == "pre_release_invalid\n"
    events = [
        json.loads(line)
        for line in (prepared.work_root / "slot-00/node-receipt.jsonl").read_text(
            encoding="utf-8",
        ).splitlines()
    ]
    assert events[0]["pbs_request_id"] == "81000.server"
    assert events[0]["payload"]["assigned_hostname"] == os.uname().nodename


def test_generated_script_rejects_self_consistent_evil_wrapper_before_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    hermetic_git_identity: GitIdentity,
) -> None:
    _, _, prepared, _, _ = _prepared(tmp_path)
    slot = prepared.launch_intent["slots"][0]
    evil = tmp_path / "evil.py"
    evil.write_bytes(b"raise SystemExit('scheduler must not execute this')\n")
    slot["wrapper_path"] = str(evil)
    slot["wrapper_sha256"] = hashlib.sha256(evil.read_bytes()).hexdigest()
    slot["wrapper_argv"][1] = str(evil)
    Path(slot["script_path"]).write_bytes(C._canonical_job_script(slot))
    command = Path(slot["script_path"]).read_text(encoding="utf-8").splitlines()[-1]
    evil_argv = shlex.split(command.removeprefix("exec "))
    assert evil_argv[:3] == ["python3.10", str(evil), "--request"]
    assert Path(evil_argv[3]).name == "wrapper-request.json"
    monkeypatch.setattr(
        C.subprocess, "run", lambda *args, **kwargs: pytest.fail("qsub effect reached"),
    )
    with pytest.raises(C.T810CoordinatorError, match="shipped wrapper bytes"):
        C._subprocess_scheduler(
            prepared.authorization, prepared, slot["qsub_argv"],
            cwd=str(prepared.work_root), env={},
        )


def test_terminal_reduced_checks_preserved_dropped_slot_presence(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    prereg, _, prepared, _, _ = _prepared(tmp_path)
    receipts = _completion_receipts(prepared, prereg, dropped={"slot-12"})
    (prepared.output_root / "slot-12" / "measurements.jsonl").unlink()
    terminal = C.verify_completion(
        prepared, receipts, release_event_sha256=H, start_spread_ns=1,
        pre_validator_receipt_sha256=H, post_validator_receipt_sha256=H,
    )
    assert terminal["state"] == "incomplete_after_start"
    assert terminal["reason_codes"] == ["presence_matrix_mismatch"]


def test_guard_and_budget_receipts_are_typed_and_digest_bound(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    prereg = _preregistration()
    guard_config = _config(tmp_path / "guard")
    guard_path = Path(guard_config["guard_receipt_path"])
    guard = json.loads(guard_path.read_text())
    guard["phase"] = "pre-submission"
    _write(guard_path, guard)
    with pytest.raises(C.T810CoordinatorError, match="phase"):
        C.prepare_group(
            guard_config, prereg, _token(guard_config, prereg),
            repository_roots={Path("/repo")},
        )
    budget_config = _config(tmp_path / "budget")
    budget_path = Path(budget_config["budget_receipt_path"])
    budget = json.loads(budget_path.read_text())
    budget["ledger_sha256_after"] = budget["ledger_sha256_before"]
    _write(budget_path, budget)
    with pytest.raises(C.T810CoordinatorError, match="ledger-after"):
        C.prepare_group(
            budget_config, prereg, _token(budget_config, prereg),
            repository_roots={Path("/repo")},
        )


def test_git_common_dir_skips_unlocked_missing_registration_file(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    identity, admin = _registration_identity(tmp_path)
    (admin / "modules").mkdir()
    sibling = tmp_path / "sibling"
    sibling.mkdir()
    sibling_gitdir = sibling / ".git"
    sibling_gitdir.write_text("gitdir: fixture\n", encoding="utf-8")
    sibling_admin = admin.parent / "sibling"
    sibling_admin.mkdir()
    (sibling_admin / "gitdir").write_text(
        str(sibling_gitdir) + "\n", encoding="utf-8",
    )

    assert C.repository_roots_from_git_identity(identity) == frozenset({
        Path(identity.repo_realpath).resolve(), sibling.resolve(),
    })


@pytest.mark.parametrize("lock_kind", ["file", "broken_symlink", "directory"])
def test_git_common_dir_rejects_locked_missing_registration_file(
    tmp_path: Path, hermetic_git_identity: GitIdentity, lock_kind: str,
) -> None:
    identity, admin = _registration_identity(tmp_path)
    locked = admin / "locked"
    if lock_kind == "file":
        locked.write_text("locked\n", encoding="utf-8")
    elif lock_kind == "broken_symlink":
        locked.symlink_to(tmp_path / "absent-lock-target")
    else:
        locked.mkdir()

    with pytest.raises(
        C.T810CoordinatorError,
        match=r"^cannot read worktree registration: file is absent$",
    ):
        C.repository_roots_from_git_identity(identity)


def test_git_common_dir_rejects_non_enoent_registration_open_error(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    identity, admin = _registration_identity(tmp_path)
    admin.rmdir()
    admin.write_text("not a directory\n", encoding="utf-8")

    with pytest.raises(
        C.T810CoordinatorError,
        match=r"^cannot read worktree registration: ",
    ):
        C.repository_roots_from_git_identity(identity)


def test_git_common_dir_rejects_lock_stat_error(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identity, admin = _registration_identity(tmp_path)
    locked = admin / "locked"
    real_lstat = C.os.lstat

    def failing_lock_lstat(path, *args, **kwargs):
        if Path(path) == locked:
            raise PermissionError("lock inspection denied")
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(C.os, "lstat", failing_lock_lstat)
    with pytest.raises(
        C.T810CoordinatorError,
        match=r"^cannot inspect worktree registration lock$",
    ):
        C.repository_roots_from_git_identity(identity)


def test_git_common_dir_rejects_symlink_registration_file(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    identity, admin = _registration_identity(tmp_path)
    target = tmp_path / "registration-target"
    target.write_text("unused\n", encoding="utf-8")
    (admin / "gitdir").symlink_to(target)

    with pytest.raises(
        C.T810CoordinatorError,
        match=r"^git common-dir contains an invalid worktree registration$",
    ):
        C.repository_roots_from_git_identity(identity)


def test_git_common_dir_rejects_non_regular_registration_file(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    identity, admin = _registration_identity(tmp_path)
    (admin / "gitdir").mkdir()

    with pytest.raises(
        C.T810CoordinatorError,
        match=r"^worktree registration is not a regular file$",
    ):
        C.repository_roots_from_git_identity(identity)


def test_git_common_dir_rejects_registration_changed_during_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    hermetic_git_identity: GitIdentity,
) -> None:
    identity, admin = _registration_identity(tmp_path)
    gitdir = admin / "gitdir"
    original = (str(tmp_path / "linked-a" / ".git") + "\n").encode()
    replacement = (str(tmp_path / "linked-b" / ".git") + "\n").encode()
    assert len(original) == len(replacement)
    gitdir.write_bytes(original)
    real_read = C.os.read
    changed = False

    def swapping_registration_read(fd: int, count: int) -> bytes:
        # Replace the same-size registration synchronously after its first read;
        # the forced mtime delta makes the following fstat comparison deterministic.
        nonlocal changed
        chunk = real_read(fd, count)
        if chunk and not changed:
            changed = True
            before = gitdir.stat()
            gitdir.write_bytes(replacement)
            os.utime(
                gitdir,
                ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000),
            )
        return chunk

    monkeypatch.setattr(C.os, "read", swapping_registration_read)
    with pytest.raises(
        C.T810CoordinatorError,
        match=r"^worktree registration changed while reading$",
    ):
        C.repository_roots_from_git_identity(identity)
    assert changed


def test_git_common_dir_derives_main_and_sibling_worktree_roots(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    main = tmp_path / "main"
    common = main / ".git"
    sibling = tmp_path / "sibling"
    (common / "worktrees" / "sibling").mkdir(parents=True)
    sibling.mkdir()
    sibling_git = sibling / ".git"
    sibling_git.write_text("gitdir: fixture\n", encoding="utf-8")
    (common / "worktrees" / "sibling" / "gitdir").write_text(
        str(sibling_git) + "\n", encoding="utf-8",
    )
    roots = C.repository_roots_from_git_identity(
        GitIdentity(str(main), str(common), str(common)),
    )
    assert roots == frozenset({main.resolve(), sibling.resolve()})
    with pytest.raises(S.T810SchemaError, match="outside every repository"):
        S.assert_repository_external(sibling / "output", repository_roots=roots)


def test_git_common_dir_preserves_missing_registered_worktree_claim(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    main = tmp_path / "main"
    common = main / ".git"
    stale = common / "worktrees" / "stale"
    stale.mkdir(parents=True)
    (stale / "gitdir").write_text(
        str(tmp_path / "removed-worktree" / ".git") + "\n", encoding="utf-8",
    )

    roots = C.repository_roots_from_git_identity(
        GitIdentity(str(main), str(common), str(common)),
    )

    assert roots == frozenset({
        main.resolve(), (tmp_path / "removed-worktree").resolve(strict=False),
    })


def test_authorized_production_core_uses_same_validator_twice_and_dormant_prereg(
    tmp_path: Path, hermetic_git_identity: GitIdentity,
) -> None:
    prereg = _preregistration()
    config = _config(tmp_path)
    preview = _preview(config, prereg)
    release_sha = _release_sha(preview)
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
    clock_calls = [0]
    def clock_ns():
        call = clock_calls[0]
        clock_calls[0] += 1
        if call < 16:
            return 0
        if call == 16:
            return 100
        if call < 19:
            return 100
        if call < 32:
            return 100 + ((call - 19) * S.START_SPREAD_MAX_NS // 12)
        return 100 + S.START_SPREAD_MAX_NS
    phases = iter(("preflight", "ack", "terminal"))
    def sleep(_seconds):
        _publish_fixture_phase(preview, next(phases), release_sha)
    result = C._coordinate_authorized(
        config, prereg, _token(config, prereg), scheduler_run=scheduler,
        clock_ns=clock_ns, sleep=sleep,
        wall_clock=lambda: "2026-08-12T00:00:04Z", validator=validator,
        repository_roots={Path("/repository")},
    )
    assert result.terminal_state["state"] == "valid"
    assert calls == ["pre_release_invalid", "valid"]
    assert len(scheduler.calls) == S.NODE_COUNT
    assert result.prepared.terminal_path.is_file()
    events = [S.parse_json(line) for line in result.prepared.coordinator_receipt_path.read_bytes().splitlines()]
    acks_recorded = [event for event in events if event["event"] == "start_ack_received"]
    assert len(acks_recorded) == S.NODE_COUNT
    assert max(event["details"]["latency_ns"] for event in acks_recorded) == S.START_SPREAD_MAX_NS


def test_all_test_nodes_pin_repository_authority(
    hermetic_git_identity: GitIdentity,
) -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    test_functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]
    assert len(test_functions) == len({node.name for node in test_functions})
    tests = {node.name: node for node in test_functions}
    def frozenset_literal(name: str) -> frozenset[str]:
        assignments = [
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == name
                for target in node.targets
            )
        ]
        assert len(assignments) == 1
        literal = assignments[0].value
        assert (
            isinstance(literal, ast.Call)
            and isinstance(literal.func, ast.Name)
            and literal.func.id == "frozenset"
            and len(literal.args) == 1
            and not literal.keywords
            and isinstance(literal.args[0], ast.Set)
        )
        items = literal.args[0].elts
        assert all(
            isinstance(item, ast.Constant) and isinstance(item.value, str)
            for item in items
        )
        return frozenset(item.value for item in items)

    assert isinstance(_LIVE_AUTHORITY_NODES, frozenset)
    assert frozenset_literal("_LIVE_AUTHORITY_NODES") == _LIVE_AUTHORITY_NODES
    assert isinstance(_HERMETIC_DIRECT_AUTHORITY_NODES, frozenset)
    assert (
        frozenset_literal("_HERMETIC_DIRECT_AUTHORITY_NODES")
        == _HERMETIC_DIRECT_AUTHORITY_NODES
    )

    hermetic_nodes = set()
    live_retry_nodes = set()
    direct_authority_nodes = set()
    for name, node in tests.items():
        parameters = {
            argument.arg
            for argument in (
                *node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs,
            )
        }
        if "hermetic_git_identity" in parameters:
            hermetic_nodes.add(name)
        if any(
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Name)
            and item.func.id == "_with_live_authority_retry"
            for item in ast.walk(node)
        ):
            live_retry_nodes.add(name)
        if any(
            isinstance(item, ast.Call)
            and (
                isinstance(item.func, ast.Name)
                and item.func.id in {
                    "resolve_git_identity", "repository_roots_from_git_identity",
                }
                or isinstance(item.func, ast.Attribute)
                and isinstance(item.func.value, ast.Name)
                and item.func.value.id == "C"
                and item.func.attr in {
                    "resolve_git_identity", "repository_roots_from_git_identity",
                }
            )
            for item in ast.walk(node)
        ):
            direct_authority_nodes.add(name)

    assert live_retry_nodes == _LIVE_AUTHORITY_NODES
    assert not hermetic_nodes.intersection(_LIVE_AUTHORITY_NODES)
    assert set(tests) == hermetic_nodes.union(_LIVE_AUTHORITY_NODES)
    assert (
        direct_authority_nodes - _LIVE_AUTHORITY_NODES
        == _HERMETIC_DIRECT_AUTHORITY_NODES
    )
    assert _HERMETIC_DIRECT_AUTHORITY_NODES <= hermetic_nodes


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
