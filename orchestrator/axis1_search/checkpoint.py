"""Create-only checkpoints and the axis-1 request write-ahead log.

The WAL deliberately records ``issued`` before control enters the transport.  On
recovery an attempt whose last durable record is ``issued`` is therefore never
reclassified as not started: its externally visible outcome is unknowable.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import datetime, timezone
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Callable
from urllib.parse import urlsplit


SCHEMA_VERSION = "izanagi-axis1-search-checkpoint/v2"
ATTEMPT_STATES = (
    "prepared",
    "issued",
    "response_stored",
    "parsed",
    "terminal",
)
RESUME_ACTIONS = (
    "continue_cursor",
    "start_independent_pass",
    "restart_branch",
    "blocked_on_ruling",
    "not_applicable",
)

# A checkpoint describes what a new process may do next.  In particular,
# not_applicable is never legal for an unstarted branch.
STATE_RESUME_ACTIONS: dict[str, frozenset[str]] = {
    "not_started": frozenset({"restart_branch"}),
    "prepared": frozenset({"continue_cursor"}),
    "issued": frozenset({"restart_branch"}),
    "response_stored": frozenset({"continue_cursor"}),
    "parsed": frozenset({"continue_cursor"}),
    "paused_quota": frozenset({"continue_cursor"}),
    "pass_complete": frozenset({"start_independent_pass"}),
    "branch_complete": frozenset({"not_applicable"}),
    "outcome_unknown": frozenset({"restart_branch"}),
    "blocked_on_ruling": frozenset({"blocked_on_ruling"}),
    "superseded": frozenset({"restart_branch"}),
}

_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_HEX_40 = re.compile(r"^[0-9a-f]{40}$")
_CHECKPOINT_NAME = re.compile(r"^[0-9]{6}\.json$")
_EMPTY_BODY_SHA256 = hashlib.sha256(b"").hexdigest()
_ALLOWED_HOSTS = frozenset({"export.arxiv.org", "api.openalex.org", "dblp.org"})


class CheckpointError(ValueError):
    """A checkpoint or WAL record violates the registered contract."""


def _utc_now(clock: Callable[[], float]) -> str:
    return datetime.fromtimestamp(clock(), timezone.utc).isoformat().replace("+00:00", "Z")


def _read_all(fd: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _parse_wal_bytes(raw: bytes) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for lineno, line in enumerate(raw.splitlines(), 1):
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CheckpointError(f"malformed WAL line {lineno}: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise CheckpointError(f"WAL line {lineno} is not an object")
        records.append(value)
    return records


def _validate_wal_records(records: Iterable[Mapping[str, Any]]) -> None:
    latest: dict[tuple[str, int], str] = {}
    for record in records:
        request_id = record.get("request_id")
        attempt_number = record.get("attempt_number")
        state = record.get("state")
        if not isinstance(request_id, str) or not isinstance(attempt_number, int):
            raise CheckpointError("WAL identity is malformed")
        if state not in ATTEMPT_STATES:
            raise CheckpointError(f"WAL contains unknown state: {state!r}")
        key = (request_id, attempt_number)
        previous = latest.get(key)
        expected = "prepared" if previous is None else (
            ATTEMPT_STATES[ATTEMPT_STATES.index(previous) + 1]
            if previous != "terminal"
            else None
        )
        if state != expected:
            raise CheckpointError(
                f"illegal WAL transition for {request_id} attempt {attempt_number}: "
                f"expected {expected!r}, got {state!r}"
            )
        latest[key] = state


def append_attempt_state(
    wal_path: str | os.PathLike[str],
    request_id: str,
    attempt_number: int,
    state: str,
    *,
    at: str | None = None,
    payload: Mapping[str, Any] | None = None,
    clock: Callable[[], float] = __import__("time").time,
) -> dict[str, Any]:
    """Append one durable WAL transition, flushing and fsyncing before return."""

    if state not in ATTEMPT_STATES:
        raise CheckpointError(f"unknown attempt state: {state}")
    if not request_id or attempt_number < 1:
        raise CheckpointError("request_id and a positive attempt_number are required")

    path = Path(wal_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDWR | os.O_APPEND | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.lseek(fd, 0, os.SEEK_SET)
        records = _parse_wal_bytes(_read_all(fd))
        _validate_wal_records(records)
        previous = [
            item
            for item in records
            if item.get("request_id") == request_id
            and item.get("attempt_number") == attempt_number
        ]
        expected = ATTEMPT_STATES[0] if not previous else (
            ATTEMPT_STATES[ATTEMPT_STATES.index(previous[-1]["state"]) + 1]
            if previous[-1]["state"] != "terminal"
            else None
        )
        if state != expected:
            raise CheckpointError(
                f"illegal WAL transition for {request_id} attempt {attempt_number}: "
                f"expected {expected!r}, got {state!r}"
            )

        record: dict[str, Any] = {
            "request_id": request_id,
            "attempt_number": attempt_number,
            "state": state,
            "at": at or _utc_now(clock),
        }
        if payload:
            record["payload"] = deepcopy(dict(payload))
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        os.lseek(fd, 0, os.SEEK_END)
        view = memoryview(encoded)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
        return record
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _load_wal_source(
    source: str | os.PathLike[str] | Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if isinstance(source, (str, os.PathLike)):
        path = Path(source)
        if not path.exists():
            return []
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(path, flags)
        try:
            return _parse_wal_bytes(_read_all(fd))
        finally:
            os.close(fd)
    return [dict(item) for item in source]


def recover_attempts(
    source: str | os.PathLike[str] | Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Return one recovery disposition for each request attempt.

    ``prepared`` has not crossed the external-effect boundary and can be
    restarted.  ``issued`` has crossed it but has no stored response, so it is
    always recovered as ``outcome_unknown`` with ``restart_branch``.
    """

    records = _load_wal_source(source)
    _validate_wal_records(records)
    latest: dict[tuple[str, int], dict[str, Any]] = {}
    order: list[tuple[str, int]] = []
    for record in records:
        request_id = record.get("request_id")
        attempt_number = record.get("attempt_number")
        state = record.get("state")
        if not isinstance(request_id, str) or not isinstance(attempt_number, int):
            raise CheckpointError("WAL identity is malformed")
        if state not in ATTEMPT_STATES:
            raise CheckpointError(f"WAL contains unknown state: {state!r}")
        key = (request_id, attempt_number)
        if key not in latest:
            order.append(key)
        latest[key] = record

    recovered: list[dict[str, Any]] = []
    for key in order:
        record = deepcopy(latest[key])
        state = record["state"]
        if state == "prepared":
            record["state"] = "not_started"
            record["resume_action"] = "restart_branch"
        elif state == "issued":
            record["state"] = "outcome_unknown"
            record["resume_action"] = "restart_branch"
            record["reason_code"] = "issued_without_stored_response"
        else:
            record["resume_action"] = (
                "not_applicable" if state == "terminal" else "continue_cursor"
            )
        recovered.append(record)
    return tuple(recovered)


