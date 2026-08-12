"""Fail-closed T-810/T-139 parallel-run guard for Pegasus PBS snapshots."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
import subprocess
from typing import Any, Callable, Mapping, Sequence

from tools.pegasus import t810_harness_schema as schema


GUARD_RECEIPT_SCHEMA = "t810-guard-receipt/v1"
KNOWN_STATES = {"Q": "QUE", "H": "HLD", "R": "RUN"}
PHASES = frozenset({"pre-submission", "pre-release"})
LIMITATIONS = (
    "authorization-witness-trust-root-absent",
    "shared-mount-repository-reachability-not-eliminated",
    "snapshot-to-release-race-not-eliminated",
)
_CRITICAL = ("Job_Owner", "job_state", "Job_Name", "queue", "exec_host")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class T810GuardError(ValueError):
    """A fail-closed snapshot, policy, identity, or scheduler violation."""

    def __init__(self, reason_code: str, detail: str):
        super().__init__(f"{reason_code}: {detail}")
        self.reason_code = reason_code


@dataclass(frozen=True)
class SchedulerJob:
    request_id: str
    owner: str
    state: str
    raw_state: str
    job_name: str
    queue: str
    exec_host: str
    execution_hosts: tuple[str, ...]


@dataclass(frozen=True)
class QueueStatus:
    queue: str
    enabled: bool
    active: bool
    queued: int
    running: int
    raw_line: str

    @property
    def available(self) -> bool:
        return self.enabled and self.active


@dataclass(frozen=True)
class GuardDecision:
    schema_version: str
    launch_intent_sha256: str
    phase: str
    policy_sha256: str
    snapshot_sha256: str
    a_series_identity_status: str
    a_series_jobs: tuple[str, ...]
    co_location_conflicts: tuple[Mapping[str, Any], ...]
    decision: str
    reason_codes: tuple[str, ...]
    b_request_ids: tuple[str, ...]
    withdrawal_actions: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        for field in (
            "a_series_jobs", "co_location_conflicts", "reason_codes",
            "b_request_ids", "withdrawal_actions", "limitations",
        ):
            value[field] = list(value[field])
        return value


def _fail(code: str, detail: str) -> None:
    raise T810GuardError(code, detail)


def _digest(value: Any, name: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        _fail("invalid-input", f"{name} is not a lowercase SHA-256 digest")
    return value


def _nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        _fail("invalid-input", f"{name} is not a non-empty string")
    return value


def _execution_hosts(value: str) -> tuple[str, ...]:
    if value in {"--", "-", "(none)"}:
        return ()
    hosts: list[str] = []
    for chunk in value.split("+"):
        host = chunk.strip().partition("/")[0]
        if not host:
            _fail("invalid-snapshot", "exec_host contains an empty host")
        if host not in hosts:
            hosts.append(host)
    return tuple(hosts)


def parse_qstat_jobs(
    text: str, *, expected_owner: str,
    expected_request_ids: Sequence[str] | None = None,
) -> tuple[SchedulerJob, ...]:
    """Parse one or more ``qstat -f`` blocks with exact critical fields."""
    if not isinstance(text, str):
        _fail("invalid-snapshot", "qstat stdout is not text")
    owner_expected = _nonempty(expected_owner, "expected_owner")
    blocks: list[tuple[str, list[str]]] = []
    current_id: str | None = None
    current_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Job Id:"):
            if current_id is not None:
                blocks.append((current_id, current_lines))
            current_id = stripped.partition(":")[2].strip()
            if not current_id:
                _fail("invalid-snapshot", "empty Job Id")
            current_lines = []
        elif current_id is not None:
            current_lines.append(line)
        elif stripped:
            _fail("invalid-snapshot", "content precedes the first Job Id")
    if current_id is not None:
        blocks.append((current_id, current_lines))
    if not blocks:
        _fail("invalid-snapshot", "no Job Id block")

    jobs: list[SchedulerJob] = []
    seen_ids: set[str] = set()
    for request_id, lines in blocks:
        if request_id in seen_ids:
            _fail("duplicate-critical-field", f"duplicate Job Id {request_id!r}")
        seen_ids.add(request_id)
        occurrences: dict[str, list[str]] = {field: [] for field in _CRITICAL}
        last_field: str | None = None
        for line in lines:
            stripped = line.strip()
            matched = False
            for field in _CRITICAL:
                prefix = field + " ="
                if stripped.startswith(prefix):
                    occurrences[field].append(stripped.partition("=")[2].strip())
                    last_field = field
                    matched = True
                    break
            if matched:
                continue
            if "=" in stripped:
                last_field = None
                continue
            # PBS wraps long values on an indented continuation line.
            if line[:1].isspace() and last_field is not None and stripped:
                occurrences[last_field][-1] += stripped
            else:
                last_field = None
        for field, values in occurrences.items():
            if len(values) != 1:
                code = "missing-critical-field" if not values else "duplicate-critical-field"
                _fail(code, f"{request_id}: {field} occurs {len(values)} times")
            if not values[0]:
                _fail("missing-critical-field", f"{request_id}: {field} is empty")
        raw_owner = occurrences["Job_Owner"][0]
        owner = raw_owner.partition("@")[0]
        if owner != owner_expected:
            _fail("owner-mismatch", f"{request_id}: expected {owner_expected!r}, got {owner!r}")
        raw_state = occurrences["job_state"][0]
        jobs.append(SchedulerJob(
            request_id=request_id,
            owner=owner,
            state=KNOWN_STATES.get(raw_state, "UNKNOWN"),
            raw_state=raw_state,
            job_name=occurrences["Job_Name"][0],
            queue=occurrences["queue"][0],
            exec_host=occurrences["exec_host"][0],
            execution_hosts=_execution_hosts(occurrences["exec_host"][0]),
        ))

    if expected_request_ids is not None:
        expected = list(expected_request_ids)
        if len(expected) != len(set(expected)) or [job.request_id for job in jobs] != expected:
            _fail("request-id-mismatch", "qstat Job Id sequence differs from requested IDs")
    return tuple(jobs)


def parse_qstat_f_transcripts(
    transcripts: Sequence[Mapping[str, Any]], *, expected_owner: str,
) -> tuple[SchedulerJob, ...]:
    """Validate transcript envelopes and parse every requested job exactly once."""
    if not isinstance(transcripts, Sequence) or isinstance(transcripts, (str, bytes)):
        _fail("invalid-snapshot", "qstat transcript set is not a sequence")
    jobs: list[SchedulerJob] = []
    request_ids: set[str] = set()
    for index, raw in enumerate(transcripts):
        try:
            transcript = schema.validate_qstat_f_transcript(raw)
        except schema.T810SchemaError as exc:
            _fail("invalid-transcript", f"transcript {index}: {exc}")
        request_id = transcript["request_id"]
        if request_id in request_ids:
            _fail("request-id-mismatch", f"duplicate transcript for {request_id!r}")
        request_ids.add(request_id)
        if transcript["rc"] != 0 or transcript["stderr"]:
            _fail("qstat-failed", f"qstat -f failed for {request_id!r}")
        parsed = parse_qstat_jobs(
            transcript["stdout"], expected_owner=expected_owner,
            expected_request_ids=[request_id],
        )
        if len(parsed) != 1:
            _fail("request-id-mismatch", f"{request_id!r} returned multiple blocks")
        jobs.extend(parsed)
    return tuple(jobs)


def parse_qstat_queue(
    transcript: Mapping[str, Any], *, expected_queue: str,
) -> QueueStatus:
    """Strictly parse the separate ``qstat -Q`` execution-queue transcript."""
    try:
        doc = schema.validate_qstat_q_transcript(transcript)
    except schema.T810SchemaError as exc:
        _fail("invalid-transcript", str(exc))
    target = _nonempty(expected_queue, "expected_queue")
    if doc["rc"] != 0 or doc["stderr"]:
        _fail("qstat-failed", "qstat -Q did not succeed cleanly")
    in_execution = False
    table_count = 0
    columns: dict[str, int] | None = None
    width = 0
    matches: list[QueueStatus] = []
    invalid = False
    for line in doc["stdout"].splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_execution = stripped.startswith("[EXECUTION QUEUE]")
            if in_execution:
                table_count += 1
                columns = None
            continue
        if not in_execution or not stripped:
            continue
        fields = stripped.split()
        if columns is None:
            if fields and fields[0] == "QueueName":
                required = ("QueueName", "ENA", "STS", "QUE", "RUN")
                if any(fields.count(name) != 1 for name in required):
                    invalid = True
                    continue
                columns = {name: fields.index(name) for name in required}
                width = len(fields)
            continue
        if fields[0] in {"<TOTAL>", "QueueName"} or set(stripped) <= {"-", " "}:
            invalid |= fields[0] == "QueueName"
            continue
        if len(fields) != width:
            invalid = True
            continue
        if fields[columns["QueueName"]] != target:
            continue
        ena, sts = fields[columns["ENA"]], fields[columns["STS"]]
        if ena not in {"ENA", "DIS"} or sts not in {"ACT", "INA"}:
            invalid = True
            continue
        try:
            queued, running = int(fields[columns["QUE"]]), int(fields[columns["RUN"]])
        except ValueError:
            invalid = True
            continue
        if queued < 0 or running < 0:
            invalid = True
            continue
        matches.append(QueueStatus(target, ena == "ENA", sts == "ACT", queued, running, line))
    if invalid or table_count != 1 or columns is None or len(matches) != 1:
        _fail("invalid-queue-snapshot", "qstat -Q execution queue is ambiguous")
    return matches[0]


def _guard_identity(policy: Mapping[str, Any]) -> tuple[str, tuple[re.Pattern[str], ...]]:
    section = policy.get("parallel_guard") if "parallel_guard" in policy else policy
    if not isinstance(section, Mapping) or set(section) != {"a_series_identity"}:
        _fail("invalid-policy", "parallel_guard fields are not exact")
    identity = section["a_series_identity"]
    fields = {"status", "field", "pilot_patterns", "main_patterns"}
    if not isinstance(identity, Mapping) or set(identity) != fields:
        _fail("invalid-policy", "a_series_identity fields are not exact")
    status = identity["status"]
    if status not in {"unresolved", "resolved"}:
        _fail("invalid-policy", "unknown a_series_identity status")
    if identity["field"] != "Job_Name":
        _fail("invalid-policy", "only Job_Name identity is supported")
    patterns: list[re.Pattern[str]] = []
    for kind in ("pilot_patterns", "main_patterns"):
        values = identity[kind]
        if not isinstance(values, list) or len(values) != len(set(values)):
            _fail("invalid-policy", f"{kind} is not a unique list")
        for raw in values:
            if not isinstance(raw, str) or not raw.startswith("^") or not raw.endswith("$"):
                _fail("invalid-policy", "A-series patterns must be explicitly anchored")
            try:
                patterns.append(re.compile(raw))
            except re.error as exc:
                _fail("invalid-policy", f"invalid A-series pattern: {exc}")
    if status == "resolved" and not patterns:
        _fail("invalid-policy", "resolved identity requires at least one pattern")
    return status, tuple(patterns)


def _manifest_identities(value: Sequence[Mapping[str, Any]]) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for index, item in enumerate(value):
        fields = {"pbs_request_id", "owner", "job_name"}
        if not isinstance(item, Mapping) or set(item) != fields:
            _fail("invalid-input", f"B manifest identity {index} fields are not exact")
        request_id = _nonempty(item["pbs_request_id"], "pbs_request_id")
        if request_id in result:
            _fail("invalid-input", "duplicate B PBS request ID")
        result[request_id] = (
            _nonempty(item["owner"], "owner"), _nonempty(item["job_name"], "job_name")
        )
    return result


def evaluate_parallel_guard(
    transcripts: Sequence[Mapping[str, Any]], *, policy: Mapping[str, Any],
    phase: str, launch_intent_sha256: str, expected_owner: str,
    b_manifest_jobs: Sequence[Mapping[str, Any]] = (), created_at: str,
) -> GuardDecision:
    """Evaluate either fresh guard phase without performing scheduler effects."""
    if phase not in PHASES:
        _fail("invalid-input", "unknown guard phase")
    _digest(launch_intent_sha256, "launch_intent_sha256")
    _nonempty(created_at, "created_at")
    policy_sha256 = schema.canonical_sha256(dict(policy))
    snapshot_sha256 = schema.canonical_sha256(list(transcripts))
    reasons: list[str] = []
    a_ids: list[str] = []
    conflicts: list[Mapping[str, Any]] = []
    b_ids: tuple[str, ...] = ()
    try:
        status, patterns = _guard_identity(policy)
        identities = _manifest_identities(b_manifest_jobs)
        b_ids = tuple(identities)
        jobs = parse_qstat_f_transcripts(transcripts, expected_owner=expected_owner)
        if status == "unresolved":
            reasons.append("priority-identity-unresolved")
        for job in jobs:
            if job.state == "UNKNOWN":
                reasons.append("unknown-job-state")
            if any(pattern.fullmatch(job.job_name) for pattern in patterns):
                a_ids.append(job.request_id)
        if a_ids:
            reasons.append("a-series-active")
        by_id = {job.request_id: job for job in jobs}
        if phase == "pre-release":
            for request_id, identity in identities.items():
                job = by_id.get(request_id)
                if job is None or (job.owner, job.job_name) != identity:
                    reasons.append("b-identity-mismatch")
            host_jobs: dict[str, list[str]] = {}
            for job in jobs:
                for host in job.execution_hosts:
                    host_jobs.setdefault(host, []).append(job.request_id)
            for host, request_ids in sorted(host_jobs.items()):
                if len(request_ids) > 1 and any(item in identities for item in request_ids):
                    conflicts.append({"hostname": host, "pbs_request_ids": sorted(request_ids)})
            if conflicts:
                reasons.append("co-location-conflict")
    except T810GuardError as exc:
        status = "invalid"
        reasons.append(exc.reason_code)
    reasons = list(dict.fromkeys(reasons))
    return GuardDecision(
        GUARD_RECEIPT_SCHEMA, launch_intent_sha256, phase, policy_sha256,
        snapshot_sha256, status, tuple(sorted(a_ids)), tuple(conflicts),
        "allow" if not reasons else "deny", tuple(reasons), b_ids, (),
        LIMITATIONS, created_at,
    )


def _verify_authorization(
    witness: Mapping[str, Any] | None, *, approval_id: str,
    preregistration_sha256: str, policy_sha256: str, run_kind: str,
) -> Mapping[str, Any]:
    if witness is None:
        _fail("launch-authorization-required", "qdel requires an authorization witness")
    try:
        doc = schema.validate_launch_authorization(witness)
    except schema.T810SchemaError as exc:
        _fail("launch-authorization-invalid", str(exc))
    expected = {
        "approval_id": approval_id,
        "preregistration_sha256": preregistration_sha256,
        "policy_sha256": policy_sha256,
    }
    for field, value in expected.items():
        if doc[field] != value:
            _fail("launch-authorization-mismatch", f"{field} mismatch")
    if run_kind not in doc["run_kinds"]:
        _fail("launch-authorization-mismatch", "run_kind is not authorized")
    return doc


def withdraw_b_group(
    decision: GuardDecision, *, fresh_transcripts: Sequence[Mapping[str, Any]],
    b_manifest_jobs: Sequence[Mapping[str, Any]], expected_owner: str,
    authorization_witness: Mapping[str, Any] | None, approval_id: str,
    preregistration_sha256: str, run_kind: str,
    publish_cancel: Callable[[], None], scheduler_run: Callable[[Sequence[str]], Any],
    created_at: str,
) -> GuardDecision:
    """Publish cancel, then qdel only exact QUE/HLD B identities via the seam."""
    if decision.phase != "pre-release":
        _fail("invalid-input", "B withdrawal is only valid in the pre-release phase")
    identities = _manifest_identities(b_manifest_jobs)
    publish_cancel()
    # First effect-boundary check occurs after the cancel marker and before any qdel.
    try:
        _verify_authorization(
            authorization_witness, approval_id=approval_id,
            preregistration_sha256=preregistration_sha256,
            policy_sha256=decision.policy_sha256, run_kind=run_kind,
        )
        jobs = parse_qstat_f_transcripts(fresh_transcripts, expected_owner=expected_owner)
    except T810GuardError as exc:
        withdrawal_reason = (
            "qdel-identity-mismatch"
            if exc.reason_code in {
                "owner-mismatch", "request-id-mismatch", "missing-critical-field",
                "duplicate-critical-field",
            }
            else exc.reason_code
        )
        return GuardDecision(
            decision.schema_version, decision.launch_intent_sha256, decision.phase,
            decision.policy_sha256, schema.canonical_sha256(list(fresh_transcripts)),
            decision.a_series_identity_status, decision.a_series_jobs,
            decision.co_location_conflicts, "deny",
            tuple(dict.fromkeys(decision.reason_codes + (exc.reason_code, withdrawal_reason))),
            tuple(identities), (), LIMITATIONS, created_at,
        )
    by_id = {job.request_id: job for job in jobs}
    actions: list[Mapping[str, Any]] = []
    reasons = list(decision.reason_codes)
    all_deleted = True
    for request_id, (owner, job_name) in identities.items():
        job = by_id.get(request_id)
        match = bool(job and job.owner == owner and job.job_name == job_name
                     and job.state in {"QUE", "HLD"})
        argv = ["qdel", request_id] if match else []
        rc: int | None = None
        if match:
            # Revalidate at every scheduler-effect entry, not merely once per batch.
            _verify_authorization(
                authorization_witness, approval_id=approval_id,
                preregistration_sha256=preregistration_sha256,
                policy_sha256=decision.policy_sha256, run_kind=run_kind,
            )
            result = scheduler_run(argv)
            if not isinstance(result, subprocess.CompletedProcess):
                _fail("scheduler-result-invalid", "qdel seam returned the wrong type")
            rc = result.returncode
            if rc != 0:
                reasons.append("qdel-failed")
                all_deleted = False
        else:
            reasons.append("qdel-identity-mismatch")
            all_deleted = False
        actions.append({
            "pbs_request_id": request_id,
            "job_name": job_name,
            "state": None if job is None else job.state,
            "identity_match": match,
            "qdel_argv": argv,
            "qdel_rc": rc,
        })
    return GuardDecision(
        decision.schema_version, decision.launch_intent_sha256, decision.phase,
        decision.policy_sha256, schema.canonical_sha256(list(fresh_transcripts)),
        decision.a_series_identity_status, decision.a_series_jobs,
        decision.co_location_conflicts, "withdrawn" if all_deleted else "deny",
        tuple(dict.fromkeys(reasons)), tuple(identities), tuple(actions), LIMITATIONS,
        created_at,
    )
