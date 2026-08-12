"""Exact admission policy and append-only node-seconds ledger for T-810."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import fcntl
import os
from pathlib import Path
import re
from typing import Any, BinaryIO, Callable, Iterator, Mapping

from tools.pegasus import t810_harness_schema as schema


POLICY_SCHEMA = "t810-admission-policy/v1"
GENESIS_SCHEMA = "t810-budget-ledger-genesis/v1"
EVENT_SCHEMA = "t810-budget-ledger-event/v1"
RECEIPT_SCHEMA = "t810-budget-receipt/v1"
MAX_NODE_SECONDS = 2**63 - 1
ZERO_SHA256 = "0" * 64
RUN_KINDS = ("builder", "liveness", "main")
LIMITATIONS = frozenset({
    "authorization-witness-trust-root-absent",
    "guard-snapshot-to-release-race-not-eliminated",
    "shared-mount-repository-reachability-not-eliminated",
})
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class T810BudgetError(ValueError):
    """A fail-closed policy, request, or ledger violation."""


@dataclass(frozen=True)
class AdmissionPolicy:
    document: Mapping[str, Any]
    sha256: str


@dataclass(frozen=True)
class BudgetRequest:
    group_id: str
    run_kind: str
    attempt: int
    requested_attempts: int
    node_count: int
    launch_intent_sha256: str
    policy_sha256: str
    preregistration_max_attempts: int | None


@dataclass(frozen=True)
class BudgetReceipt:
    schema_version: str
    launch_intent_sha256: str
    policy_sha256: str
    estimates_sha256: str
    ledger_path: str
    ledger_sha256_before: str
    ledger_sha256_after: str
    reservation_id: str
    run_kind: str
    requested_attempts: int
    estimate_per_attempt_node_seconds: int
    required_node_seconds: int
    total_node_seconds: int
    counted_node_seconds: int
    remaining_node_seconds: int
    admitted: bool
    reason: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BudgetEvent:
    document: Mapping[str, Any]
    ledger_sha256_after: str


LockFactory = Callable[[Path], Any]


def _exact(value: Any, fields: set[str], name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise T810BudgetError(f"{name} must be an object")
    if set(value) != fields:
        raise T810BudgetError(f"{name} has unknown or missing fields")
    return dict(value)


def _str(value: Any, name: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value:
        raise T810BudgetError(f"{name} must be a non-empty string")
    return value


def _digest(value: Any, name: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise T810BudgetError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _int(
    value: Any, name: str, *, minimum: int = 0, nullable: bool = False,
) -> int | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise T810BudgetError(f"{name} must be an integer")
    if value < minimum or value > MAX_NODE_SECONDS:
        raise T810BudgetError(f"{name} is outside the admitted integer range")
    return value


def _validate_policy(value: Any) -> dict[str, Any]:
    top = _exact(value, {
        "schema_version", "parallel_guard", "qsub", "approved_hostnames",
        "budget", "limitations",
    }, "admission policy")
    if top["schema_version"] != POLICY_SCHEMA:
        raise T810BudgetError("admission policy schema mismatch")

    guard = _exact(top["parallel_guard"], {"a_series_identity"}, "parallel_guard")
    identity = _exact(guard["a_series_identity"], {
        "status", "field", "pilot_patterns", "main_patterns",
    }, "parallel_guard.a_series_identity")
    if identity["status"] not in {"unresolved", "resolved"} or identity["field"] != "Job_Name":
        raise T810BudgetError("parallel guard identity status or field is invalid")
    for name in ("pilot_patterns", "main_patterns"):
        values = identity[name]
        if (not isinstance(values, list) or any(not isinstance(item, str) for item in values)
                or len(values) != len(set(values))):
            raise T810BudgetError(f"{name} must be a unique string list")
        for pattern in values:
            if not pattern.startswith("^") or not pattern.endswith("$"):
                raise T810BudgetError("A-series identity patterns must be anchored")
            try:
                re.compile(pattern)
            except re.error as exc:
                raise T810BudgetError(f"invalid A-series identity pattern: {exc}") from exc
    if identity["status"] == "resolved" and not (
        identity["pilot_patterns"] or identity["main_patterns"]
    ):
        raise T810BudgetError("resolved A-series identity has no patterns")

    qsub = _exact(top["qsub"], {
        "status", "project", "queue", "walltime_by_run_kind",
    }, "qsub")
    if qsub["status"] not in {"unratified", "ratified"}:
        raise T810BudgetError("qsub status is invalid")
    walltimes = _exact(qsub["walltime_by_run_kind"], set(RUN_KINDS), "qsub walltime map")
    if qsub["status"] == "ratified":
        project = _str(qsub["project"], "qsub.project")
        queue = _str(qsub["queue"], "qsub.queue")
        if any(character.isspace() for character in project + queue):
            raise T810BudgetError("qsub project or queue contains whitespace")
        for kind, walltime in walltimes.items():
            if not isinstance(walltime, str) or re.fullmatch(r"[0-9]{2,}:[0-5][0-9]:[0-5][0-9]", walltime) is None:
                raise T810BudgetError(f"qsub walltime for {kind} is invalid")
            if walltime == "00:00:00":
                raise T810BudgetError(f"qsub walltime for {kind} must be positive")
    elif qsub["project"] is not None or qsub["queue"] is not None or any(item is not None for item in walltimes.values()):
        raise T810BudgetError("unratified qsub values must be null")

    hosts = _exact(top["approved_hostnames"], {"status", "hostnames"}, "approved_hostnames")
    if hosts["status"] not in {"unratified", "ratified"}:
        raise T810BudgetError("approved_hostnames status is invalid")
    if (not isinstance(hosts["hostnames"], list)
            or any(not isinstance(item, str) or not item for item in hosts["hostnames"])
            or len(hosts["hostnames"]) != len(set(hosts["hostnames"]))):
        raise T810BudgetError("approved_hostnames.hostnames is invalid")
    if hosts["status"] == "ratified" and not hosts["hostnames"]:
        raise T810BudgetError("ratified approved_hostnames must not be empty")
    if hosts["status"] == "unratified" and hosts["hostnames"]:
        raise T810BudgetError("unratified approved_hostnames must be empty")

    budget = _exact(top["budget"], {
        "status", "accounting_unit", "total_node_seconds", "estimates",
        "attempt_policy", "ledger", "admission",
    }, "budget")
    if budget["status"] not in {"unratified", "ratified"}:
        raise T810BudgetError("budget status is invalid")
    if budget["accounting_unit"] != "node-seconds":
        raise T810BudgetError("budget accounting unit is invalid")
    total = _int(
        budget["total_node_seconds"], "budget.total_node_seconds", minimum=1,
        nullable=budget["status"] == "unratified",
    )
    estimates = _exact(budget["estimates"], set(RUN_KINDS), "budget.estimates")
    for kind, raw in estimates.items():
        estimate = _exact(raw, {
            "walltime_seconds", "jobs_per_attempt", "node_seconds_per_attempt",
            "provisional_note",
        }, f"budget.estimates.{kind}")
        _str(estimate["provisional_note"], f"budget.estimates.{kind}.provisional_note")
        nullable = budget["status"] == "unratified"
        wall = _int(estimate["walltime_seconds"], f"{kind}.walltime_seconds", minimum=1, nullable=nullable)
        jobs = _int(estimate["jobs_per_attempt"], f"{kind}.jobs_per_attempt", minimum=1, nullable=nullable)
        amount = _int(estimate["node_seconds_per_attempt"], f"{kind}.node_seconds_per_attempt", minimum=1, nullable=nullable)
        if nullable:
            if any(item is not None for item in (wall, jobs, amount)):
                raise T810BudgetError("unratified estimate numbers must all be null")
        elif wall * jobs != amount or amount > MAX_NODE_SECONDS:
            raise T810BudgetError(f"{kind} estimate product mismatch or overflow")
    attempts = _exact(budget["attempt_policy"], {
        "builder_attempts", "liveness_max_attempts", "main_max_attempts_ref",
    }, "budget.attempt_policy")
    nullable = budget["status"] == "unratified"
    builder_attempts = _int(attempts["builder_attempts"], "builder_attempts", minimum=1, nullable=nullable)
    liveness_attempts = _int(attempts["liveness_max_attempts"], "liveness_max_attempts", minimum=1, nullable=nullable)
    ref = attempts["main_max_attempts_ref"]
    if nullable:
        if builder_attempts is not None or liveness_attempts is not None or ref is not None:
            raise T810BudgetError("unratified attempt policy values must be null")
    elif ref != "preregistration.terminal.retry.max_attempts":
        raise T810BudgetError("main_max_attempts_ref is not the frozen preregistration reference")
    elif builder_attempts != 1:
        raise T810BudgetError("builder_attempts must be exactly one")

    ledger = _exact(budget["ledger"], {
        "schema_version", "location", "lock_method", "counted_statuses", "genesis_sha256",
    }, "budget.ledger")
    if (ledger["schema_version"] != EVENT_SCHEMA or ledger["location"] != "repository-external"
            or ledger["lock_method"] != "flock"):
        raise T810BudgetError("ledger policy literal mismatch")
    if ledger["counted_statuses"] != ["reserved", "consumed"]:
        raise T810BudgetError("ledger counted_statuses must be exact")
    _digest(ledger["genesis_sha256"], "budget.ledger.genesis_sha256")
    admission = _exact(budget["admission"], {
        "formula", "integer_arithmetic", "max_node_seconds",
    }, "budget.admission")
    if (admission["formula"] != "0 < required <= remaining"
            or admission["integer_arithmetic"] != "exact"
            or admission["max_node_seconds"] != MAX_NODE_SECONDS):
        raise T810BudgetError("budget admission rule is not exact")
    limitations = top["limitations"]
    if not isinstance(limitations, list) or set(limitations) != LIMITATIONS or len(limitations) != len(LIMITATIONS):
        raise T810BudgetError("policy limitations are not exact")
    if budget["status"] == "ratified" and total is None:
        raise T810BudgetError("ratified budget lacks total_node_seconds")
    return top


def load_admission_policy(path: str | Path) -> AdmissionPolicy:
    """Load one exact policy, rejecting duplicate JSON keys at every depth."""
    try:
        raw = Path(path).read_bytes()
        value = schema.parse_json(raw)
    except (OSError, schema.T810SchemaError) as exc:
        raise T810BudgetError(f"cannot load admission policy: {exc}") from exc
    document = _validate_policy(value)
    return AdmissionPolicy(document=document, sha256=schema.canonical_sha256(document))


def admission_policy_from_mapping(value: Mapping[str, Any]) -> AdmissionPolicy:
    """Internal/test seam for an already parsed synthetic ratified policy."""
    document = _validate_policy(value)
    return AdmissionPolicy(document=document, sha256=schema.canonical_sha256(document))


def validate_genesis_record(value: Any) -> dict[str, Any]:
    record = _exact(value, {
        "schema_version", "sequence", "event_id", "status", "created_at", "previous_sha256",
    }, "ledger genesis")
    if (record["schema_version"] != GENESIS_SCHEMA or record["sequence"] != 0
            or isinstance(record["sequence"], bool) or record["status"] != "genesis"
            or record["previous_sha256"] is not None):
        raise T810BudgetError("ledger genesis literals are invalid")
    _str(record["event_id"], "ledger genesis event_id")
    _str(record["created_at"], "ledger genesis created_at")
    return record


_EVENT_FIELDS = {
    "schema_version", "sequence", "event_id", "reservation_id", "group_id",
    "run_kind", "attempt", "requested_attempts", "estimate_per_attempt_node_seconds",
    "amount_node_seconds", "status", "finalization_reason", "witness_sha256",
    "launch_intent_sha256", "created_at", "previous_sha256", "policy_sha256",
}


def _validate_event(value: Any) -> dict[str, Any]:
    event = _exact(value, _EVENT_FIELDS, "ledger event")
    if event["schema_version"] != EVENT_SCHEMA:
        raise T810BudgetError("ledger event schema mismatch")
    for name in ("sequence", "attempt", "requested_attempts", "estimate_per_attempt_node_seconds", "amount_node_seconds"):
        _int(event[name], f"ledger event {name}", minimum=1)
    for name in ("event_id", "reservation_id", "group_id", "created_at"):
        _str(event[name], f"ledger event {name}")
    if event["run_kind"] not in RUN_KINDS or event["status"] not in {"reserved", "consumed", "released"}:
        raise T810BudgetError("ledger event literal is invalid")
    for name in ("launch_intent_sha256", "previous_sha256", "policy_sha256"):
        _digest(event[name], f"ledger event {name}")
    if event["estimate_per_attempt_node_seconds"] * event["requested_attempts"] != event["amount_node_seconds"]:
        raise T810BudgetError("ledger event amount does not match its estimate")
    if event["amount_node_seconds"] > MAX_NODE_SECONDS:
        raise T810BudgetError("ledger event amount overflow")
    if event["status"] == "reserved":
        if event["finalization_reason"] is not None or event["witness_sha256"] is not None:
            raise T810BudgetError("reserved event carries finalization evidence")
    else:
        _str(event["finalization_reason"], "ledger event finalization_reason")
        _digest(event["witness_sha256"], "ledger event witness_sha256")
    return event


@dataclass(frozen=True)
class _LedgerState:
    raw: bytes
    records: tuple[Mapping[str, Any], ...]
    latest: Mapping[str, Mapping[str, Any]]
    counted: int


def _parse_ledger(raw: bytes, policy: AdmissionPolicy) -> _LedgerState:
    if not raw or not raw.endswith(b"\n"):
        raise T810BudgetError("ledger is empty or has a partial final line")
    records: list[Mapping[str, Any]] = []
    lines = raw.splitlines()
    for index, line in enumerate(lines):
        try:
            parsed = schema.parse_json(line)
        except schema.T810SchemaError as exc:
            raise T810BudgetError(f"ledger line {index + 1} is invalid: {exc}") from exc
        record = validate_genesis_record(parsed) if index == 0 else _validate_event(parsed)
        if line != schema.canonical_json_bytes(record):
            raise T810BudgetError(f"ledger line {index + 1} is not canonical JSON")
        records.append(record)
    genesis_sha = schema.canonical_sha256(records[0])
    expected_genesis = policy.document["budget"]["ledger"]["genesis_sha256"]
    if genesis_sha != expected_genesis:
        raise T810BudgetError("ledger genesis digest does not match policy")
    previous = genesis_sha
    latest: dict[str, Mapping[str, Any]] = {}
    keys: set[tuple[str, str, int]] = set()
    event_ids: set[str] = set()
    for sequence, event in enumerate(records[1:], 1):
        if event["sequence"] != sequence:
            raise T810BudgetError("ledger sequence gap")
        if event["previous_sha256"] != previous:
            raise T810BudgetError("ledger previous_sha256 chain mismatch")
        if event["policy_sha256"] != policy.sha256:
            raise T810BudgetError("ledger event policy digest mismatch")
        if event["event_id"] in event_ids:
            raise T810BudgetError("duplicate ledger event_id")
        event_ids.add(event["event_id"])
        reservation_id = event["reservation_id"]
        prior = latest.get(reservation_id)
        if event["status"] == "reserved":
            key = (event["group_id"], event["run_kind"], event["attempt"])
            if prior is not None or key in keys:
                raise T810BudgetError("duplicate budget reservation")
            keys.add(key)
        else:
            if prior is None or prior["status"] != "reserved":
                raise T810BudgetError("finalize replay or invalid reservation transition")
            immutable = {
                "reservation_id", "group_id", "run_kind", "attempt", "requested_attempts",
                "estimate_per_attempt_node_seconds", "amount_node_seconds", "launch_intent_sha256",
            }
            if any(event[name] != prior[name] for name in immutable):
                raise T810BudgetError("finalize event changes reservation identity")
        latest[reservation_id] = event
        previous = schema.canonical_sha256(event)
    counted = sum(
        event["amount_node_seconds"] for event in latest.values()
        if event["status"] in policy.document["budget"]["ledger"]["counted_statuses"]
    )
    if counted > MAX_NODE_SECONDS:
        raise T810BudgetError("ledger counted amount overflow")
    total = policy.document["budget"]["total_node_seconds"]
    if total is not None and counted > total:
        raise T810BudgetError("ledger counted amount exceeds policy total")
    return _LedgerState(raw, tuple(records), latest, counted)


@contextmanager
def _flocked(path: Path) -> Iterator[BinaryIO]:
    try:
        handle = path.open("r+b")
    except OSError as exc:
        raise T810BudgetError(f"cannot open existing budget ledger: {exc}") from exc
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield handle
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def _external_ledger_path(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise T810BudgetError("ledger path must be absolute")
    repository = Path(__file__).resolve().parents[2]
    resolved = path.resolve(strict=False)
    if resolved == repository or repository in resolved.parents:
        raise T810BudgetError("ledger path must be repository-external")
    return resolved


def _request(value: BudgetRequest | Mapping[str, Any]) -> BudgetRequest:
    if isinstance(value, BudgetRequest):
        request = value
    else:
        raw = _exact(value, {
            "group_id", "run_kind", "attempt", "requested_attempts", "node_count",
            "launch_intent_sha256", "policy_sha256", "preregistration_max_attempts",
        }, "budget request")
        request = BudgetRequest(**raw)
    _str(request.group_id, "request.group_id")
    if request.run_kind not in RUN_KINDS:
        raise T810BudgetError("request.run_kind is invalid")
    _int(request.attempt, "request.attempt", minimum=1)
    _int(request.requested_attempts, "request.requested_attempts", minimum=1)
    _int(request.node_count, "request.node_count", minimum=1)
    _digest(request.launch_intent_sha256, "request.launch_intent_sha256")
    _digest(request.policy_sha256, "request.policy_sha256")
    if request.preregistration_max_attempts is not None:
        _int(request.preregistration_max_attempts, "request.preregistration_max_attempts", minimum=1)
    return request


def _read_locked(handle: BinaryIO, policy: AdmissionPolicy) -> _LedgerState:
    handle.seek(0)
    return _parse_ledger(handle.read(), policy)


def _append_locked(handle: BinaryIO, event: Mapping[str, Any]) -> bytes:
    raw = schema.canonical_json_bytes(event) + b"\n"
    handle.seek(0, os.SEEK_END)
    if handle.write(raw) != len(raw):
        raise T810BudgetError("short ledger append")
    handle.flush()
    os.fsync(handle.fileno())
    handle.seek(0)
    return handle.read()


def _denied_receipt(
    request: BudgetRequest, policy: AdmissionPolicy, ledger_path: Path,
    reason: str, created_at: str,
) -> BudgetReceipt:
    estimate = policy.document["budget"]["estimates"][request.run_kind]["node_seconds_per_attempt"]
    estimate = 0 if estimate is None else estimate
    total = policy.document["budget"]["total_node_seconds"] or 0
    reservation_id = schema.canonical_sha256({
        "group_id": request.group_id, "run_kind": request.run_kind,
        "attempt": request.attempt, "launch_intent_sha256": request.launch_intent_sha256,
    })
    return BudgetReceipt(
        RECEIPT_SCHEMA, request.launch_intent_sha256, policy.sha256,
        schema.canonical_sha256(policy.document["budget"]["estimates"]),
        str(ledger_path), ZERO_SHA256, ZERO_SHA256, reservation_id,
        request.run_kind, request.requested_attempts, estimate, 0, total, 0, total,
        False, reason, created_at,
    )


def reserve_budget(
    request: BudgetRequest | Mapping[str, Any], *, policy: AdmissionPolicy,
    ledger_path: str | Path, clock: Callable[[], str],
    lock_factory: LockFactory | None = None,
) -> BudgetReceipt:
    """Inside one lock: read, validate, check ``0 < required <= remaining``, append."""
    req = _request(request)
    path = _external_ledger_path(ledger_path)
    created_at = _str(clock(), "clock result")
    if policy.document["budget"]["status"] != "ratified":
        return _denied_receipt(req, policy, path, "budget-unratified", created_at)
    if req.policy_sha256 != policy.sha256:
        return _denied_receipt(req, policy, path, "policy-digest-mismatch", created_at)
    estimate = policy.document["budget"]["estimates"][req.run_kind]
    if estimate["jobs_per_attempt"] != req.node_count:
        return _denied_receipt(req, policy, path, "jobs-per-attempt-mismatch", created_at)
    attempts = policy.document["budget"]["attempt_policy"]
    # One reservation is one concrete attempt.  A caller reserves every allowed
    # retry slot before scheduler effects, so an unused retry can be released
    # without releasing the consumed first attempt.
    allowed = req.requested_attempts == 1 and (
        req.attempt <= attempts["builder_attempts"] if req.run_kind == "builder"
        else req.attempt <= attempts["liveness_max_attempts"] if req.run_kind == "liveness"
        else req.preregistration_max_attempts == 2 and req.attempt <= req.preregistration_max_attempts
    )
    if not allowed:
        return _denied_receipt(req, policy, path, "attempt-policy-mismatch", created_at)
    required = estimate["node_seconds_per_attempt"] * req.requested_attempts
    if required > MAX_NODE_SECONDS:
        raise T810BudgetError("required node-seconds overflow")
    reservation_id = schema.canonical_sha256({
        "group_id": req.group_id, "run_kind": req.run_kind, "attempt": req.attempt,
        "launch_intent_sha256": req.launch_intent_sha256,
    })
    locker = lock_factory or _flocked
    with locker(path) as handle:
        state = _read_locked(handle, policy)
        before = schema.sha256_bytes(state.raw)
        total = policy.document["budget"]["total_node_seconds"]
        remaining = total - state.counted
        key = (req.group_id, req.run_kind, req.attempt)
        duplicate = any(
            (event["group_id"], event["run_kind"], event["attempt"]) == key
            for event in state.latest.values()
        )
        reason = "duplicate-reservation" if duplicate else "insufficient-budget"
        if duplicate or not (0 < required <= remaining):
            return BudgetReceipt(
                RECEIPT_SCHEMA, req.launch_intent_sha256, policy.sha256,
                schema.canonical_sha256(policy.document["budget"]["estimates"]),
                str(path), before, before, reservation_id, req.run_kind,
                req.requested_attempts, estimate["node_seconds_per_attempt"], required,
                total, state.counted, remaining, False, reason, created_at,
            )
        previous = schema.canonical_sha256(state.records[-1])
        event = _validate_event({
            "schema_version": EVENT_SCHEMA, "sequence": len(state.records),
            "event_id": schema.canonical_sha256({
                "reservation_id": reservation_id, "sequence": len(state.records),
                "created_at": created_at, "previous_sha256": previous,
            }),
            "reservation_id": reservation_id, "group_id": req.group_id,
            "run_kind": req.run_kind, "attempt": req.attempt,
            "requested_attempts": req.requested_attempts,
            "estimate_per_attempt_node_seconds": estimate["node_seconds_per_attempt"],
            "amount_node_seconds": required, "status": "reserved",
            "finalization_reason": None, "witness_sha256": None,
            "launch_intent_sha256": req.launch_intent_sha256,
            "created_at": created_at, "previous_sha256": previous,
            "policy_sha256": policy.sha256,
        })
        after_raw = _append_locked(handle, event)
        after = schema.sha256_bytes(after_raw)
        return BudgetReceipt(
            RECEIPT_SCHEMA, req.launch_intent_sha256, policy.sha256,
            schema.canonical_sha256(policy.document["budget"]["estimates"]),
            str(path), before, after, reservation_id, req.run_kind,
            req.requested_attempts, estimate["node_seconds_per_attempt"], required,
            total, state.counted, remaining - required, True, "admitted", created_at,
        )


_FINALIZATION = {
    "scheduler-reachability-unknown": "consumed",
    "submission-accepted": "consumed",
    "pre-submission-aborted": "released",
    "qdel-confirmed-before-start": "released",
    "unused-retry": "released",
}


def finalize_budget(
    reservation_id: str, *, policy: AdmissionPolicy, ledger_path: str | Path,
    outcome: str, witness_sha256: str, clock: Callable[[], str],
    lock_factory: LockFactory | None = None,
) -> BudgetEvent:
    """Finalize one reservation exactly once using the frozen conservative table."""
    _str(reservation_id, "reservation_id")
    if outcome not in _FINALIZATION:
        raise T810BudgetError("unknown budget finalization outcome")
    _digest(witness_sha256, "witness_sha256")
    if policy.document["budget"]["status"] != "ratified":
        raise T810BudgetError("budget is unratified")
    path = _external_ledger_path(ledger_path)
    created_at = _str(clock(), "clock result")
    locker = lock_factory or _flocked
    with locker(path) as handle:
        state = _read_locked(handle, policy)
        reserved = state.latest.get(reservation_id)
        if reserved is None or reserved["status"] != "reserved":
            raise T810BudgetError("finalize replay or unknown reservation")
        if outcome == "unused-retry" and not (
            reserved["run_kind"] == "main" and reserved["attempt"] == 2
        ):
            raise T810BudgetError("unused-retry requires the reserved main retry slot")
        previous = schema.canonical_sha256(state.records[-1])
        event = dict(reserved)
        event.update({
            "sequence": len(state.records),
            "event_id": schema.canonical_sha256({
                "reservation_id": reservation_id, "outcome": outcome,
                "sequence": len(state.records), "created_at": created_at,
                "previous_sha256": previous,
            }),
            "status": _FINALIZATION[outcome], "finalization_reason": outcome,
            "witness_sha256": witness_sha256, "created_at": created_at,
            "previous_sha256": previous,
        })
        validated = _validate_event(event)
        after = schema.sha256_bytes(_append_locked(handle, validated))
        return BudgetEvent(validated, after)
