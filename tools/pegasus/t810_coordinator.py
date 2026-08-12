"""Fail-closed coordinator for one T-810 N-job attempt; it never issues witnesses."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, is_dataclass
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Callable, Mapping, Sequence

from orchestrator.campaign.t810_preregistration import (
    APPROVAL_RECEIPT_SCHEMA_VERSION,
    PREREG_PATH,
    ApprovalReceipt,
    VerifiedT810Preregistration,
    load_t810_preregistration,
)
from orchestrator.campaign.t810_validator import (
    BaselineEnvelope,
    pass_witness_sha256,
    validate_t810,
)
from tools.pegasus import t810_harness_schema as schema


class T810CoordinatorError(RuntimeError):
    pass

@dataclass(frozen=True)
class PreparedGroup:
    preregistration: VerifiedT810Preregistration
    admission_policy: Mapping[str, Any]
    launch_intent: Mapping[str, Any]
    launch_intent_sha256: str
    manifest: Mapping[str, Any]
    manifest_sha256: str
    release_nonce: str
    approved_hostnames: frozenset[str]
    work_root: Path
    output_root: Path
    intent_path: Path
    manifest_path: Path
    submission_path: Path
    coordinator_receipt_path: Path
    terminal_path: Path
    release_path: Path
    cancel_path: Path

@dataclass(frozen=True)
class BarrierDecision:
    status: str
    reason_codes: tuple[str, ...]
    receipt_sha256_by_slot: Mapping[str, str]

@dataclass(frozen=True)
class AckDecision:
    accepted: bool
    reason_codes: tuple[str, ...]
    spread_ns: int
    latency_ns_by_slot: Mapping[str, int]
    receipt_sha256_by_slot: Mapping[str, str]

@dataclass(frozen=True)
class CoordinationResult:
    prepared: PreparedGroup
    submission_receipt: Mapping[str, Any] | None
    terminal_state: Mapping[str, Any]

SchedulerRun = Callable[..., subprocess.CompletedProcess[str]]
Clock = Callable[[], int]
WallClock = Callable[[], str]
Validator = Callable[..., Any]

def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise T810CoordinatorError(f"{name} must be an object")
    return dict(value)

def _require_fields(value: Mapping[str, Any], fields: set[str], name: str) -> None:
    if set(value) != fields:
        raise T810CoordinatorError(f"{name} has unknown or missing fields")

def _policy_digest(policy: Mapping[str, Any]) -> str:
    return schema.canonical_sha256(dict(policy))
def _approved_hosts(policy: Mapping[str, Any]) -> frozenset[str]:
    item = _object(policy.get("approved_hostnames"), "approved_hostnames policy")
    if item.get("status") != "ratified":
        raise T810CoordinatorError("approved_hostnames policy is not ratified")
    values = item.get("hostnames")
    if not isinstance(values, list) or not values:
        raise T810CoordinatorError("approved_hostnames.hostnames must be non-empty")
    if any(not isinstance(host, str) or not host for host in values):
        raise T810CoordinatorError("approved_hostnames contains a non-string hostname")
    if len(values) != len(set(values)):
        raise T810CoordinatorError("approved_hostnames contains duplicates")
    return frozenset(values)
def verify_launch_authorization(
    witness: Mapping[str, Any] | None,
    *,
    preregistration: VerifiedT810Preregistration,
    policy_sha256: str,
    run_kind: str,
) -> Mapping[str, Any]:
    if witness is None:
        raise T810CoordinatorError("launch authorization witness is required")
    try:
        document = schema.validate_launch_authorization(witness)
    except schema.T810SchemaError as exc:
        raise T810CoordinatorError(f"invalid launch authorization witness: {exc}") from exc
    if document["preregistration_sha256"] != preregistration.sha256:
        raise T810CoordinatorError("authorization preregistration digest mismatch")
    if document["policy_sha256"] != policy_sha256:
        raise T810CoordinatorError("authorization policy digest mismatch")
    if document["approval_id"] != preregistration.approval_id:
        raise T810CoordinatorError("authorization approval id mismatch")
    if run_kind not in document["run_kinds"]:
        raise T810CoordinatorError("authorization does not include run_kind")
    return document
def _ensure_external_root(path: Path, name: str) -> Path:
    if not path.is_absolute():
        raise T810CoordinatorError(f"{name} must be absolute")
    repo = Path(__file__).resolve().parents[2]
    resolved = path.resolve(strict=False)
    if resolved == repo or repo in resolved.parents:
        raise T810CoordinatorError(f"{name} must be outside the repository")
    resolved.mkdir(parents=True, exist_ok=True)
    if resolved.is_symlink() or not resolved.is_dir():
        raise T810CoordinatorError(f"{name} must be a real directory")
    return resolved
def _write_create_only(path: Path, value: Any) -> bytes:
    raw = schema.canonical_json_bytes(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / ("." + path.name + "." + schema.sha256_bytes(raw)[:16] + ".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(temporary, flags, 0o600)
        try:
            offset = 0
            while offset < len(raw):
                written = os.write(fd, raw[offset:])
                if written <= 0:
                    raise T810CoordinatorError(f"short write for {path.name}")
                offset += written
            os.fsync(fd)
        finally:
            os.close(fd)
        os.link(temporary, path, follow_symlinks=False)
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except (FileExistsError, OSError) as exc:
        raise T810CoordinatorError(f"create-only publication failed: {path}") from exc
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return raw
def _touch_create_only(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        raise T810CoordinatorError(f"create-only publication failed: {path}") from exc
def _read_json(path: Path, name: str) -> Mapping[str, Any]:
    try:
        info = path.lstat()
        if path.is_symlink() or not path.is_file():
            raise T810CoordinatorError(f"{name} is not a regular file")
        raw = path.read_bytes()
        if path.stat().st_ino != info.st_ino:
            raise T810CoordinatorError(f"{name} changed while reading")
        value = schema.parse_json(raw)
    except (OSError, schema.T810SchemaError) as exc:
        raise T810CoordinatorError(f"cannot read {name}: {exc}") from exc
    return _object(value, name)
def _append_coordinator_event(
    prepared: PreparedGroup, event: str, details: Mapping[str, Any], *,
    wall_time: str, monotonic_ns: int, slot_id: str | None = None,
) -> str:
    try:
        lines = prepared.coordinator_receipt_path.read_bytes().splitlines()
        previous = None if not lines else schema.canonical_sha256(schema.parse_json(lines[-1]))
        document = schema.validate_coordinator_event({
            "schema_version": schema.COORDINATOR_EVENT_SCHEMA,
            "group_manifest_sha256": prepared.manifest_sha256, "sequence": len(lines),
            "event": event, "wall_time": wall_time,
            "coordinator_monotonic_ns": monotonic_ns, "slot_id": slot_id,
            "previous_event_sha256": previous, "details": dict(details),
        })
        raw = schema.canonical_json_bytes(document) + b"\n"
        fd = os.open(
            prepared.coordinator_receipt_path,
            os.O_WRONLY | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            if os.write(fd, raw) != len(raw):
                raise T810CoordinatorError("short coordinator receipt write")
            os.fsync(fd)
        finally:
            os.close(fd)
    except (OSError, schema.T810SchemaError) as exc:
        raise T810CoordinatorError("could not append coordinator receipt") from exc
    return schema.canonical_sha256(document)
def _receipt_intent_digest(receipt: Mapping[str, Any], name: str) -> str:
    digest = receipt.get("launch_intent_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise T810CoordinatorError(f"{name} does not bind launch intent")
    return digest
def prepare_group(
    config: Mapping[str, Any], preregistration: VerifiedT810Preregistration,
) -> PreparedGroup:
    if not isinstance(preregistration, VerifiedT810Preregistration):
        raise T810CoordinatorError("verified preregistration from loader is required")
    document = _object(config, "coordinator config")
    intent = schema.validate_launch_intent(document.get("launch_intent"))
    policy = _object(document.get("admission_policy"), "admission policy")
    guard = _object(document.get("guard_receipt"), "guard receipt")
    budget = _object(document.get("budget_receipt"), "budget receipt")
    nonce = document.get("release_nonce")
    if not isinstance(nonce, str) or not nonce:
        raise T810CoordinatorError("release nonce is required")
    policy_sha256 = _policy_digest(policy)
    if intent["policy_sha256"] != policy_sha256:
        raise T810CoordinatorError("launch intent policy digest mismatch")
    if intent["preregistration_sha256"] != preregistration.sha256:
        raise T810CoordinatorError("launch intent preregistration digest mismatch")
    if intent["prereg_approval_id"] != preregistration.approval_id:
        raise T810CoordinatorError("launch intent approval id is not loader-derived")
    selected = preregistration.projection["design"]["selected"]
    if intent["node_count"] != int(selected["node_count"]):
        raise T810CoordinatorError("launch intent node_count differs from preregistration")
    if intent["round_count"] != int(selected["round_count"]):
        raise T810CoordinatorError("launch intent round_count differs from preregistration")
    approved = _approved_hosts(policy)
    work_root = _ensure_external_root(Path(intent["work_root"]), "work_root")
    output_root = _ensure_external_root(Path(intent["output_root"]), "output_root")
    if work_root == output_root:
        raise T810CoordinatorError("work_root and output_root must differ")
    for slot in intent["slots"]:
        slot_root = output_root / slot["slot_id"]
        expected_out = slot_root / "pbs.stdout.log"
        expected_err = slot_root / "pbs.stderr.log"
        if Path(slot["pbs_stdout_path"]) != expected_out or Path(slot["pbs_stderr_path"]) != expected_err:
            raise T810CoordinatorError("PBS log paths do not match frozen artifact layout")
    intent_sha256 = schema.canonical_sha256(intent)
    if _receipt_intent_digest(guard, "guard receipt") != intent_sha256:
        raise T810CoordinatorError("guard receipt launch intent mismatch")
    if _receipt_intent_digest(budget, "budget receipt") != intent_sha256:
        raise T810CoordinatorError("budget receipt launch intent mismatch")
    if guard.get("decision") not in {"allow", "admit", "admitted"}:
        raise T810CoordinatorError("guard receipt does not allow launch")
    if budget.get("admitted") is not True:
        raise T810CoordinatorError("budget receipt does not admit launch")

    control = work_root / "control"
    intent_path = control / "launch-intent.json"
    _write_create_only(intent_path, intent)
    manifest = schema.validate_group_manifest({
        "schema_version": schema.GROUP_MANIFEST_SCHEMA,
        "group_id": intent["group_id"],
        "created_at": document.get("manifest_created_at", intent["created_at"]),
        "launch_intent_sha256": intent_sha256,
        "guard_receipt_sha256": schema.canonical_sha256(guard),
        "budget_receipt_sha256": schema.canonical_sha256(budget),
        "release_token_commitment": schema.release_token_commitment(nonce),
    })
    manifest_path = output_root / "group-manifest.json"
    _write_create_only(manifest_path, manifest)
    manifest_sha256 = schema.canonical_sha256(manifest)
    for slot in intent["slots"]:
        slot_root = output_root / slot["slot_id"]
        slot_root.mkdir(parents=True, exist_ok=True)
        for name in ("pbs.stdout.log", "pbs.stderr.log"):
            _touch_create_only(slot_root / name)
    for name in ("coordinator.stdout.log", "coordinator.stderr.log"):
        _touch_create_only(output_root / name)
    _touch_create_only(output_root / "coordinator-receipt.jsonl")
    return PreparedGroup(
        preregistration, policy, intent, intent_sha256, manifest, manifest_sha256,
        nonce, approved, work_root, output_root, intent_path, manifest_path,
        output_root / "submission-receipt.json", output_root / "coordinator-receipt.jsonl",
        output_root / "terminal-state.json", control / "release.json", control / "cancel.json",
    )
def _scheduler_effect(
    prepared: PreparedGroup,
    witness: Mapping[str, Any] | None,
    scheduler_run: SchedulerRun,
    argv: Sequence[str],
) -> subprocess.CompletedProcess[str]:
    verify_launch_authorization(
        witness, preregistration=prepared.preregistration,
        policy_sha256=prepared.launch_intent["policy_sha256"],
        run_kind=prepared.launch_intent["run_kind"],
    )
    result = scheduler_run(list(argv), cwd=str(prepared.work_root), env={})
    if not isinstance(result, subprocess.CompletedProcess):
        raise T810CoordinatorError("scheduler adapter returned an invalid result")
    return result
def submit_group(
    prepared: PreparedGroup,
    witness: Mapping[str, Any] | None,
    *,
    scheduler_run: SchedulerRun,
    wall_clock: WallClock,
) -> Mapping[str, Any]:
    requests: list[dict[str, Any]] = []
    for slot in prepared.launch_intent["slots"]:
        result = _scheduler_effect(prepared, witness, scheduler_run, slot["qsub_argv"])
        stdout = result.stdout if isinstance(result.stdout, str) else ""
        stderr = result.stderr if isinstance(result.stderr, str) else ""
        pbs_id = stdout.strip() if result.returncode == 0 and stdout.strip() else None
        requests.append({
            "slot_id": slot["slot_id"], "logical_request_id": slot["logical_request_id"],
            "job_name": slot["job_name"], "qsub_argv": list(slot["qsub_argv"]),
            "qsub_rc": result.returncode, "qsub_stdout": stdout, "qsub_stderr": stderr,
            "pbs_request_id": pbs_id,
        })
    receipt = schema.validate_submission_receipt({
        "schema_version": schema.SUBMISSION_RECEIPT_SCHEMA,
        "group_manifest_sha256": prepared.manifest_sha256,
        "created_at": wall_clock(), "requests": requests,
    }, expected_node_count=len(prepared.launch_intent["slots"]))
    _write_create_only(prepared.submission_path, receipt)
    return receipt
def _complete_submission(prepared: PreparedGroup) -> Mapping[str, Any]:
    if not prepared.submission_path.exists():
        raise T810CoordinatorError("submission receipt must exist before barrier evaluation")
    receipt = schema.validate_submission_receipt(
        _read_json(prepared.submission_path, "submission receipt"),
        expected_node_count=len(prepared.launch_intent["slots"]),
    )
    if receipt["group_manifest_sha256"] != prepared.manifest_sha256:
        raise T810CoordinatorError("submission receipt manifest mismatch")
    for slot, request in zip(prepared.launch_intent["slots"], receipt["requests"], strict=True):
        for field in ("slot_id", "logical_request_id", "job_name", "qsub_argv"):
            if request[field] != slot[field]:
                raise T810CoordinatorError(f"submission receipt {field} mismatch")
    return receipt
def _bound_node_event(
    prepared: PreparedGroup, event: Mapping[str, Any], request: Mapping[str, Any], expected_event: str,
) -> Mapping[str, Any]:
    node = schema.validate_node_event(event)
    if node["event"] != expected_event:
        raise T810CoordinatorError(f"expected {expected_event} node event")
    if (node["group_manifest_sha256"] != prepared.manifest_sha256
            or node["group_id"] != prepared.launch_intent["group_id"]):
        raise T810CoordinatorError("node event manifest identity mismatch")
    for field in ("slot_id", "logical_request_id", "pbs_request_id"):
        if node[field] != request[field]:
            raise T810CoordinatorError(f"node event {field} mismatch")
    return node
def evaluate_ready_barrier(
    prepared: PreparedGroup,
    ready_events: Sequence[Mapping[str, Any]],
    *,
    elapsed_seconds: int | float,
) -> BarrierDecision:
    submission = _complete_submission(prepared)
    if any(item["qsub_rc"] != 0 or item["pbs_request_id"] is None for item in submission["requests"]):
        return BarrierDecision("cancel", ("submission_failed",), {})
    count = len(prepared.launch_intent["slots"])
    if isinstance(elapsed_seconds, bool) or not isinstance(elapsed_seconds, (int, float)) or elapsed_seconds < 0:
        raise T810CoordinatorError("elapsed_seconds is invalid")
    if len(ready_events) < count:
        if elapsed_seconds < schema.READY_TIMEOUT_SECONDS:
            return BarrierDecision("waiting", (), {})
        return BarrierDecision("cancel", ("ready_timeout",), {})
    requests = {item["slot_id"]: item for item in submission["requests"]}
    events: dict[str, Mapping[str, Any]] = {}
    reasons: set[str] = set()
    digests: dict[str, str] = {}
    for raw in ready_events:
        slot_id = raw.get("slot_id") if isinstance(raw, Mapping) else None
        if slot_id not in requests or slot_id in events:
            reasons.add("preflight_failed")
            continue
        try:
            event = _bound_node_event(prepared, raw, requests[slot_id], "preflight")
        except (schema.T810SchemaError, T810CoordinatorError):
            reasons.add("preflight_failed")
            continue
        events[slot_id] = event
        digests[slot_id] = schema.canonical_sha256(event)
        payload = event["payload"]
        if payload["assigned_hostname"] != payload["actual_hostname"]:
            reasons.add("hostname_mismatch")
        if payload["actual_hostname"] not in prepared.approved_hostnames:
            reasons.add("unapproved_hostname")
        slot = prepared.launch_intent["slots"][int(slot_id[-2:])]
        if (payload["binary_source_sha256"] != slot["binary_sha256"]
                or payload["binary_copy_sha256"] != slot["binary_sha256"]):
            reasons.add("binary_copy_hash_mismatch")
        samples = payload["quiet_samples"]
        if len(samples) < 3 or any(sample["load_average_1m"] > 1.0 for sample in samples[-3:]):
            reasons.add("quiet_gate_failed")
        if payload["observed_submission_argv"] != slot["qsub_argv"]:
            reasons.add("submission_argv_mismatch")
        if (payload["competing_processes"]
                or not all(payload["repo_absence"].values())):
            reasons.add("preflight_failed")
    if len(events) != count:
        reasons.add("preflight_failed")
    hostnames = [event["payload"]["actual_hostname"] for event in events.values()]
    if len(set(hostnames)) != count:
        reasons.add("hostname_count_mismatch")
        if len(hostnames) != len(set(hostnames)):
            reasons.add("duplicate_hostname")
    return BarrierDecision("release" if not reasons else "cancel", tuple(sorted(reasons)), digests)
def _publish_marker(
    prepared: PreparedGroup,
    witness: Mapping[str, Any] | None,
    *,
    kind: str,
    wall_clock: WallClock,
    reason_codes: Sequence[str] = (),
) -> tuple[Mapping[str, Any], str]:
    verify_launch_authorization(
        witness, preregistration=prepared.preregistration,
        policy_sha256=prepared.launch_intent["policy_sha256"],
        run_kind=prepared.launch_intent["run_kind"],
    )
    if kind == "release":
        if prepared.cancel_path.exists():
            raise T810CoordinatorError("release forbidden after cancel")
        marker = {
            "schema_version": schema.CONTROL_MARKER_SCHEMA,
            "group_manifest_sha256": prepared.manifest_sha256,
            "group_id": prepared.launch_intent["group_id"], "kind": "release",
            "published_at": wall_clock(), "nonce": prepared.release_nonce,
        }
        marker = schema.validate_control_marker(
            marker, expected_release_token_commitment=prepared.manifest["release_token_commitment"],
        )
        path = prepared.release_path
    elif kind == "cancel":
        marker = schema.validate_control_marker({
            "schema_version": schema.CONTROL_MARKER_SCHEMA,
            "group_manifest_sha256": prepared.manifest_sha256,
            "group_id": prepared.launch_intent["group_id"], "kind": "cancel",
            "published_at": wall_clock(), "reason_codes": list(dict.fromkeys(reason_codes)),
        })
        path = prepared.cancel_path
    else:
        raise T810CoordinatorError("unknown control marker kind")
    _write_create_only(path, marker)
    return marker, schema.canonical_sha256(marker)
def publish_release(
    prepared: PreparedGroup, witness: Mapping[str, Any] | None, *, wall_clock: WallClock,
) -> tuple[Mapping[str, Any], str]:
    return _publish_marker(prepared, witness, kind="release", wall_clock=wall_clock)
def publish_cancel(
    prepared: PreparedGroup,
    witness: Mapping[str, Any] | None,
    reason_codes: Sequence[str],
    *,
    wall_clock: WallClock,
) -> tuple[Mapping[str, Any], str]:
    return _publish_marker(
        prepared, witness, kind="cancel", reason_codes=reason_codes, wall_clock=wall_clock,
    )
def release_is_still_active(prepared: PreparedGroup, release_sha256: str) -> bool:
    if prepared.cancel_path.exists() or not prepared.release_path.exists():
        return False
    marker = schema.validate_control_marker(
        _read_json(prepared.release_path, "release marker"),
        expected_release_token_commitment=prepared.manifest["release_token_commitment"],
    )
    return schema.canonical_sha256(marker) == release_sha256
def evaluate_start_acks(
    prepared: PreparedGroup,
    ack_events: Sequence[tuple[Mapping[str, Any], int]],
    *,
    release_marker_sha256: str,
    release_published_ns: int,
) -> AckDecision:
    submission = _complete_submission(prepared)
    requests = {item["slot_id"]: item for item in submission["requests"]}
    seen: set[str] = set()
    reasons: set[str] = set()
    latencies: dict[str, int] = {}
    digests: dict[str, str] = {}
    for raw, received_ns in ack_events:
        slot_id = raw.get("slot_id") if isinstance(raw, Mapping) else None
        if slot_id not in requests:
            reasons.add("ack-unknown-slot")
            continue
        if slot_id in seen:
            reasons.add("ack-duplicate")
            continue
        seen.add(slot_id)
        try:
            event = _bound_node_event(prepared, raw, requests[slot_id], "start_ack")
        except (schema.T810SchemaError, T810CoordinatorError):
            reasons.add("release-marker-mismatch")
            continue
        if isinstance(received_ns, bool) or not isinstance(received_ns, int) or received_ns < release_published_ns:
            reasons.add("release-marker-mismatch")
            continue
        payload = event["payload"]
        if payload["release_marker_sha256"] != release_marker_sha256:
            reasons.add("release-marker-mismatch")
        if not payload["cancel_marker_absent"]:
            reasons.add("cancel_marker_observed")
        latencies[slot_id] = received_ns - release_published_ns
        digests[slot_id] = schema.canonical_sha256(event)
    if len(seen) != len(requests):
        reasons.add("ack-missing")
    spread = max(latencies.values(), default=0)
    if spread > schema.START_SPREAD_MAX_NS:
        reasons.add("start_spread_exceeded")
    return AckDecision(not reasons, tuple(sorted(reasons)), spread, latencies, digests)
def _presence_for_state(
    preregistration: VerifiedT810Preregistration,
    state: str,
    completed: set[str],
    reached: set[str],
    started: set[str] | None = None,
) -> dict[str, list[str]]:
    artifacts = preregistration.projection["artifacts"]
    matrix = artifacts["presence_matrix"][state]
    slots = [artifacts["slots"]["id_format"] % i for i in range(schema.NODE_COUNT)]
    started = started or set()
    result: dict[str, list[str]] = {}
    for slot in slots:
        paths: list[str] = []
        receipt_required = matrix["node_receipts"] == "all-13" or slot in reached
        measurement_rule = matrix["measurements"]
        measurement_required = (
            measurement_rule in {"all-13-times-10", "completed-12-plus-preserved-dropped"}
            or (measurement_rule == "started-slots-exact" and slot in started)
        )
        if receipt_required or measurement_required:
            paths.extend(f"{slot}/{name}" for name in artifacts["slots"]["always_files"])
        if receipt_required:
            paths.append(f"{slot}/{artifacts['slots']['conditional_node_receipt_file']}")
        if measurement_required:
            paths.append(f"{slot}/{artifacts['slots']['conditional_measurements_file']}")
        result[slot] = sorted(paths)
    return result
def verify_completion(
    prepared: PreparedGroup,
    completion_receipts: Sequence[Mapping[str, Any]],
    *,
    release_event_sha256: str,
    start_spread_ns: int,
    pre_validator_receipt_sha256: str,
    post_validator_receipt_sha256: str,
) -> Mapping[str, Any]:
    submission = _complete_submission(prepared)
    requests = {item["slot_id"]: item for item in submission["requests"]}
    by_slot: dict[str, Mapping[str, Any]] = {}
    structure_bad = False
    for raw in completion_receipts:
        slot_id = raw.get("slot_id") if isinstance(raw, Mapping) else None
        if slot_id not in requests or slot_id in by_slot:
            structure_bad = True
            continue
        by_slot[slot_id] = raw
    if set(by_slot) != set(requests):
        structure_bad = True
    if structure_bad:
        raise T810CoordinatorError(
            "completion receipts contain an orphan, duplicate, unknown, or missing slot"
        )
    completed: set[str] = set()
    started: set[str] = set()
    receipt_hashes: dict[str, str | None] = {slot: None for slot in requests}
    integrity_reasons: set[str] = set()
    actual_presence: dict[str, list[str]] = {slot: [] for slot in requests}
    for slot_id, raw in by_slot.items():
        try:
            _require_fields(
                raw,
                {"slot_id", "terminal_event", "measurement_event", "node_receipt_sha256", "actual_presence"},
                "completion receipt",
            )
            terminal = _bound_node_event(prepared, raw["terminal_event"], requests[slot_id], "terminal")
            digest = raw["node_receipt_sha256"]
            if not isinstance(digest, str) or len(digest) != 64:
                raise T810CoordinatorError("node receipt digest is invalid")
            receipt_hashes[slot_id] = digest
            presence = raw["actual_presence"]
            if not isinstance(presence, list) or any(not isinstance(item, str) for item in presence):
                raise T810CoordinatorError("actual presence is invalid")
            actual_presence[slot_id] = list(presence)
            measurement_raw = raw["measurement_event"]
            if measurement_raw is None:
                continue
            started.add(slot_id)
            measurement = _bound_node_event(prepared, measurement_raw, requests[slot_id], "measurement")
            payload = measurement["payload"]
            terminal_payload = terminal["payload"]
            rounds = payload["rounds"]
            if (not terminal_payload["measurement_started"]
                    or terminal_payload["completed_rounds"] != prepared.launch_intent["round_count"]
                    or len(rounds) != prepared.launch_intent["round_count"]
                    or payload["benchmark_rc"] != 0
                    or any(item["exit_code"] != 0 for item in rounds)):
                integrity_reasons.add("completed_rounds_missing")
                continue
            slot = prepared.launch_intent["slots"][int(slot_id[-2:])]
            if payload["binary_after_sha256"] != slot["binary_sha256"]:
                integrity_reasons.add("binary_after_hash_mismatch")
                continue
            completed.add(slot_id)
        except (schema.T810SchemaError, T810CoordinatorError, KeyError, TypeError):
            structure_bad = True
    if structure_bad:
        raise T810CoordinatorError("completion receipt content is invalid")
    count = len(requests)
    if integrity_reasons:
        state, reasons = "incomplete_after_start", integrity_reasons
    elif len(completed) <= count - 2:
        state, reasons = "incomplete_after_start", {"insufficient_completions"}
    elif len(completed) == count - 1:
        state, reasons = "terminal_reduced", {"single_job_dropped"}
    elif len(completed) == count:
        state, reasons = "valid", {"all_jobs_complete"}
    else:
        state, reasons = "incomplete_after_start", {"presence_matrix_mismatch"}
    expected_presence = _presence_for_state(
        prepared.preregistration, state, completed, set(by_slot), started,
    )
    presence_valid = all(expected_presence[slot] == actual_presence[slot] for slot in completed if state == "terminal_reduced")
    if state != "terminal_reduced":
        presence_valid = expected_presence == actual_presence
    if not presence_valid:
        state, reasons = "incomplete_after_start", {"presence_matrix_mismatch"}
        expected_presence = _presence_for_state(
            prepared.preregistration, state, completed, set(by_slot), started,
        )
        presence_valid = expected_presence == actual_presence
    slots = list(requests)
    terminal_state = {
        "schema_version": schema.TERMINAL_STATE_SCHEMA,
        "group_manifest_sha256": prepared.manifest_sha256,
        "attempt_ordinal": prepared.launch_intent["attempt_ordinal"], "state": state,
        "reason_codes": sorted(reasons), "release_event_sha256": release_event_sha256,
        "start_spread_ns": start_spread_ns, "completed_slot_ids": sorted(completed),
        "dropped_slot_ids": sorted(set(slots) - completed),
        "node_receipt_sha256_by_slot": receipt_hashes,
        "expected_presence": expected_presence, "actual_presence": actual_presence,
        "presence_valid": presence_valid,
        "pre_validator_receipt_sha256": pre_validator_receipt_sha256,
        "post_validator_receipt_sha256": post_validator_receipt_sha256,
        "retry_allowed": schema.retry_allowed(state, prepared.launch_intent["attempt_ordinal"]),
    }
    return schema.validate_terminal_state(terminal_state, expected_node_count=count)
def _validation_digest(result: Any) -> str:
    if is_dataclass(result):
        value = asdict(result)
    elif isinstance(result, Mapping):
        value = dict(result)
    else:
        value = {"ok": bool(getattr(result, "ok", False)), "type": type(result).__name__}
    return schema.canonical_sha256(value)
def _validator_ok(result: Any) -> bool:
    return bool(result.get("ok")) if isinstance(result, Mapping) else bool(getattr(result, "ok", False))
def _baseline_envelope(result: Any, validator_kwargs: Mapping[str, Any]) -> BaselineEnvelope | None:
    if not all(hasattr(result, name) for name in ("baseline", "baseline_digest", "lineage")):
        return None
    try:
        digest = pass_witness_sha256(
            result=result,
            attempt_nonce=validator_kwargs["attempt_nonce"],
            invocation_nonce=validator_kwargs["pre_invocation_nonce"], phase="pre",
        )
        return BaselineEnvelope(result.baseline, result.baseline_digest, result.lineage, digest)
    except (KeyError, TypeError, ValueError):
        return None
def _run_validator(
    validator: Validator,
    preregistration: VerifiedT810Preregistration,
    validator_kwargs: Mapping[str, Any],
    *,
    claimed_state: str,
    previous_baseline: BaselineEnvelope | None,
) -> Any:
    kwargs = dict(validator_kwargs)
    kwargs.update({
        "preregistration": preregistration,
        "claimed_state": claimed_state,
        "previous_baseline": previous_baseline,
    })
    return validator(**kwargs)
def _early_terminal(
    prepared: PreparedGroup,
    state: str,
    reasons: Sequence[str],
    *,
    release_sha256: str | None,
    spread_ns: int | None,
    receipt_hashes: Mapping[str, str],
    pre_digest: str,
    post_digest: str,
) -> Mapping[str, Any]:
    slots = [slot["slot_id"] for slot in prepared.launch_intent["slots"]]
    expected = _presence_for_state(prepared.preregistration, state, set(), set(receipt_hashes))
    actual = {slot: list(expected[slot]) for slot in slots}
    receipt_map: dict[str, str | None] = {
        slot: receipt_hashes.get(slot) for slot in slots
    }
    if state != "pre_release_invalid" and any(value is None for value in receipt_map.values()):
        raise T810CoordinatorError("post-release terminal state lacks an exact node receipt")
    value = {
        "schema_version": schema.TERMINAL_STATE_SCHEMA,
        "group_manifest_sha256": prepared.manifest_sha256,
        "attempt_ordinal": prepared.launch_intent["attempt_ordinal"], "state": state,
        "reason_codes": list(reasons), "release_event_sha256": release_sha256,
        "start_spread_ns": spread_ns, "completed_slot_ids": [], "dropped_slot_ids": slots,
        "node_receipt_sha256_by_slot": receipt_map,
        "expected_presence": expected, "actual_presence": actual, "presence_valid": True,
        "pre_validator_receipt_sha256": pre_digest,
        "post_validator_receipt_sha256": post_digest,
        "retry_allowed": schema.retry_allowed(state, prepared.launch_intent["attempt_ordinal"]),
    }
    return schema.validate_terminal_state(value, expected_node_count=len(slots))
def _coordinate_authorized(
    config: Mapping[str, Any],
    preregistration: VerifiedT810Preregistration,
    witness: Mapping[str, Any],
    *,
    scheduler_run: SchedulerRun,
    clock_ns: Clock,
    wall_clock: WallClock,
    validator: Validator,
) -> CoordinationResult:
    policy = _object(config.get("admission_policy"), "admission policy")
    intent = _object(config.get("launch_intent"), "launch intent")
    verify_launch_authorization(
        witness, preregistration=preregistration, policy_sha256=_policy_digest(policy),
        run_kind=str(intent.get("run_kind", "")),
    )
    prepared = prepare_group(config, preregistration)
    initial_ns = clock_ns()
    _append_coordinator_event(
        prepared, "manifest_committed", {"manifest_sha256": prepared.manifest_sha256},
        wall_time=wall_clock(), monotonic_ns=initial_ns,
    )
    validator_kwargs = _object(config.get("validator_kwargs", {}), "validator kwargs")
    pre = _run_validator(
        validator, preregistration, validator_kwargs,
        claimed_state="pre_release_invalid", previous_baseline=None,
    )
    pre_digest = _validation_digest(pre)
    baseline = _baseline_envelope(pre, validator_kwargs)
    submission: Mapping[str, Any] | None = None
    release_sha: str | None = None
    release_ns = initial_ns
    spread: int | None = None
    ready_hashes: Mapping[str, str] = {}
    state = "pre_release_invalid"
    reasons: tuple[str, ...] = ("pre_inventory_mismatch",)
    terminal: Mapping[str, Any] | None = None
    if _validator_ok(pre):
        submission = submit_group(
            prepared, witness, scheduler_run=scheduler_run, wall_clock=wall_clock,
        )
        barrier = evaluate_ready_barrier(
            prepared, config.get("ready_events", ()),
            elapsed_seconds=config.get("ready_elapsed_seconds", schema.READY_TIMEOUT_SECONDS),
        )
        ready_hashes = barrier.receipt_sha256_by_slot
        for slot_id, digest in ready_hashes.items():
            _append_coordinator_event(
                prepared, "ready_received", {
                    "receipt_sha256": digest, "accepted": barrier.status == "release",
                    "reason_codes": [] if barrier.status == "release" else list(barrier.reason_codes),
                }, wall_time=wall_clock(), monotonic_ns=initial_ns, slot_id=slot_id,
            )
        if barrier.status != "release":
            reasons = barrier.reason_codes or ("ready_timeout",)
            _, cancel_sha = publish_cancel(prepared, witness, reasons, wall_clock=wall_clock)
            _append_coordinator_event(
                prepared, "cancel_published", {
                    "marker_sha256": cancel_sha, "reason_codes": list(reasons),
                }, wall_time=wall_clock(), monotonic_ns=initial_ns,
            )
        else:
            release_ns = clock_ns()
            _, release_sha = publish_release(prepared, witness, wall_clock=wall_clock)
            _append_coordinator_event(
                prepared, "release_published", {"marker_sha256": release_sha},
                wall_time=wall_clock(), monotonic_ns=release_ns,
            )
            raw_acks = config.get("ack_events", ())
            ack_events: list[tuple[Mapping[str, Any], int]] = []
            for item in raw_acks:
                event = item[0] if isinstance(item, tuple) else item
                ack_events.append((event, clock_ns()))
            ack = evaluate_start_acks(
                prepared, ack_events, release_marker_sha256=release_sha,
                release_published_ns=release_ns,
            )
            spread = ack.spread_ns
            for slot_id, digest in ack.receipt_sha256_by_slot.items():
                _append_coordinator_event(
                    prepared, "start_ack_received", {
                        "receipt_sha256": digest,
                        "received_monotonic_ns": release_ns + ack.latency_ns_by_slot[slot_id],
                        "latency_ns": ack.latency_ns_by_slot[slot_id],
                        "accepted": ack.accepted, "reason_codes": list(ack.reason_codes),
                    }, wall_time=wall_clock(),
                    monotonic_ns=release_ns + ack.latency_ns_by_slot[slot_id], slot_id=slot_id,
                )
            if not ack.accepted:
                state, reasons = "post_release_pre_measurement_invalid", ack.reason_codes
                _, cancel_sha = publish_cancel(prepared, witness, reasons, wall_clock=wall_clock)
                _append_coordinator_event(
                    prepared, "cancel_published", {
                        "marker_sha256": cancel_sha, "reason_codes": list(reasons),
                    }, wall_time=wall_clock(), monotonic_ns=release_ns + spread,
                )
            else:
                placeholder = schema.canonical_sha256({"post-validator": "pending"})
                terminal = verify_completion(
                    prepared, config.get("completion_receipts", ()),
                    release_event_sha256=release_sha, start_spread_ns=spread,
                    pre_validator_receipt_sha256=pre_digest,
                    post_validator_receipt_sha256=placeholder,
                )
                state, reasons = terminal["state"], tuple(terminal["reason_codes"])
                for receipt in config.get("completion_receipts", ()):
                    slot_id = receipt.get("slot_id")
                    if slot_id in terminal["node_receipt_sha256_by_slot"]:
                        _append_coordinator_event(
                            prepared, "completion_received", {
                                "receipt_sha256": receipt["node_receipt_sha256"],
                                "accepted": state in {"valid", "terminal_reduced"},
                                "reason_codes": [] if state in {"valid", "terminal_reduced"}
                                else list(reasons),
                            }, wall_time=wall_clock(), monotonic_ns=release_ns + spread,
                            slot_id=slot_id,
                        )
    post = _run_validator(
        validator, preregistration, validator_kwargs,
        claimed_state=state, previous_baseline=baseline,
    )
    post_digest = _validation_digest(post)
    if terminal is None:
        terminal = _early_terminal(
            prepared, state, reasons, release_sha256=release_sha, spread_ns=spread,
            receipt_hashes=ready_hashes, pre_digest=pre_digest, post_digest=post_digest,
        )
    else:
        terminal = dict(terminal)
        terminal["post_validator_receipt_sha256"] = post_digest
        if not _validator_ok(post) and terminal["state"] in {"valid", "terminal_reduced"}:
            terminal["state"] = "incomplete_after_start"
            terminal["reason_codes"] = ["post_inventory_mismatch"]
            terminal["retry_allowed"] = False
        terminal = schema.validate_terminal_state(
            terminal, expected_node_count=len(prepared.launch_intent["slots"]),
        )
    _append_coordinator_event(
        prepared, "terminal_decided", {"terminal_state_sha256": schema.canonical_sha256(terminal)},
        wall_time=wall_clock(), monotonic_ns=release_ns + (spread or 0),
    )
    _write_create_only(prepared.terminal_path, terminal)
    return CoordinationResult(prepared, submission, terminal)
def coordinate(
    config: Mapping[str, Any],
    preregistration: VerifiedT810Preregistration,
    witness: Mapping[str, Any] | None,
) -> CoordinationResult:
    policy = _object(config.get("admission_policy"), "admission policy")
    intent = _object(config.get("launch_intent"), "launch intent")
    verify_launch_authorization(
        witness, preregistration=preregistration, policy_sha256=_policy_digest(policy),
        run_kind=str(intent.get("run_kind", "")),
    )
    return _coordinate_authorized(
        config, preregistration, witness,
        scheduler_run=_subprocess_scheduler, clock_ns=time.monotonic_ns,
        wall_clock=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        validator=validate_t810,
    )
def _subprocess_scheduler(
    argv: Sequence[str], *, cwd: str, env: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv), cwd=cwd, env=dict(env), text=True, capture_output=True, check=False,
    )
def _load_cli_json(path: str, name: str) -> Mapping[str, Any]:
    return _read_json(Path(path), name)
def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="coordinate one authorized T-810 attempt")
    parser.add_argument("--config", required=True)
    parser.add_argument("--approval-receipt", required=True)
    parser.add_argument("--preregistration", default=str(PREREG_PATH))
    parser.add_argument("--authorization-witness")
    args = parser.parse_args(argv)
    if args.authorization_witness is None:
        return 2
    try:
        approval = _load_cli_json(args.approval_receipt, "approval receipt")
        preregistration = load_t810_preregistration(
            Path(args.preregistration),
            approval_receipt=ApprovalReceipt(
                artifact_sha256=approval["artifact_sha256"],
                approval_id=approval["approval_id"],
                schema_version=approval.get("schema_version", APPROVAL_RECEIPT_SCHEMA_VERSION),
            ),
        )
        config = _load_cli_json(args.config, "coordinator config")
        witness = _load_cli_json(args.authorization_witness, "launch authorization witness")
        coordinate(config, preregistration, witness)
    except (KeyError, OSError, ValueError, T810CoordinatorError):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
