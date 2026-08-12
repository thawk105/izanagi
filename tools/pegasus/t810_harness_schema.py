"""Pure, fail-closed schemas for the T-810 Pegasus measurement harness."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping, TypeAlias

JSONValue: TypeAlias = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]
Document: TypeAlias = dict[str, Any]

LAUNCH_INTENT_SCHEMA = "t810-launch-intent/v1"
LAUNCH_AUTHORIZATION_SCHEMA = "t810-launch-authorization/v1"
GROUP_MANIFEST_SCHEMA = "t810-group-manifest/v1"
SUBMISSION_RECEIPT_SCHEMA = "t810-submission-receipt/v1"
CONTROL_MARKER_SCHEMA = "t810-control-marker/v1"
NODE_EVENT_SCHEMA = "t810-node-event/v1"
COORDINATOR_EVENT_SCHEMA = "t810-coordinator-event/v1"
TERMINAL_STATE_SCHEMA = "t810-terminal-state/v1"
QSTAT_F_TRANSCRIPT_SCHEMA = "t810-qstat-f-transcript/v1"
QSTAT_Q_TRANSCRIPT_SCHEMA = "t810-qstat-q-transcript/v1"
QSUB_TRANSCRIPT_SCHEMA = "t810-qsub-transcript/v1"

NODE_COUNT = 13
ROUND_COUNT = 10
READY_TIMEOUT_SECONDS = 1200
START_SPREAD_MAX_NS = 5_000_000_000
RUN_KINDS = frozenset({"builder", "liveness", "main"})
TERMINAL_STATES = frozenset({
    "pre_release_invalid", "post_release_pre_measurement_invalid",
    "incomplete_after_start", "terminal_reduced", "valid",
})

_PRE = "pre_release"
_POST = "post_release_pre_measurement"
_STARTED = "after_measurement_start"
_STATE_ROWS = {
    (_PRE, reason): "pre_release_invalid" for reason in (
        "ready_timeout", "hostname_count_mismatch", "duplicate_hostname",
        "unapproved_hostname", "hostname_mismatch", "binary_copy_hash_mismatch",
        "quiet_gate_failed", "submission_argv_mismatch", "pre_inventory_mismatch",
        "submission_failed", "guard_denied", "budget_denied", "preflight_failed",
    )
} | {
    (_POST, reason): "post_release_pre_measurement_invalid" for reason in (
        "start_spread_exceeded", "cancel_marker_observed",
        "dependency_manifest_mismatch", "module_list_mismatch",
        "trace_symbols_present", "numa_nodes_mismatch", "release-marker-mismatch",
        "ack-missing", "ack-unknown-slot", "ack-duplicate",
    )
} | {
    (_STARTED, reason): "incomplete_after_start" for reason in (
        "insufficient_completions", "completed_rounds_missing",
        "binary_after_hash_mismatch", "post_inventory_mismatch",
        "presence_matrix_mismatch",
    )
} | {
    (_STARTED, "single_job_dropped"): "terminal_reduced",
    (_STARTED, "all_jobs_complete"): "valid",
}
BOUNDARY_REASON_TO_STATE: Mapping[tuple[str, str], str] = MappingProxyType(_STATE_ROWS)
REASON_CODES = frozenset(reason for _, reason in BOUNDARY_REASON_TO_STATE)
del _STATE_ROWS

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SLOT = re.compile(r"slot-[0-9]{2}\Z")


class T810SchemaError(ValueError):
    """A single fail-closed T-810 schema violation."""


def _fail(path: str, reason: str) -> None:
    raise T810SchemaError(f"{path}: {reason}")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"$.{key}", "duplicate key")
        result[key] = value
    return result


def parse_json(raw: str | bytes | bytearray) -> JSONValue:
    """Parse JSON while rejecting duplicate object keys."""
    try:
        value = json.loads(raw, object_pairs_hook=_pairs)
    except T810SchemaError:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
        _fail("$", f"invalid JSON ({type(exc).__name__})")
    _json_value(value, "$")
    return value


def _json_value(value: Any, path: str) -> None:
    if value is None or isinstance(value, (bool, str)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if math.isfinite(value):
            return
        _fail(path, "non-finite number")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                _fail(path, "object key is not str")
            _json_value(item, f"{path}.{key}")
        return
    _fail(path, "not a JSON value")


def canonical_json_bytes(value: Any) -> bytes:
    _json_value(value, "$")
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    if not isinstance(value, bytes):
        _fail("$", "digest input is not bytes")
    return hashlib.sha256(value).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def release_token_commitment(nonce: str) -> str:
    _string(nonce, "$.nonce")
    return sha256_bytes(nonce.encode("utf-8"))


def _object(value: Any, fields: frozenset[str], path: str) -> Document:
    if not isinstance(value, Mapping):
        _fail(path, "not an object")
    for key in value:
        if not isinstance(key, str):
            _fail(path, "object key is not str")
    actual = set(value)
    missing = fields - actual
    if missing:
        _fail(f"{path}.{sorted(missing)[0]}", "missing field")
    unknown = actual - fields
    if unknown:
        _fail(f"{path}.{sorted(unknown)[0]}", "unknown field")
    return dict(value)


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(path, "not a non-empty str")
    return value


def _integer(value: Any, path: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        _fail(path, f"not an int >= {minimum}")
    return value


def _number(value: Any, path: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        _fail(path, "not a finite number")
    return value


def _boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        _fail(path, "not a bool")
    return value


def _hash(value: Any, path: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        _fail(path, "not a lowercase SHA-256 hex digest")
    return value


def _literal(value: Any, allowed: frozenset[str], path: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        _fail(path, "unknown literal")
    return value


def _path(value: Any, path: str) -> str:
    value = _string(value, path)
    if (not value.startswith("/") or value == "/" or value.startswith("//")
            or value.endswith("/") or any(part in {"", ".", ".."} for part in value[1:].split("/"))
            or str(PurePosixPath(value)) != value):
        _fail(path, "not a canonical absolute path")
    return value


def _artifact_path(value: Any, path: str) -> str:
    value = _string(value, path)
    if (value.startswith("/") or value.endswith("/")
            or any(part in {"", ".", ".."} for part in value.split("/"))
            or str(PurePosixPath(value)) != value):
        _fail(path, "not a canonical relative artifact path")
    return value


def _argv(value: Any, path: str) -> list[str]:
    if not isinstance(value, list) or not value:
        _fail(path, "not a non-empty argv list")
    for index, item in enumerate(value):
        _string(item, f"{path}[{index}]")
    return value


def _strings(value: Any, path: str, *, unique: bool = False) -> list[str]:
    if not isinstance(value, list):
        _fail(path, "not a list")
    for index, item in enumerate(value):
        _string(item, f"{path}[{index}]")
    if unique and len(value) != len(set(value)):
        _fail(path, "contains duplicate values")
    return value


def _reasons(value: Any, path: str) -> list[str]:
    values = _strings(value, path, unique=True)
    for index, reason in enumerate(values):
        if reason not in REASON_CODES:
            _fail(f"{path}[{index}]", "unknown reason code")
    return values


def _schema(document: Document, literal: str, path: str = "$") -> None:
    if document["schema_version"] != literal:
        _fail(f"{path}.schema_version", "schema literal mismatch")


_SLOT_FIELDS = frozenset({
    "slot_id", "logical_request_id", "job_name", "qsub_argv", "wrapper_argv",
    "pbs_stdout_path", "pbs_stderr_path", "binary_source_path", "binary_sha256",
    "wrapper_path", "wrapper_sha256", "runner_policy_path", "runner_policy_sha256",
})
_INTENT_FIELDS = frozenset({
    "schema_version", "group_id", "run_kind", "attempt_ordinal", "policy_sha256",
    "preregistration_sha256", "prereg_approval_id", "created_at", "node_count",
    "round_count", "ready_timeout_seconds", "start_spread_max_ns", "work_root",
    "output_root", "slots",
})


def validate_launch_intent(value: Any) -> Document:
    doc = _object(value, _INTENT_FIELDS, "$")
    _schema(doc, LAUNCH_INTENT_SCHEMA)
    for field in ("group_id", "prereg_approval_id", "created_at"):
        _string(doc[field], f"$.{field}")
    _literal(doc["run_kind"], RUN_KINDS, "$.run_kind")
    if doc["attempt_ordinal"] not in (1, 2) or isinstance(doc["attempt_ordinal"], bool):
        _fail("$.attempt_ordinal", "must be exact int 1 or 2")
    for field in ("policy_sha256", "preregistration_sha256"):
        _hash(doc[field], f"$.{field}")
    for field in ("node_count", "round_count"):
        _integer(doc[field], f"$.{field}", minimum=1)
    for field, expected in (("ready_timeout_seconds", READY_TIMEOUT_SECONDS),
                            ("start_spread_max_ns", START_SPREAD_MAX_NS)):
        if isinstance(doc[field], bool) or doc[field] != expected:
            _fail(f"$.{field}", f"must be exact int {expected}")
    work_root, output_root = _path(doc["work_root"], "$.work_root"), _path(doc["output_root"], "$.output_root")
    if work_root == output_root:
        _fail("$.output_root", "must differ from work_root")
    slots = doc["slots"]
    if not isinstance(slots, list) or len(slots) != doc["node_count"]:
        _fail("$.slots", "length does not equal node_count")
    unique: dict[str, set[str]] = {name: set() for name in ("logical_request_id", "job_name", "pbs_stdout_path", "pbs_stderr_path")}
    for index, raw in enumerate(slots):
        path = f"$.slots[{index}]"
        slot = _object(raw, _SLOT_FIELDS, path)
        if slot["slot_id"] != f"slot-{index:02d}":
            _fail(f"{path}.slot_id", "not the continuous canonical slot id")
        for field in ("logical_request_id", "job_name"):
            item = _string(slot[field], f"{path}.{field}")
            if item in unique[field]:
                _fail(f"{path}.{field}", "duplicate value")
            unique[field].add(item)
        for field in ("pbs_stdout_path", "pbs_stderr_path", "binary_source_path", "wrapper_path", "runner_policy_path"):
            item = _path(slot[field], f"{path}.{field}")
            if field in unique:
                if item in unique[field]:
                    _fail(f"{path}.{field}", "duplicate value")
                unique[field].add(item)
        for field in ("binary_sha256", "wrapper_sha256", "runner_policy_sha256"):
            _hash(slot[field], f"{path}.{field}")
        qsub = _argv(slot["qsub_argv"], f"{path}.qsub_argv")
        wrapper = _argv(slot["wrapper_argv"], f"{path}.wrapper_argv")
        if len(wrapper) < 2 or wrapper[:2] != ["python3.10", slot["wrapper_path"]]:
            _fail(f"{path}.wrapper_argv", "does not use python3.10 and wrapper_path")
        for option, field in (("-o", "pbs_stdout_path"), ("-e", "pbs_stderr_path")):
            if qsub.count(option) != 1 or qsub.index(option) + 1 >= len(qsub) or qsub[qsub.index(option) + 1] != slot[field]:
                _fail(f"{path}.qsub_argv", f"does not bind {option} to {field}")
        for field in ("pbs_stdout_path", "pbs_stderr_path"):
            if not slot[field].startswith(output_root + "/"):
                _fail(f"{path}.{field}", "not below output_root")
    return doc


_LAUNCH_AUTHORIZATION_FIELDS = frozenset({
    "schema_version", "approval_id", "preregistration_sha256", "policy_sha256",
    "run_kinds", "issued_on", "nonce",
})


def validate_launch_authorization(value: Any) -> Document:
    doc = _object(value, _LAUNCH_AUTHORIZATION_FIELDS, "$")
    _schema(doc, LAUNCH_AUTHORIZATION_SCHEMA)
    for field in ("approval_id", "issued_on", "nonce"):
        _string(doc[field], f"$.{field}")
    for field in ("preregistration_sha256", "policy_sha256"):
        _hash(doc[field], f"$.{field}")
    run_kinds = _strings(doc["run_kinds"], "$.run_kinds", unique=True)
    for index, run_kind in enumerate(run_kinds):
        _literal(run_kind, RUN_KINDS, f"$.run_kinds[{index}]")
    return doc


_MANIFEST_FIELDS = frozenset({
    "schema_version", "group_id", "created_at", "launch_intent_sha256",
    "guard_receipt_sha256", "budget_receipt_sha256", "release_token_commitment",
})


def validate_group_manifest(value: Any) -> Document:
    doc = _object(value, _MANIFEST_FIELDS, "$")
    _schema(doc, GROUP_MANIFEST_SCHEMA)
    _string(doc["group_id"], "$.group_id")
    _string(doc["created_at"], "$.created_at")
    for field in ("launch_intent_sha256", "guard_receipt_sha256", "budget_receipt_sha256", "release_token_commitment"):
        _hash(doc[field], f"$.{field}")
    return doc


_REQUEST_FIELDS = frozenset({
    "slot_id", "logical_request_id", "job_name", "qsub_argv", "qsub_rc",
    "qsub_stdout", "qsub_stderr", "pbs_request_id",
})


def validate_submission_receipt(value: Any, *, expected_node_count: int = NODE_COUNT) -> Document:
    doc = _object(value, frozenset({"schema_version", "group_manifest_sha256", "created_at", "requests"}), "$")
    _schema(doc, SUBMISSION_RECEIPT_SCHEMA)
    _hash(doc["group_manifest_sha256"], "$.group_manifest_sha256")
    _string(doc["created_at"], "$.created_at")
    requests = doc["requests"]
    _integer(expected_node_count, "$.expected_node_count", minimum=1)
    if not isinstance(requests, list) or len(requests) != expected_node_count:
        _fail("$.requests", f"must contain exactly {expected_node_count} entries")
    pbs_ids: set[str] = set()
    for index, raw in enumerate(requests):
        path = f"$.requests[{index}]"
        request = _object(raw, _REQUEST_FIELDS, path)
        if request["slot_id"] != f"slot-{index:02d}":
            _fail(f"{path}.slot_id", "not the continuous canonical slot id")
        for field in ("logical_request_id", "job_name", "qsub_stdout", "qsub_stderr"):
            if not isinstance(request[field], str):
                _fail(f"{path}.{field}", "not a str")
        _argv(request["qsub_argv"], f"{path}.qsub_argv")
        _integer(request["qsub_rc"], f"{path}.qsub_rc")
        pbs_id = request["pbs_request_id"]
        if pbs_id is not None:
            _string(pbs_id, f"{path}.pbs_request_id")
            if pbs_id in pbs_ids:
                _fail(f"{path}.pbs_request_id", "duplicate value")
            pbs_ids.add(pbs_id)
        if request["qsub_rc"] == 0 and pbs_id is None:
            _fail(f"{path}.pbs_request_id", "null for successful qsub")
        if request["qsub_rc"] != 0 and pbs_id is not None:
            _fail(f"{path}.pbs_request_id", "must be null for failed qsub")
    return doc


def validate_control_marker(
    value: Any, *, expected_release_token_commitment: str | None = None,
) -> Document:
    if not isinstance(value, Mapping):
        _fail("$", "not an object")
    kind = value.get("kind")
    common = {"schema_version", "group_manifest_sha256", "group_id", "kind", "published_at"}
    fields = frozenset(common | ({"nonce"} if kind == "release" else {"reason_codes"} if kind == "cancel" else set()))
    doc = _object(value, fields, "$")
    _schema(doc, CONTROL_MARKER_SCHEMA)
    _literal(kind, frozenset({"release", "cancel"}), "$.kind")
    _hash(doc["group_manifest_sha256"], "$.group_manifest_sha256")
    _string(doc["group_id"], "$.group_id")
    _string(doc["published_at"], "$.published_at")
    if kind == "release":
        nonce = _string(doc["nonce"], "$.nonce")
        if expected_release_token_commitment is not None:
            _hash(expected_release_token_commitment, "$.expected_release_token_commitment")
            if release_token_commitment(nonce) != expected_release_token_commitment:
                _fail("$.nonce", "not the committed release-token preimage")
    else:
        if not _reasons(doc["reason_codes"], "$.reason_codes"):
            _fail("$.reason_codes", "cancel requires at least one reason")
    return doc


_NODE_FIELDS = frozenset({
    "schema_version", "group_manifest_sha256", "group_id", "slot_id",
    "logical_request_id", "pbs_request_id", "sequence", "event", "observed_at",
    "previous_event_sha256", "payload",
})
_HARDWARE_FIELDS = frozenset({"cpu_model", "physical_cores", "hyperthreading", "memory", "numa_nodes", "cache", "frequency_policy"})


def _isolation(value: Any, path: str) -> None:
    item = _object(value, frozenset({"inventory_sha256", "competing_processes_sha256"}), path)
    _hash(item["inventory_sha256"], f"{path}.inventory_sha256")
    _hash(item["competing_processes_sha256"], f"{path}.competing_processes_sha256")


def _preflight(value: Any, path: str) -> None:
    fields = frozenset({
        "assigned_hostname", "actual_hostname", "hardware", "interpreter",
        "competing_processes", "quiet_samples", "binary_source_sha256",
        "binary_copy_sha256", "dependency_manifest_sha256", "module_list_sha256",
        "trace_symbols", "isolation_before", "observed_submission_argv", "repo_absence",
        "passed", "reason_codes",
    })
    item = _object(value, fields, path)
    _string(item["assigned_hostname"], f"{path}.assigned_hostname")
    _string(item["actual_hostname"], f"{path}.actual_hostname")
    hardware = _object(item["hardware"], _HARDWARE_FIELDS, f"{path}.hardware")
    for field in ("cpu_model", "memory", "frequency_policy"):
        _string(hardware[field], f"{path}.hardware.{field}")
    _integer(hardware["physical_cores"], f"{path}.hardware.physical_cores", minimum=1)
    _integer(hardware["numa_nodes"], f"{path}.hardware.numa_nodes", minimum=1)
    _boolean(hardware["hyperthreading"], f"{path}.hardware.hyperthreading")
    _strings(hardware["cache"], f"{path}.hardware.cache")
    interpreter = _object(item["interpreter"], frozenset({"executable", "version"}), f"{path}.interpreter")
    _path(interpreter["executable"], f"{path}.interpreter.executable")
    _string(interpreter["version"], f"{path}.interpreter.version")
    processes = item["competing_processes"]
    if not isinstance(processes, list):
        _fail(f"{path}.competing_processes", "not a list")
    process_fields = frozenset({"pid", "uid", "cpu_affinity", "command"})
    for index, raw in enumerate(processes):
        pp = f"{path}.competing_processes[{index}]"
        process = _object(raw, process_fields, pp)
        _integer(process["pid"], f"{pp}.pid", minimum=1)
        if process["uid"] is not None:
            _integer(process["uid"], f"{pp}.uid")
        if process["cpu_affinity"] is not None:
            if not isinstance(process["cpu_affinity"], list):
                _fail(f"{pp}.cpu_affinity", "not a list or null")
            for cpu_index, cpu in enumerate(process["cpu_affinity"]):
                _integer(cpu, f"{pp}.cpu_affinity[{cpu_index}]")
        _string(process["command"], f"{pp}.command")
    samples = item["quiet_samples"]
    if not isinstance(samples, list) or not samples:
        _fail(f"{path}.quiet_samples", "not a non-empty list")
    for index, raw in enumerate(samples):
        sp = f"{path}.quiet_samples[{index}]"
        sample = _object(raw, frozenset({"observed_at", "load_average_1m"}), sp)
        _string(sample["observed_at"], f"{sp}.observed_at")
        _number(sample["load_average_1m"], f"{sp}.load_average_1m")
    for field in ("binary_source_sha256", "binary_copy_sha256", "dependency_manifest_sha256", "module_list_sha256"):
        _hash(item[field], f"{path}.{field}")
    _strings(item["trace_symbols"], f"{path}.trace_symbols", unique=True)
    _isolation(item["isolation_before"], f"{path}.isolation_before")
    _argv(item["observed_submission_argv"], f"{path}.observed_submission_argv")
    absence = _object(item["repo_absence"], frozenset({"package_repo_free", "roots_repo_external", "git_ancestor_absent", "pbs_workdir_repo_external"}), f"{path}.repo_absence")
    for field in absence:
        _boolean(absence[field], f"{path}.repo_absence.{field}")
    _boolean(item["passed"], f"{path}.passed")
    _reasons(item["reason_codes"], f"{path}.reason_codes")


def _rounds(value: Any, path: str) -> None:
    if not isinstance(value, list):
        _fail(path, "not a list")
    fields = frozenset({"index", "started_at", "ended_at", "effective_clock", "throughput", "exit_code"})
    for index, raw in enumerate(value, 1):
        rp = f"{path}[{index - 1}]"
        item = _object(raw, fields, rp)
        if item["index"] != index or isinstance(item["index"], bool):
            _fail(f"{rp}.index", "not a continuous one-based index")
        for field in ("started_at", "ended_at"):
            _string(item[field], f"{rp}.{field}")
        _number(item["effective_clock"], f"{rp}.effective_clock")
        _number(item["throughput"], f"{rp}.throughput")
        _integer(item["exit_code"], f"{rp}.exit_code")


def validate_node_event(value: Any) -> Document:
    doc = _object(value, _NODE_FIELDS, "$")
    _schema(doc, NODE_EVENT_SCHEMA)
    _hash(doc["group_manifest_sha256"], "$.group_manifest_sha256")
    for field in ("group_id", "logical_request_id", "pbs_request_id", "observed_at"):
        _string(doc[field], f"$.{field}")
    if not isinstance(doc["slot_id"], str) or _SLOT.fullmatch(doc["slot_id"]) is None:
        _fail("$.slot_id", "not a canonical slot id")
    sequence = _integer(doc["sequence"], "$.sequence")
    _hash(doc["previous_event_sha256"], "$.previous_event_sha256", nullable=True)
    if (sequence == 0) != (doc["previous_event_sha256"] is None):
        _fail("$.previous_event_sha256", "null iff sequence is zero")
    event = _literal(doc["event"], frozenset({"preflight", "ready", "start_ack", "measurement", "terminal"}), "$.event")
    payload_path = "$.payload"
    if event == "preflight":
        _preflight(doc["payload"], payload_path)
    elif event == "ready":
        item = _object(doc["payload"], frozenset({"preflight_event_sha256", "ready", "reason_codes"}), payload_path)
        _hash(item["preflight_event_sha256"], f"{payload_path}.preflight_event_sha256")
        _boolean(item["ready"], f"{payload_path}.ready")
        _reasons(item["reason_codes"], f"{payload_path}.reason_codes")
    elif event == "start_ack":
        item = _object(doc["payload"], frozenset({"release_marker_sha256", "cancel_marker_absent", "ack_nonce"}), payload_path)
        _hash(item["release_marker_sha256"], f"{payload_path}.release_marker_sha256")
        _boolean(item["cancel_marker_absent"], f"{payload_path}.cancel_marker_absent")
        _string(item["ack_nonce"], f"{payload_path}.ack_nonce")
    elif event == "measurement":
        item = _object(doc["payload"], frozenset({"rounds", "benchmark_rc", "binary_after_sha256", "isolation_after"}), payload_path)
        _rounds(item["rounds"], f"{payload_path}.rounds")
        _integer(item["benchmark_rc"], f"{payload_path}.benchmark_rc")
        _hash(item["binary_after_sha256"], f"{payload_path}.binary_after_sha256")
        _isolation(item["isolation_after"], f"{payload_path}.isolation_after")
    else:
        item = _object(doc["payload"], frozenset({"state", "reason_codes", "measurement_started", "completed_rounds"}), payload_path)
        _literal(item["state"], TERMINAL_STATES, f"{payload_path}.state")
        _reasons(item["reason_codes"], f"{payload_path}.reason_codes")
        _boolean(item["measurement_started"], f"{payload_path}.measurement_started")
        _integer(item["completed_rounds"], f"{payload_path}.completed_rounds")
    return doc


_COORDINATOR_DETAILS = {
    "manifest_committed": frozenset({"manifest_sha256"}),
    "ready_received": frozenset({"receipt_sha256", "accepted", "reason_codes"}),
    "release_published": frozenset({"marker_sha256"}),
    "start_ack_received": frozenset({
        "receipt_sha256", "received_monotonic_ns", "latency_ns", "accepted", "reason_codes",
    }),
    "cancel_published": frozenset({"marker_sha256", "reason_codes"}),
    "completion_received": frozenset({"receipt_sha256", "accepted", "reason_codes"}),
    "terminal_decided": frozenset({"terminal_state_sha256"}),
}


def validate_coordinator_event(value: Any) -> Document:
    fields = frozenset({"schema_version", "group_manifest_sha256", "sequence", "event", "wall_time", "coordinator_monotonic_ns", "slot_id", "previous_event_sha256", "details"})
    doc = _object(value, fields, "$")
    _schema(doc, COORDINATOR_EVENT_SCHEMA)
    _hash(doc["group_manifest_sha256"], "$.group_manifest_sha256")
    sequence = _integer(doc["sequence"], "$.sequence")
    _string(doc["wall_time"], "$.wall_time")
    _integer(doc["coordinator_monotonic_ns"], "$.coordinator_monotonic_ns")
    _hash(doc["previous_event_sha256"], "$.previous_event_sha256", nullable=True)
    if (sequence == 0) != (doc["previous_event_sha256"] is None):
        _fail("$.previous_event_sha256", "null iff sequence is zero")
    event = doc["event"]
    if not isinstance(event, str) or event not in _COORDINATOR_DETAILS:
        _fail("$.event", "unknown literal")
    slot_events = {"ready_received", "start_ack_received", "completion_received"}
    if event in slot_events:
        if not isinstance(doc["slot_id"], str) or _SLOT.fullmatch(doc["slot_id"]) is None:
            _fail("$.slot_id", "not a canonical slot id")
    elif doc["slot_id"] is not None:
        _fail("$.slot_id", "must be null for group event")
    details = _object(doc["details"], _COORDINATOR_DETAILS[event], "$.details")
    for field, item in details.items():
        path = f"$.details.{field}"
        if field.endswith("sha256"):
            _hash(item, path)
        elif field in {"accepted"}:
            _boolean(item, path)
        elif field in {"received_monotonic_ns", "latency_ns"}:
            _integer(item, path)
        elif field == "reason_codes":
            _reasons(item, path)
    return doc


def classify_terminal_state(boundary: str, reason_code: str) -> str:
    try:
        return BOUNDARY_REASON_TO_STATE[(boundary, reason_code)]
    except (KeyError, TypeError):
        _fail("$.reason_code", "not allowed at boundary")


def retry_allowed(state: str, attempt_ordinal: int) -> bool:
    _literal(state, TERMINAL_STATES, "$.state")
    if attempt_ordinal not in (1, 2) or isinstance(attempt_ordinal, bool):
        _fail("$.attempt_ordinal", "must be exact int 1 or 2")
    return state == "pre_release_invalid" and attempt_ordinal == 1


_TERMINAL_FIELDS = frozenset({
    "schema_version", "group_manifest_sha256", "attempt_ordinal", "state",
    "reason_codes", "release_event_sha256", "start_spread_ns", "completed_slot_ids",
    "dropped_slot_ids", "node_receipt_sha256_by_slot", "expected_presence",
    "actual_presence", "presence_valid", "pre_validator_receipt_sha256",
    "post_validator_receipt_sha256", "retry_allowed",
})


def validate_terminal_state(value: Any, *, expected_node_count: int = NODE_COUNT) -> Document:
    doc = _object(value, _TERMINAL_FIELDS, "$")
    _schema(doc, TERMINAL_STATE_SCHEMA)
    _hash(doc["group_manifest_sha256"], "$.group_manifest_sha256")
    ordinal = doc["attempt_ordinal"]
    state = _literal(doc["state"], TERMINAL_STATES, "$.state")
    reasons = _reasons(doc["reason_codes"], "$.reason_codes")
    if not reasons:
        _fail("$.reason_codes", "must contain at least one reason")
    boundary = (_PRE if state == "pre_release_invalid" else _POST
                if state == "post_release_pre_measurement_invalid" else _STARTED)
    for reason in reasons:
        if classify_terminal_state(boundary, reason) != state:
            _fail("$.reason_codes", "contains a reason not classified to state")
    release = _hash(doc["release_event_sha256"], "$.release_event_sha256", nullable=True)
    spread = doc["start_spread_ns"]
    if state == "pre_release_invalid":
        if release is not None or spread is not None:
            _fail("$.release_event_sha256", "release evidence forbidden before release")
    else:
        if release is None:
            _fail("$.release_event_sha256", "release evidence required")
        _integer(spread, "$.start_spread_ns")
    if "start_spread_exceeded" in reasons and spread <= START_SPREAD_MAX_NS:
        _fail("$.start_spread_ns", "does not exceed frozen maximum")
    completed = _strings(doc["completed_slot_ids"], "$.completed_slot_ids", unique=True)
    dropped = _strings(doc["dropped_slot_ids"], "$.dropped_slot_ids", unique=True)
    _integer(expected_node_count, "$.expected_node_count", minimum=1)
    all_slots = completed + dropped
    expected_slots = [f"slot-{index:02d}" for index in range(expected_node_count)]
    if sorted(all_slots) != expected_slots or len(all_slots) != expected_node_count:
        _fail("$.completed_slot_ids", "completed/dropped are not an exact slot partition")
    if state in {"pre_release_invalid", "post_release_pre_measurement_invalid"} and completed:
        _fail("$.completed_slot_ids", "completion forbidden before measurement_start")
    if state == "valid" and (len(completed) != expected_node_count or dropped):
        _fail("$.completed_slot_ids", "valid requires all jobs complete")
    if state == "terminal_reduced" and (len(completed) != expected_node_count - 1 or len(dropped) != 1):
        _fail("$.completed_slot_ids", "terminal_reduced requires exactly N-1 complete")
    integrity_reasons = {"completed_rounds_missing", "binary_after_hash_mismatch", "post_inventory_mismatch", "presence_matrix_mismatch"}
    if state == "incomplete_after_start" and len(completed) > expected_node_count - 2 and not integrity_reasons.intersection(reasons):
        _fail("$.completed_slot_ids", "state requires <= N-2 complete or completed-job integrity failure")
    receipt_map = _object(doc["node_receipt_sha256_by_slot"], frozenset(expected_slots), "$.node_receipt_sha256_by_slot")
    for slot, digest in receipt_map.items():
        _hash(digest, f"$.node_receipt_sha256_by_slot.{slot}", nullable=state == "pre_release_invalid")
    matrices: dict[str, Document] = {}
    for field in ("expected_presence", "actual_presence"):
        matrix = _object(doc[field], frozenset(expected_slots), f"$.{field}")
        matrices[field] = matrix
        for slot, paths in matrix.items():
            values = _strings(paths, f"$.{field}.{slot}", unique=True)
            for index, item in enumerate(values):
                _artifact_path(item, f"$.{field}.{slot}[{index}]")
    evaluated = completed if state == "terminal_reduced" else expected_slots
    actual_valid = all(matrices["expected_presence"][slot] == matrices["actual_presence"][slot] for slot in evaluated)
    _boolean(doc["presence_valid"], "$.presence_valid")
    if doc["presence_valid"] != actual_valid:
        _fail("$.presence_valid", "does not match exact evaluated presence")
    _hash(doc["pre_validator_receipt_sha256"], "$.pre_validator_receipt_sha256")
    _hash(doc["post_validator_receipt_sha256"], "$.post_validator_receipt_sha256")
    _boolean(doc["retry_allowed"], "$.retry_allowed")
    if doc["retry_allowed"] != retry_allowed(state, ordinal):
        _fail("$.retry_allowed", "does not match frozen retry rule")
    return doc


def _transcript(value: Any, schema: str, fields: frozenset[str]) -> Document:
    doc = _object(value, fields, "$")
    _schema(doc, schema)
    _string(doc["captured_at"], "$.captured_at")
    _integer(doc["rc"], "$.rc")
    for field in ("stdout", "stderr"):
        if not isinstance(doc[field], str):
            _fail(f"$.{field}", "not a str")
    _argv(doc["command_argv"], "$.command_argv")
    return doc


def validate_qstat_f_transcript(value: Any) -> Document:
    fields = frozenset({"schema_version", "captured_at", "request_id", "command_argv", "rc", "stdout", "stderr"})
    doc = _transcript(value, QSTAT_F_TRANSCRIPT_SCHEMA, fields)
    _string(doc["request_id"], "$.request_id")
    if doc["command_argv"] != ["qstat", "-f", doc["request_id"]]:
        _fail("$.command_argv", "not canonical qstat -f argv")
    return doc


def validate_qstat_q_transcript(value: Any) -> Document:
    fields = frozenset({"schema_version", "captured_at", "command_argv", "rc", "stdout", "stderr"})
    doc = _transcript(value, QSTAT_Q_TRANSCRIPT_SCHEMA, fields)
    if doc["command_argv"] != ["qstat", "-Q"]:
        _fail("$.command_argv", "not canonical qstat -Q argv")
    return doc


def validate_qsub_transcript(value: Any) -> Document:
    fields = frozenset({"schema_version", "captured_at", "slot_id", "command_argv", "rc", "stdout", "stderr", "pbs_request_id"})
    doc = _transcript(value, QSUB_TRANSCRIPT_SCHEMA, fields)
    if not isinstance(doc["slot_id"], str) or _SLOT.fullmatch(doc["slot_id"]) is None:
        _fail("$.slot_id", "not a canonical slot id")
    if doc["command_argv"][0] != "qsub":
        _fail("$.command_argv", "not qsub argv")
    pbs_id = doc["pbs_request_id"]
    if pbs_id is not None:
        _string(pbs_id, "$.pbs_request_id")
    if (doc["rc"] == 0) != (pbs_id is not None):
        _fail("$.pbs_request_id", "presence does not match qsub rc")
    return doc