def _require_type(obj: Mapping[str, Any], key: str, expected: type) -> Any:
    value = obj.get(key)
    if not isinstance(value, expected):
        raise CheckpointError(f"{key} must be {expected.__name__}")
    return value


def _validate_sha(value: Any, field: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str) or not _HEX_64.fullmatch(value):
        raise CheckpointError(f"{field} must be a lowercase SHA-256")


def _validate_complete_request(value: Any, field: str) -> None:
    if not isinstance(value, Mapping):
        raise CheckpointError(f"{field} must be an object")
    required = {
        "request_id",
        "leaf_query_id",
        "logical_query_id",
        "index",
        "request_role",
        "executable",
        "method",
        "scheme",
        "host",
        "path",
        "query_parameters",
        "encoded_url",
        "headers",
        "empty_body_sha256",
        "timeout_s",
        "page_number",
        "position_in",
        "expected_interpreted_query",
        "target_run_id",
        "target_pass_number",
        "target_window_number",
        "parent_response_sha256",
        "catalog_template_sha256",
    }
    missing = sorted(required - set(value))
    if missing:
        raise CheckpointError(f"{field} lacks complete request fields: {missing}")
    if value["method"] != "GET" or value["scheme"] != "https":
        raise CheckpointError(f"{field} must be an HTTPS GET")
    if value["host"] not in _ALLOWED_HOSTS:
        raise CheckpointError(f"{field}.host is not registered")
    try:
        parsed_url = urlsplit(value["encoded_url"])
        port = parsed_url.port
    except (TypeError, ValueError) as exc:
        raise CheckpointError(f"{field}.encoded_url is malformed") from exc
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname != value["host"]
        or port not in (None, 443)
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.fragment
        or parsed_url.path != value["path"]
    ):
        raise CheckpointError(f"{field}.encoded_url contradicts the registered authority/path")
    if not isinstance(value["executable"], bool):
        raise CheckpointError(f"{field}.executable must be boolean")
    if value["empty_body_sha256"] != _EMPTY_BODY_SHA256:
        raise CheckpointError(f"{field}.empty_body_sha256 is not the empty-body digest")
    _validate_sha(value["catalog_template_sha256"], f"{field}.catalog_template_sha256")
    _validate_sha(
        value["parent_response_sha256"],
        f"{field}.parent_response_sha256",
        nullable=True,
    )
    if not isinstance(value["query_parameters"], (list, tuple)):
        raise CheckpointError(f"{field}.query_parameters must be ordered pairs")
    if not isinstance(value["headers"], (list, tuple)):
        raise CheckpointError(f"{field}.headers must be ordered pairs")
    for sequence_name in ("query_parameters", "headers"):
        for pair in value[sequence_name]:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2 or not all(
                isinstance(part, str) for part in pair
            ):
                raise CheckpointError(f"{field}.{sequence_name} contains a malformed pair")
    if not isinstance(value["target_pass_number"], int) or value["target_pass_number"] < 1:
        raise CheckpointError(f"{field}.target_pass_number must be positive")
    if not isinstance(value["target_window_number"], int) or value["target_window_number"] < 1:
        raise CheckpointError(f"{field}.target_window_number must be positive")
    if not isinstance(value["page_number"], int) or value["page_number"] < 0:
        raise CheckpointError(f"{field}.page_number must be nonnegative")
    if value["position_in"] is not None and not isinstance(value["position_in"], str):
        raise CheckpointError(f"{field}.position_in must be a string or null")


def validate_checkpoint(value: Mapping[str, Any]) -> None:
    """Perform the cross-field checks that JSON Schema cannot express cleanly."""

    required = {
        "schema_version",
        "checkpoint_id",
        "previous_checkpoint",
        "registration_epoch",
        "registration_commit",
        "catalog_path",
        "catalog_sha256",
        "bundle_root",
        "canonical_runner_argv",
        "query_id",
        "leaf_query_id",
        "index",
        "run_id",
        "pass_number",
        "window_number",
        "state",
        "resume_action",
        "requests",
        "cursor_state",
        "completed_ledger",
        "second_pass",
        "waiting_ruling_ids",
        "quota",
        "last_attempt",
    }
    missing = sorted(required - set(value))
    if missing:
        raise CheckpointError(f"checkpoint lacks required fields: {missing}")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise CheckpointError("unsupported checkpoint schema_version")
    checkpoint_id = _require_type(value, "checkpoint_id", str)
    if not re.fullmatch(r"[0-9]{6}", checkpoint_id):
        raise CheckpointError("checkpoint_id must be six decimal digits")
    commit = _require_type(value, "registration_commit", str)
    if not _HEX_40.fullmatch(commit):
        raise CheckpointError("registration_commit must be 40 lowercase hex digits")
    for field in ("catalog_sha256",):
        _validate_sha(value.get(field), field)
    for field in (
        "registration_epoch",
        "catalog_path",
        "bundle_root",
        "query_id",
        "leaf_query_id",
        "index",
        "run_id",
    ):
        _require_type(value, field, str)
    argv = value.get("canonical_runner_argv")
    if not isinstance(argv, (list, tuple)) or not argv or not all(
        isinstance(arg, str) and arg for arg in argv
    ):
        raise CheckpointError("canonical_runner_argv must be a nonempty string array")
    if argv.count("--checkpoint") != 1 or "--query-id" in argv:
        raise CheckpointError("canonical_runner_argv must encode the checkpoint resume action")
    checkpoint_argv_index = argv.index("--checkpoint")
    if checkpoint_argv_index + 1 >= len(argv):
        raise CheckpointError("canonical_runner_argv lacks the checkpoint path")

    state = value.get("state")
    action = value.get("resume_action")
    if state not in STATE_RESUME_ACTIONS:
        raise CheckpointError(f"unknown checkpoint state: {state!r}")
    if action not in RESUME_ACTIONS:
        raise CheckpointError(f"unknown resume_action: {action!r}")
    if action not in STATE_RESUME_ACTIONS[state]:
        raise CheckpointError(f"illegal state/resume_action pair: {state}/{action}")

    for field in ("pass_number", "window_number"):
        if not isinstance(value.get(field), int) or value[field] < 0:
            raise CheckpointError(f"{field} must be a nonnegative integer")
    if state in {"not_started", "superseded"}:
        if value["pass_number"] != 0 or value["window_number"] != 0:
            raise CheckpointError(f"{state} checkpoints must use pass/window zero")
    elif value["pass_number"] < 1 or value["window_number"] < 1:
        raise CheckpointError("started checkpoints require positive pass/window numbers")

    previous_checkpoint = value["previous_checkpoint"]
    if previous_checkpoint is not None:
        if not isinstance(previous_checkpoint, Mapping):
            raise CheckpointError("previous_checkpoint must be an object or null")
        if set(previous_checkpoint) != {"path", "bytes", "sha256"}:
            raise CheckpointError("previous_checkpoint must contain path, bytes, and sha256")
        if not isinstance(previous_checkpoint["path"], str) or not previous_checkpoint["path"]:
            raise CheckpointError("previous_checkpoint.path is required")
        if not isinstance(previous_checkpoint["bytes"], int) or previous_checkpoint["bytes"] < 0:
            raise CheckpointError("previous_checkpoint.bytes must be nonnegative")
        _validate_sha(previous_checkpoint["sha256"], "previous_checkpoint.sha256")

    requests = _require_type(value, "requests", dict)
    # D1183 requires both counterfactual next steps even when only one is selected.
    for request_role in ("continue_cursor", "start_independent_pass"):
        request_value = requests.get(request_role)
        _validate_complete_request(request_value, f"requests.{request_role}")
        if request_value["request_role"] != request_role:
            raise CheckpointError(f"requests.{request_role}.request_role is inconsistent")
    if action == "restart_branch":
        _validate_complete_request(requests.get("restart_branch"), "requests.restart_branch")
    if "restart_branch" in requests:
        _validate_complete_request(requests["restart_branch"], "requests.restart_branch")
        if requests["restart_branch"]["request_role"] != "restart_branch":
            raise CheckpointError("requests.restart_branch.request_role is inconsistent")
    executable_roles = {
        role
        for role, request_value in requests.items()
        if isinstance(request_value, Mapping) and request_value.get("executable") is True
    }
    expected_executable = {action} if action in {
        "continue_cursor",
        "start_independent_pass",
        "restart_branch",
    } else set()
    if executable_roles != expected_executable:
        raise CheckpointError(
            f"executable request roles {sorted(executable_roles)} do not match resume_action {action}"
        )

    cursor = _require_type(value, "cursor_state", dict)
    for field in (
        "previous_request_id",
        "parent_response_sha256",
        "position_in",
        "position_out",
        "page_number",
        "leaf_ordinal",
    ):
        if field not in cursor:
            raise CheckpointError(f"cursor_state.{field} is required")
    _validate_sha(cursor["parent_response_sha256"], "cursor_state.parent_response_sha256", nullable=True)

    ledger = _require_type(value, "completed_ledger", dict)
    if not isinstance(ledger.get("path"), str) or not ledger["path"].endswith(".json"):
        raise CheckpointError("completed_ledger.path must name a JSON object")
    if ledger.get("primary_key_kind") != "index_work_id":
        raise CheckpointError("completed_ledger.primary_key_kind must be index_work_id")
    _validate_sha(ledger.get("ledger_sha256"), "completed_ledger.ledger_sha256")
    _validate_sha(ledger.get("primary_key_digest"), "completed_ledger.primary_key_digest")
    if ledger["ledger_sha256"] == ledger["primary_key_digest"] and ledger.get("row_count", 0) > 0:
        # Equality is possible in theory, so it is not invalid.  Keeping the two
        # separately named fields is the actual contract; do not conflate them.
        pass
    for field in ("row_count", "distinct_count"):
        if not isinstance(ledger.get(field), int) or ledger[field] < 0:
            raise CheckpointError(f"completed_ledger.{field} must be nonnegative")

    if not isinstance(value.get("waiting_ruling_ids"), list) or not all(
        isinstance(item, str) and re.fullmatch(r"(?:D[0-9]+|T-[0-9]+)", item)
        for item in value["waiting_ruling_ids"]
    ):
        raise CheckpointError("waiting_ruling_ids must contain only D<number>/T-<number>")
    second_pass = _require_type(value, "second_pass", dict)
    for field in (
        "required",
        "state",
        "ledger_path",
        "primary_key_digest",
        "first_primary_key_digest",
        "matches_first",
        "accepted",
    ):
        if field not in second_pass:
            raise CheckpointError(f"second_pass.{field} is required")
    if not isinstance(second_pass["required"], bool):
        raise CheckpointError("second_pass.required must be boolean")
    _validate_sha(second_pass["primary_key_digest"], "second_pass.primary_key_digest", nullable=True)
    _validate_sha(
        second_pass["first_primary_key_digest"],
        "second_pass.first_primary_key_digest",
        nullable=True,
    )
    quota = _require_type(value, "quota", dict)
    for field in (
        "index",
        "observed_at_utc",
        "observed_at_jst",
        "limit",
        "remaining",
        "credits_per_request",
        "reset_seconds",
        "observed_request_id",
        "cost_usd",
        "header_evidence",
    ):
        if field not in quota:
            raise CheckpointError(f"quota.{field} is required")
    last_attempt = _require_type(value, "last_attempt", dict)
    for field in ("state", "request_id", "attempt_number", "failure", "raw_evidence_path"):
        if field not in last_attempt:
            raise CheckpointError(f"last_attempt.{field} is required")


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8") + b"\n"


def _next_checkpoint_id(directory: Path) -> str:
    maximum = 0
    for entry in directory.iterdir():
        if entry.is_file() and _CHECKPOINT_NAME.fullmatch(entry.name):
            maximum = max(maximum, int(entry.stem))
    if maximum >= 999999:
        raise CheckpointError("checkpoint sequence exhausted")
    return f"{maximum + 1:06d}"


def _publish_create_only(target: Path, payload: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = -1
        try:
            os.link(temporary, target, follow_symlinks=False)
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                raise FileExistsError(target) from exc
            raise
        temporary.unlink()
        dir_fd = os.open(target.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def write_checkpoint(
    destination: str | os.PathLike[str], checkpoint: Mapping[str, Any]
) -> Path:
    """Publish a checkpoint once using a six-digit create-only filename.

    ``destination`` may be a concrete ``000001.json`` path or a checkpoint
    directory.  Directory mode assigns the next sequence number and retries a
    concurrent collision without overwriting either writer.
    """

    destination_path = Path(destination)
    explicit = destination_path.suffix == ".json"
    directory = destination_path.parent if explicit else destination_path
    directory.mkdir(parents=True, exist_ok=True)

    if explicit and not _CHECKPOINT_NAME.fullmatch(destination_path.name):
        raise CheckpointError("checkpoint filename must be six digits plus .json")

    while True:
        value = deepcopy(dict(checkpoint))
        checkpoint_id = destination_path.stem if explicit else _next_checkpoint_id(directory)
        if "checkpoint_id" in value and value["checkpoint_id"] != checkpoint_id:
            raise CheckpointError("checkpoint_id does not match destination sequence")
        value["checkpoint_id"] = checkpoint_id
        target = destination_path if explicit else directory / f"{checkpoint_id}.json"
        argv = value.get("canonical_runner_argv")
        if isinstance(argv, (list, tuple)):
            value["canonical_runner_argv"] = [
                os.fspath(target) if item == "{checkpoint_path}" else item for item in argv
            ]
        validate_checkpoint(value)
        try:
            _publish_create_only(target, _canonical_bytes(value))
            return target
        except FileExistsError:
            if explicit:
                raise


def load_checkpoint(path: str | os.PathLike[str]) -> dict[str, Any]:
    checkpoint_path = Path(path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(checkpoint_path, flags)
    try:
        raw = _read_all(fd)
    finally:
        os.close(fd)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CheckpointError(f"invalid checkpoint JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise CheckpointError("checkpoint must contain a JSON object")
    validate_checkpoint(value)
    if _CHECKPOINT_NAME.fullmatch(checkpoint_path.name) and value["checkpoint_id"] != checkpoint_path.stem:
        raise CheckpointError("checkpoint_id does not match filename")
    return value


__all__ = [
    "ATTEMPT_STATES",
    "CheckpointError",
    "RESUME_ACTIONS",
    "SCHEMA_VERSION",
    "STATE_RESUME_ACTIONS",
    "append_attempt_state",
    "load_checkpoint",
    "recover_attempts",
    "validate_checkpoint",
    "write_checkpoint",
]
