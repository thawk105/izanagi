"""File-bound, fail-closed coordinator for one T-810 13-job attempt."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, is_dataclass
import os
from pathlib import Path
import re
import shlex
import stat
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
    GitIdentity,
    T810ValidationError,
    pass_witness_sha256,
    resolve_git_identity,
    validate_t810,
)
from tools.pegasus import t810_harness_schema as schema
from tools.pegasus import t810_pbs_wrapper as pbs_wrapper


POLICY_SCHEMA = "t810-admission-policy/v1"
GUARD_RECEIPT_SCHEMA = "t810-guard-receipt/v1"
BUDGET_RECEIPT_SCHEMA = "t810-budget-receipt/v1"
_NODE_RECEIPT_NAME = "node-receipt.jsonl"
_MEASUREMENTS_NAME = "measurements.jsonl"


class T810CoordinatorError(RuntimeError):
    """A fail-closed policy, authorization, filesystem, or receipt violation."""


@dataclass(frozen=True)
class PreparedGroup:
    preregistration: VerifiedT810Preregistration
    admission_policy: Mapping[str, Any]
    authorization: schema.AuthorizationToken
    launch_intent: Mapping[str, Any]
    launch_intent_sha256: str
    manifest: Mapping[str, Any]
    manifest_sha256: str
    release_nonce: str
    approved_hostnames: frozenset[str]
    limitations: frozenset[str]
    repository_roots: frozenset[Path]
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
class NodeReceipt:
    path: Path
    raw: bytes
    sha256: str
    events: tuple[Mapping[str, Any], ...]


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
Sleeper = Callable[[float], None]
Validator = Callable[..., Any]


def _fail(message: str) -> None:
    raise T810CoordinatorError(message)


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{name} must be an object")
    return dict(value)


def _exact(value: Any, fields: set[str] | frozenset[str], name: str) -> dict[str, Any]:
    result = _object(value, name)
    if set(result) != set(fields):
        _fail(f"{name} has unknown or missing fields")
    return result


def _text(value: Any, name: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value:
        _fail(f"{name} must be a non-empty string")
    return value


def _integer(value: Any, name: str, *, minimum: int = 0, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        _fail(f"{name} must be an integer >= {minimum}")
    return value


def _digest(value: Any, name: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if (not isinstance(value, str) or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)):
        _fail(f"{name} must be a lowercase SHA-256 digest")
    return value


def _strings(value: Any, name: str, *, unique: bool = True) -> list[str]:
    if (not isinstance(value, list)
            or any(not isinstance(item, str) or not item for item in value)):
        _fail(f"{name} must be a string list")
    if unique and len(value) != len(set(value)):
        _fail(f"{name} contains duplicates")
    return list(value)


def _absolute_path(value: Any, name: str) -> Path:
    if isinstance(value, Path):
        path = value
        text = str(value)
    else:
        text = _text(value, name)
        assert text is not None
        path = Path(text)
    if not path.is_absolute() or str(path) != text or any(part == ".." for part in path.parts):
        _fail(f"{name} must be a canonical absolute path")
    return path


def _read_regular_bytes(path: Path, name: str, *, missing_ok: bool = False) -> bytes | None:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        if missing_ok:
            return None
        _fail(f"cannot read {name}: file is absent")
    except OSError as exc:
        _fail(f"cannot read {name}: {exc}")
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            _fail(f"{name} is not a regular file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns,
        ):
            _fail(f"{name} changed while reading")
        return b"".join(chunks)
    finally:
        os.close(fd)


def _assert_declared_file_identity(
    path: Path, declared_sha256: str, name: str,
) -> str:
    """Require a declared digest to describe stable regular-file bytes."""
    raw = _read_regular_bytes(path, name)
    assert raw is not None
    actual_sha256 = schema.sha256_bytes(raw)
    if actual_sha256 != declared_sha256:
        _fail(f"{name} does not match its declared SHA-256")
    return actual_sha256


def _assert_staged_file_identities(slot: Mapping[str, Any]) -> None:
    wrapper_sha256 = _assert_declared_file_identity(
        Path(slot["wrapper_path"]), slot["wrapper_sha256"], "staged wrapper",
    )
    shipped_wrapper = Path(__file__).resolve().parent / "t810_pbs_wrapper.py"
    shipped_raw = _read_regular_bytes(shipped_wrapper, "shipped wrapper")
    assert shipped_raw is not None
    if wrapper_sha256 != schema.sha256_bytes(shipped_raw):
        _fail("staged wrapper does not match the shipped wrapper bytes")
    _assert_declared_file_identity(
        Path(slot["binary_source_path"]), slot["binary_sha256"], "staged binary",
    )


def _read_json(path: Path, name: str) -> Mapping[str, Any]:
    raw = _read_regular_bytes(path, name)
    assert raw is not None
    try:
        return _object(schema.parse_json(raw), name)
    except schema.T810SchemaError as exc:
        raise T810CoordinatorError(f"cannot read {name}: {exc}") from exc


def _validate_policy(document: Any) -> Mapping[str, Any]:
    top = _exact(document, {
        "schema_version", "parallel_guard", "qsub", "approved_hostnames",
        "budget", "limitations",
    }, "admission policy")
    if top["schema_version"] != POLICY_SCHEMA:
        _fail("admission policy schema mismatch")
    guard = _exact(top["parallel_guard"], {"a_series_identity"}, "parallel_guard")
    identity = _exact(guard["a_series_identity"], {
        "status", "field", "pilot_patterns", "main_patterns",
    }, "parallel_guard.a_series_identity")
    if identity["status"] not in {"unresolved", "resolved"} or identity["field"] != "Job_Name":
        _fail("parallel guard identity is invalid")
    _strings(identity["pilot_patterns"], "parallel_guard pilot patterns")
    _strings(identity["main_patterns"], "parallel_guard main patterns")
    for pattern in identity["pilot_patterns"] + identity["main_patterns"]:
        if not pattern.startswith("^") or not pattern.endswith("$"):
            _fail("parallel guard patterns must be anchored")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise T810CoordinatorError("parallel guard pattern is invalid") from exc
    if identity["status"] == "resolved" and not (
        identity["pilot_patterns"] or identity["main_patterns"]
    ):
        _fail("resolved parallel guard identity has no patterns")
    if identity["status"] == "unresolved" and (
        identity["pilot_patterns"] or identity["main_patterns"]
    ):
        _fail("unresolved parallel guard identity has patterns")
    qsub = _exact(top["qsub"], {
        "status", "project", "queue", "walltime_by_run_kind",
    }, "qsub policy")
    if qsub["status"] not in {"unratified", "ratified"}:
        _fail("qsub status is invalid")
    walltimes = _exact(
        qsub["walltime_by_run_kind"], set(schema.RUN_KINDS), "qsub walltime map",
    )
    hosts = _exact(top["approved_hostnames"], {"status", "hostnames"}, "approved_hostnames")
    if hosts["status"] not in {"unratified", "ratified"}:
        _fail("approved_hostnames status is invalid")
    _strings(hosts["hostnames"], "approved_hostnames.hostnames")
    budget = _exact(top["budget"], {
        "status", "accounting_unit", "total_node_seconds", "estimates",
        "attempt_policy", "ledger", "admission",
    }, "budget policy")
    if budget["status"] not in {"unratified", "ratified"} or budget["accounting_unit"] != "node-seconds":
        _fail("budget status or accounting unit is invalid")
    estimates = _exact(budget["estimates"], set(schema.RUN_KINDS), "budget estimates")
    for run_kind, raw in estimates.items():
        estimate = _exact(raw, {
            "walltime_seconds", "jobs_per_attempt", "node_seconds_per_attempt",
            "provisional_note",
        }, f"budget estimate {run_kind}")
        _text(estimate["provisional_note"], f"budget estimate {run_kind} note")
    _exact(budget["attempt_policy"], {
        "builder_attempts", "liveness_max_attempts", "main_max_attempts_ref",
    }, "budget attempt policy")
    ledger = _exact(budget["ledger"], {
        "schema_version", "location", "lock_method", "counted_statuses", "genesis_sha256",
    }, "budget ledger policy")
    _digest(ledger["genesis_sha256"], "budget genesis")
    _strings(ledger["counted_statuses"], "budget counted statuses")
    _exact(budget["admission"], {
        "formula", "integer_arithmetic", "max_node_seconds",
    }, "budget admission policy")
    try:
        schema.validate_limitation_ids(top["limitations"], "$.limitations")
    except schema.T810SchemaError as exc:
        raise T810CoordinatorError(f"admission policy limitations are invalid: {exc}") from exc
    # Ratified values must be complete; unratified values are denied separately before receipts.
    if qsub["status"] == "ratified":
        project = _text(qsub["project"], "qsub.project")
        queue = _text(qsub["queue"], "qsub.queue")
        assert project is not None and queue is not None
        if any(character.isspace() for character in project + queue):
            _fail("qsub project or queue contains whitespace")
        for run_kind, walltime in walltimes.items():
            value = _text(walltime, f"qsub walltime {run_kind}")
            if re.fullmatch(r"[0-9]{2,}:[0-5][0-9]:[0-5][0-9]", value) is None:
                _fail(f"qsub walltime {run_kind} is invalid")
    elif qsub["project"] is not None or qsub["queue"] is not None or any(
        value is not None for value in walltimes.values()
    ):
        _fail("unratified qsub values must be null")
    if hosts["status"] == "ratified" and not hosts["hostnames"]:
        _fail("ratified approved_hostnames is empty")
    if hosts["status"] == "unratified" and hosts["hostnames"]:
        _fail("unratified approved_hostnames is not empty")
    if budget["status"] == "ratified":
        _integer(budget["total_node_seconds"], "budget total", minimum=1)
        for run_kind, estimate in estimates.items():
            wall = _integer(estimate["walltime_seconds"], f"{run_kind} walltime", minimum=1)
            jobs = _integer(estimate["jobs_per_attempt"], f"{run_kind} jobs", minimum=1)
            amount = _integer(
                estimate["node_seconds_per_attempt"], f"{run_kind} amount", minimum=1,
            )
            if wall * jobs != amount:
                _fail(f"budget estimate {run_kind} product mismatch")
        attempts = budget["attempt_policy"]
        if (_integer(attempts["builder_attempts"], "builder_attempts", minimum=1) != 1
                or _integer(attempts["liveness_max_attempts"], "liveness_max_attempts", minimum=1) is None
                or attempts["main_max_attempts_ref"] != "preregistration.terminal.retry.max_attempts"):
            _fail("ratified budget attempt policy is invalid")
    else:
        if budget["total_node_seconds"] is not None:
            _fail("unratified budget total must be null")
        for estimate in estimates.values():
            if any(estimate[field] is not None for field in (
                "walltime_seconds", "jobs_per_attempt", "node_seconds_per_attempt",
            )):
                _fail("unratified budget estimates must be null")
        if any(value is not None for value in budget["attempt_policy"].values()):
            _fail("unratified budget attempt policy must be null")
    if (ledger["schema_version"] != "t810-budget-ledger-event/v1"
            or ledger["location"] != "repository-external"
            or ledger["lock_method"] != "flock"
            or ledger["counted_statuses"] != ["reserved", "consumed"]):
        _fail("budget ledger policy literals are invalid")
    admission = budget["admission"]
    if (admission["formula"] != "0 < required <= remaining"
            or admission["integer_arithmetic"] != "exact"
            or admission["max_node_seconds"] != 2**63 - 1):
        _fail("budget admission policy literals are invalid")
    return top


def load_admission_policy(path: str | Path) -> tuple[Mapping[str, Any], str]:
    """Load the exact policy file; duplicate keys and unknown fields fail closed."""
    document = _validate_policy(_read_json(Path(path), "admission policy"))
    return document, schema.canonical_sha256(document)


def _require_fully_ratified(policy: Mapping[str, Any]) -> None:
    statuses = {
        "parallel_guard.a_series_identity": policy["parallel_guard"]["a_series_identity"]["status"],
        "qsub": policy["qsub"]["status"],
        "approved_hostnames": policy["approved_hostnames"]["status"],
        "budget": policy["budget"]["status"],
    }
    expected = {
        "parallel_guard.a_series_identity": "resolved",
        "qsub": "ratified", "approved_hostnames": "ratified", "budget": "ratified",
    }
    denied = [name for name, status in statuses.items() if status != expected[name]]
    if denied:
        _fail("admission policy is not fully ratified: " + ", ".join(denied))


def _validate_guard_receipt(
    value: Any, *, launch_intent_sha256: str, policy_sha256: str,
) -> Mapping[str, Any]:
    receipt = _exact(value, {
        "schema_version", "launch_intent_sha256", "phase", "policy_sha256",
        "snapshot_sha256", "a_series_identity_status", "a_series_jobs",
        "co_location_conflicts", "decision", "reason_codes", "b_request_ids",
        "withdrawal_actions", "limitations", "created_at",
    }, "guard receipt")
    if (receipt["schema_version"] != GUARD_RECEIPT_SCHEMA
            or receipt["phase"] != "pre-release" or receipt["decision"] != "allow"):
        _fail("guard receipt schema, phase, or decision is invalid")
    if (receipt["launch_intent_sha256"] != launch_intent_sha256
            or receipt["policy_sha256"] != policy_sha256):
        _fail("guard receipt binding mismatch")
    _digest(receipt["snapshot_sha256"], "guard snapshot")
    if receipt["a_series_identity_status"] != "resolved":
        _fail("guard receipt identity is not resolved")
    for field in ("a_series_jobs", "reason_codes", "b_request_ids"):
        _strings(receipt[field], f"guard receipt {field}")
    if receipt["a_series_jobs"] or receipt["reason_codes"]:
        _fail("allowing guard receipt has A-series jobs or reason codes")
    if not isinstance(receipt["co_location_conflicts"], list) or receipt["co_location_conflicts"]:
        _fail("allowing guard receipt has co-location conflicts")
    if not isinstance(receipt["withdrawal_actions"], list) or receipt["withdrawal_actions"]:
        _fail("allowing guard receipt has withdrawal actions")
    schema.validate_limitation_ids(receipt["limitations"], "$.guard_receipt.limitations")
    _text(receipt["created_at"], "guard receipt created_at")
    return receipt


def _validate_budget_receipt(
    value: Any, *, launch_intent_sha256: str, policy_sha256: str, run_kind: str,
) -> Mapping[str, Any]:
    receipt = _exact(value, {
        "schema_version", "launch_intent_sha256", "policy_sha256", "estimates_sha256",
        "ledger_path", "ledger_sha256_before", "ledger_sha256_after", "reservation_id",
        "run_kind", "requested_attempts", "estimate_per_attempt_node_seconds",
        "required_node_seconds", "total_node_seconds", "counted_node_seconds",
        "remaining_node_seconds", "admitted", "reason", "created_at", "limitations",
    }, "budget receipt")
    if (receipt["schema_version"] != BUDGET_RECEIPT_SCHEMA
            or receipt["admitted"] is not True or receipt["reason"] != "admitted"):
        _fail("budget receipt schema or decision is invalid")
    if (receipt["launch_intent_sha256"] != launch_intent_sha256
            or receipt["policy_sha256"] != policy_sha256
            or receipt["run_kind"] != run_kind):
        _fail("budget receipt binding mismatch")
    for field in (
        "estimates_sha256", "ledger_sha256_before", "ledger_sha256_after", "reservation_id",
    ):
        _digest(receipt[field], f"budget receipt {field}")
    if receipt["ledger_sha256_before"] == receipt["ledger_sha256_after"]:
        _fail("admitted budget receipt has no ledger-after transition")
    _absolute_path(receipt["ledger_path"], "budget receipt ledger_path")
    for field in (
        "requested_attempts", "estimate_per_attempt_node_seconds", "required_node_seconds",
        "total_node_seconds", "counted_node_seconds", "remaining_node_seconds",
    ):
        _integer(receipt[field], f"budget receipt {field}")
    if (receipt["requested_attempts"] != 1
            or receipt["required_node_seconds"]
            != receipt["estimate_per_attempt_node_seconds"] * receipt["requested_attempts"]
            or receipt["remaining_node_seconds"]
            != receipt["total_node_seconds"] - receipt["counted_node_seconds"]
            - receipt["required_node_seconds"]
            or receipt["remaining_node_seconds"] < 0):
        _fail("budget receipt arithmetic is inconsistent")
    schema.validate_limitation_ids(receipt["limitations"], "$.budget_receipt.limitations")
    _text(receipt["created_at"], "budget receipt created_at")
    return receipt


_VALIDATOR_REQUIRED = {
    "repo_root", "approved_git_identity", "approved_git_identity_sha256", "writable_root",
    "manifest_path", "manifest_root", "expected_manifest_sha256", "executable",
    "expected_executable_sha256", "attempt_root", "attempt_receipt", "attempt_nonce",
    "pre_invocation_nonce",
}


def _decode_validator_kwargs(value: Any) -> Mapping[str, Any]:
    raw = _object(value, "validator kwargs")
    if not _VALIDATOR_REQUIRED <= set(raw) or set(raw) - (_VALIDATOR_REQUIRED | {"mountinfo_text"}):
        _fail("validator kwargs has unknown or missing fields")
    result = dict(raw)
    for field in (
        "repo_root", "writable_root", "manifest_path", "manifest_root", "executable",
        "attempt_root",
    ):
        result[field] = _absolute_path(raw[field], f"validator kwargs {field}")
    if isinstance(raw["approved_git_identity"], GitIdentity):
        identity_value = raw["approved_git_identity"]
        identity = asdict(identity_value)
    else:
        identity = _exact(raw["approved_git_identity"], {
            "repo_realpath", "git_dir_realpath", "common_dir_realpath",
        }, "approved_git_identity")
        identity_value = GitIdentity(**identity)
    for field in identity:
        _absolute_path(identity[field], f"approved_git_identity.{field}")
    result["approved_git_identity"] = identity_value
    for field in (
        "approved_git_identity_sha256", "expected_manifest_sha256",
        "expected_executable_sha256",
    ):
        _digest(raw[field], f"validator kwargs {field}")
    if raw["attempt_receipt"] is not None:
        result["attempt_receipt"] = _object(raw["attempt_receipt"], "attempt receipt")
    _text(raw["attempt_nonce"], "validator kwargs attempt_nonce")
    _text(raw["pre_invocation_nonce"], "validator kwargs pre_invocation_nonce")
    if "mountinfo_text" in raw and raw["mountinfo_text"] is not None:
        _text(raw["mountinfo_text"], "validator kwargs mountinfo_text")
    return result


_CONFIG_FIELDS = {
    "launch_intent", "admission_policy_path", "guard_receipt_path",
    "budget_receipt_path", "release_nonce", "manifest_created_at", "validator_kwargs",
}


def decode_config(value: Any) -> Mapping[str, Any]:
    """Decode the exact JSON-facing config before any validator or effect call."""
    raw = _exact(value, _CONFIG_FIELDS, "coordinator config")
    try:
        intent = schema.validate_launch_intent(raw["launch_intent"])
    except schema.T810SchemaError as exc:
        raise T810CoordinatorError(f"invalid launch intent: {exc}") from exc
    result = dict(raw)
    result["launch_intent"] = intent
    for field in ("admission_policy_path", "guard_receipt_path", "budget_receipt_path"):
        result[field] = _absolute_path(raw[field], field)
    _text(raw["release_nonce"], "release_nonce")
    _text(raw["manifest_created_at"], "manifest_created_at")
    result["validator_kwargs"] = _decode_validator_kwargs(raw["validator_kwargs"])
    return result


def repository_roots_from_git_identity(identity: GitIdentity) -> frozenset[Path]:
    """Derive main and linked-worktree realpaths from the approved common git dir."""
    if not isinstance(identity, GitIdentity):
        _fail("approved GitIdentity is required")
    common = Path(identity.common_dir_realpath).resolve(strict=True)
    roots = {Path(identity.repo_realpath).resolve(strict=True)}
    if common.name == ".git":
        roots.add(common.parent.resolve(strict=True))
    worktrees = common / "worktrees"
    if worktrees.is_dir():
        for admin in worktrees.iterdir():
            gitdir = admin / "gitdir"
            if gitdir.is_symlink():
                _fail("git common-dir contains an invalid worktree registration")
            registered_raw = _read_regular_bytes(
                gitdir, "worktree registration", missing_ok=True,
            )
            if registered_raw is None:
                try:
                    os.lstat(admin / "locked")
                except FileNotFoundError:
                    continue
                except OSError as exc:
                    raise T810CoordinatorError(
                        "cannot inspect worktree registration lock"
                    ) from exc
                _fail("cannot read worktree registration: file is absent")
            try:
                registered_text = registered_raw.decode("utf-8").strip()
            except UnicodeError as exc:
                raise T810CoordinatorError("cannot resolve registered worktree") from exc
            if not registered_text:
                continue
            try:
                registered = Path(registered_text).resolve(strict=True)
            except FileNotFoundError:
                try:
                    registered = Path(registered_text).resolve(strict=False)
                except OSError as exc:
                    raise T810CoordinatorError(
                        "cannot resolve registered worktree"
                    ) from exc
            except OSError as exc:
                raise T810CoordinatorError("cannot resolve registered worktree") from exc
            roots.add(registered.parent)
    return frozenset(roots)


def _require_token(
    token: Any, *, preregistration: VerifiedT810Preregistration, policy_sha256: str,
    run_kind: str,
) -> schema.AuthorizationToken:
    if not isinstance(token, schema.AuthorizationToken):
        _fail("launch authorization witness must be a verified AuthorizationToken")
    if (token.preregistration_sha256 != preregistration.sha256
            or token.policy_sha256 != policy_sha256 or token.run_kind != run_kind
            or token.document["approval_id"] != preregistration.approval_id):
        _fail("AuthorizationToken binding mismatch")
    return token


def _canonical_qsub_argv(
    slot: Mapping[str, Any], *, policy: Mapping[str, Any], run_kind: str,
) -> tuple[str, ...]:
    qsub = policy["qsub"]
    return (
        "qsub", "-A", qsub["project"], "-q", qsub["queue"], "-b", "1",
        "-l", f"elapstim_req={qsub['walltime_by_run_kind'][run_kind]}",
        "-N", slot["job_name"], "-o", slot["pbs_stdout_path"],
        "-e", slot["pbs_stderr_path"], slot["script_path"],
    )


def _canonical_job_script(slot: Mapping[str, Any]) -> bytes:
    return ("#!/bin/sh\nset -eu\nexec " + shlex.join(slot["wrapper_argv"]) + "\n").encode(
        "utf-8",
    )


def _assert_canonical_job_script(slot: Mapping[str, Any]) -> None:
    raw = _read_regular_bytes(Path(slot["script_path"]), "canonical PBS job script")
    if raw != _canonical_job_script(slot):
        _fail("PBS job script does not match the frozen wrapper argv")


def _authorization_token(
    witness: Any, *, preregistration: VerifiedT810Preregistration,
    policy_sha256: str, run_kind: str,
) -> schema.AuthorizationToken:
    try:
        token = schema.verify_launch_authorization(
            witness, run_kind=run_kind, preregistration_sha256=preregistration.sha256,
            policy_sha256=policy_sha256,
        )
    except schema.T810SchemaError as exc:
        raise T810CoordinatorError(f"invalid launch authorization witness: {exc}") from exc
    return _require_token(
        token, preregistration=preregistration, policy_sha256=policy_sha256,
        run_kind=run_kind,
    )


def _ensure_external_root(
    token: schema.AuthorizationToken, path: Path, name: str,
    *, repository_roots: frozenset[Path],
) -> Path:
    if not isinstance(token, schema.AuthorizationToken):
        _fail("AuthorizationToken is required at the directory effect boundary")
    try:
        resolved = schema.assert_repository_external(path, repository_roots=repository_roots)
    except schema.T810SchemaError as exc:
        raise T810CoordinatorError(f"{name} is not repository-external: {exc}") from exc
    resolved.mkdir(parents=True, exist_ok=True)
    info = resolved.lstat()
    if not stat.S_ISDIR(info.st_mode) or resolved.is_symlink():
        _fail(f"{name} must be a real directory")
    return resolved


def _write_create_only(token: schema.AuthorizationToken, path: Path, value: Any) -> bytes:
    raw = schema.canonical_json_bytes(value) + b"\n"
    _write_bytes_create_only(token, path, raw)
    return raw


def _write_bytes_create_only(
    token: schema.AuthorizationToken, path: Path, raw: bytes, *, mode: int = 0o600,
) -> None:
    if not isinstance(token, schema.AuthorizationToken):
        _fail("AuthorizationToken is required at the publication effect boundary")
    if not isinstance(raw, bytes):
        _fail("publication bytes must be exact bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, mode)
        try:
            offset = 0
            while offset < len(raw):
                written = os.write(fd, raw[offset:])
                if written <= 0:
                    _fail(f"short write for {path.name}")
                offset += written
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        raise T810CoordinatorError(f"create-only publication failed: {path}") from exc


def _touch_create_only(token: schema.AuthorizationToken, path: Path) -> None:
    if not isinstance(token, schema.AuthorizationToken):
        _fail("AuthorizationToken is required at the publication effect boundary")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
        os.fsync(fd)
        os.close(fd)
    except OSError as exc:
        raise T810CoordinatorError(f"create-only publication failed: {path}") from exc


def prepare_group(
    config: Mapping[str, Any], preregistration: VerifiedT810Preregistration,
    authorization: schema.AuthorizationToken, *, repository_roots: Sequence[Path],
) -> PreparedGroup:
    if not isinstance(preregistration, VerifiedT810Preregistration):
        _fail("verified preregistration from loader is required")
    document = decode_config(config)
    intent = document["launch_intent"]
    policy, policy_sha256 = load_admission_policy(document["admission_policy_path"])
    # C-7: no guard/budget receipt is read until every ratifiable policy field passes.
    _require_fully_ratified(policy)
    token = _require_token(
        authorization, preregistration=preregistration, policy_sha256=policy_sha256,
        run_kind=intent["run_kind"],
    )
    if intent["policy_sha256"] != policy_sha256:
        _fail("launch intent policy digest mismatch")
    if (intent["preregistration_sha256"] != preregistration.sha256
            or intent["prereg_approval_id"] != preregistration.approval_id):
        _fail("launch intent preregistration binding mismatch")
    selected = preregistration.projection["design"]["selected"]
    if (intent["node_count"] != int(selected["node_count"])
            or intent["round_count"] != int(selected["round_count"])):
        _fail("launch intent differs from preregistration design")
    try:
        coordinator_identity = resolve_git_identity(Path(__file__).resolve().parents[2])
    except T810ValidationError as exc:
        raise T810CoordinatorError("cannot resolve coordinator repository identity") from exc
    caller_roots = frozenset(
        Path(root).resolve(strict=False) for root in repository_roots
    )
    if not caller_roots:
        _fail("repository_roots must not be empty")
    roots = frozenset({
        *repository_roots_from_git_identity(coordinator_identity),
        *caller_roots,
    })
    work_root = _ensure_external_root(token, Path(intent["work_root"]), "work_root", repository_roots=roots)
    output_root = _ensure_external_root(token, Path(intent["output_root"]), "output_root", repository_roots=roots)
    if work_root == output_root or work_root in output_root.parents or output_root in work_root.parents:
        _fail("work_root and output_root must be disjoint")
    for slot in intent["slots"]:
        for field in ("pbs_stdout_path", "pbs_stderr_path", "script_path"):
            try:
                schema.assert_repository_external(slot[field], repository_roots=roots)
            except schema.T810SchemaError as exc:
                raise T810CoordinatorError(f"{field} is not repository-external: {exc}") from exc
        slot_root = output_root / slot["slot_id"]
        script_path = work_root / slot["slot_id"] / "job.pbs"
        request_path = work_root / slot["slot_id"] / "wrapper-request.json"
        if (Path(slot["pbs_stdout_path"]) != slot_root / "pbs.stdout.log"
                or Path(slot["pbs_stderr_path"]) != slot_root / "pbs.stderr.log"
                or Path(slot["script_path"]) != script_path):
            _fail("PBS paths do not match the frozen artifact layout")
        if tuple(slot["wrapper_argv"]) != (
            "python3.10", slot["wrapper_path"], "--request", str(request_path),
        ):
            _fail("wrapper argv does not bind the static request path")
        if tuple(slot["qsub_argv"]) != _canonical_qsub_argv(
            slot, policy=policy, run_kind=intent["run_kind"],
        ):
            _fail("qsub argv does not match the ratified canonical form")
        _assert_staged_file_identities(slot)
    intent_sha256 = schema.canonical_sha256(intent)
    guard = _validate_guard_receipt(
        _read_json(document["guard_receipt_path"], "guard receipt"),
        launch_intent_sha256=intent_sha256, policy_sha256=policy_sha256,
    )
    budget = _validate_budget_receipt(
        _read_json(document["budget_receipt_path"], "budget receipt"),
        launch_intent_sha256=intent_sha256, policy_sha256=policy_sha256,
        run_kind=intent["run_kind"],
    )
    try:
        schema.assert_repository_external(budget["ledger_path"], repository_roots=roots)
    except schema.T810SchemaError as exc:
        raise T810CoordinatorError(f"budget ledger is not repository-external: {exc}") from exc
    limitations = frozenset(
        policy["limitations"] + guard["limitations"] + budget["limitations"],
    )
    control = work_root / "control"
    intent_path = control / "launch-intent.json"
    _write_create_only(token, intent_path, intent)
    manifest = schema.validate_group_manifest({
        "schema_version": schema.GROUP_MANIFEST_SCHEMA,
        "group_id": intent["group_id"], "created_at": document["manifest_created_at"],
        "launch_intent_sha256": intent_sha256,
        "guard_receipt_sha256": schema.canonical_sha256(guard),
        "budget_receipt_sha256": schema.canonical_sha256(budget),
        "release_token_commitment": schema.release_token_commitment(document["release_nonce"]),
    })
    manifest_path = output_root / "group-manifest.json"
    _write_create_only(token, manifest_path, manifest)
    for slot in intent["slots"]:
        pbs_wrapper.publish_wrapper_request(
            intent, manifest, preregistration, token, slot_id=slot["slot_id"],
            dependency_manifest_path=Path(slot["wrapper_path"]).parent / "dependencies.json",
            interpreter_realpath=Path("/usr/bin/python3.10"),
        )
        _write_bytes_create_only(
            token, Path(slot["script_path"]), _canonical_job_script(slot), mode=0o700,
        )
        for name in ("pbs.stdout.log", "pbs.stderr.log"):
            _touch_create_only(token, output_root / slot["slot_id"] / name)
    for name in ("coordinator.stdout.log", "coordinator.stderr.log", "coordinator-receipt.jsonl"):
        _touch_create_only(token, output_root / name)
    return PreparedGroup(
        preregistration, policy, token, intent, intent_sha256, manifest,
        schema.canonical_sha256(manifest), document["release_nonce"],
        frozenset(policy["approved_hostnames"]["hostnames"]), limitations, roots,
        work_root, output_root, intent_path, manifest_path,
        output_root / "submission-receipt.json", output_root / "coordinator-receipt.jsonl",
        output_root / "terminal-state.json", control / "release.json", control / "cancel.json",
    )


def _append_coordinator_event(
    prepared: PreparedGroup, token: schema.AuthorizationToken,
    event: str, details: Mapping[str, Any], *,
    wall_time: str, monotonic_ns: int, slot_id: str | None = None,
) -> str:
    _require_token(
        token, preregistration=prepared.preregistration,
        policy_sha256=prepared.launch_intent["policy_sha256"],
        run_kind=prepared.launch_intent["run_kind"],
    )
    raw = _read_regular_bytes(prepared.coordinator_receipt_path, "coordinator receipt")
    assert raw is not None
    lines = raw.splitlines()
    previous = None if not lines else schema.canonical_sha256(schema.parse_json(lines[-1]))
    document = schema.validate_coordinator_event({
        "schema_version": schema.COORDINATOR_EVENT_SCHEMA,
        "group_manifest_sha256": prepared.manifest_sha256, "sequence": len(lines),
        "event": event, "wall_time": wall_time, "coordinator_monotonic_ns": monotonic_ns,
        "slot_id": slot_id, "previous_event_sha256": previous, "details": dict(details),
    })
    encoded = schema.canonical_json_bytes(document) + b"\n"
    try:
        fd = os.open(
            prepared.coordinator_receipt_path,
            os.O_WRONLY | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0),
        )
        if os.write(fd, encoded) != len(encoded):
            _fail("short coordinator receipt write")
        os.fsync(fd)
        os.close(fd)
    except OSError as exc:
        raise T810CoordinatorError("could not append coordinator receipt") from exc
    return schema.canonical_sha256(document)


def _scheduler_effect(
    prepared: PreparedGroup, token: schema.AuthorizationToken,
    scheduler_run: SchedulerRun, argv: Sequence[str],
) -> subprocess.CompletedProcess[str]:
    _require_token(
        token, preregistration=prepared.preregistration,
        policy_sha256=prepared.launch_intent["policy_sha256"],
        run_kind=prepared.launch_intent["run_kind"],
    )
    allowed = {
        _canonical_qsub_argv(
            slot, policy=prepared.admission_policy,
            run_kind=prepared.launch_intent["run_kind"],
        )
        for slot in prepared.launch_intent["slots"]
    }
    if tuple(argv) not in allowed or not argv or argv[0] != "qsub":
        _fail("scheduler effect argv is not a canonical qsub command")
    selected = next(
        slot for slot in prepared.launch_intent["slots"]
        if tuple(argv) == _canonical_qsub_argv(
            slot, policy=prepared.admission_policy,
            run_kind=prepared.launch_intent["run_kind"],
        )
    )
    _assert_canonical_job_script(selected)
    result = scheduler_run(
        token, prepared, list(argv), cwd=str(prepared.work_root), env={},
    )
    if not isinstance(result, subprocess.CompletedProcess):
        _fail("scheduler adapter returned an invalid result")
    return result


def submit_group(
    prepared: PreparedGroup, token: schema.AuthorizationToken, *,
    scheduler_run: SchedulerRun, wall_clock: WallClock,
) -> Mapping[str, Any]:
    requests: list[dict[str, Any]] = []
    for slot in prepared.launch_intent["slots"]:
        result = _scheduler_effect(prepared, token, scheduler_run, slot["qsub_argv"])
        stdout = result.stdout if isinstance(result.stdout, str) else ""
        stderr = result.stderr if isinstance(result.stderr, str) else ""
        pbs_id = stdout.strip() if result.returncode == 0 and stdout.strip() else None
        requests.append({
            "slot_id": slot["slot_id"], "logical_request_id": slot["logical_request_id"],
            "job_name": slot["job_name"], "qsub_argv": list(slot["qsub_argv"]),
            "qsub_rc": result.returncode, "qsub_stdout": stdout,
            "qsub_stderr": stderr, "pbs_request_id": pbs_id,
        })
    receipt = schema.validate_submission_receipt({
        "schema_version": schema.SUBMISSION_RECEIPT_SCHEMA,
        "group_manifest_sha256": prepared.manifest_sha256,
        "created_at": wall_clock(), "requests": requests,
    })
    _write_create_only(token, prepared.submission_path, receipt)
    return receipt


def _complete_submission(prepared: PreparedGroup) -> Mapping[str, Any]:
    receipt = schema.validate_submission_receipt(
        _read_json(prepared.submission_path, "submission receipt"),
    )
    if receipt["group_manifest_sha256"] != prepared.manifest_sha256:
        _fail("submission receipt manifest mismatch")
    for slot, request in zip(prepared.launch_intent["slots"], receipt["requests"], strict=True):
        for field in ("slot_id", "logical_request_id", "job_name", "qsub_argv"):
            if request[field] != slot[field]:
                _fail(f"submission receipt {field} mismatch")
    return receipt


def _node_path(prepared: PreparedGroup, slot_id: str) -> Path:
    return prepared.work_root / slot_id / _NODE_RECEIPT_NAME


def _bound_node_event(
    prepared: PreparedGroup, event: Mapping[str, Any], request: Mapping[str, Any],
) -> Mapping[str, Any]:
    node = schema.validate_node_event(event)
    if (node["group_manifest_sha256"] != prepared.manifest_sha256
            or node["group_id"] != prepared.launch_intent["group_id"]):
        _fail("node event manifest identity mismatch")
    for field in ("slot_id", "logical_request_id", "pbs_request_id"):
        if node[field] != request[field]:
            _fail(f"node event {field} mismatch")
    return node


def _read_node_receipt(
    prepared: PreparedGroup, request: Mapping[str, Any], *, missing_ok: bool = False,
) -> NodeReceipt | None:
    slot_id = request["slot_id"]
    path = _node_path(prepared, slot_id)
    raw = _read_regular_bytes(path, f"{slot_id} node receipt", missing_ok=missing_ok)
    if raw is None:
        return None
    if not raw or not raw.endswith(b"\n") or b"\n\n" in raw:
        _fail(f"{slot_id} node receipt is not complete JSONL")
    events: list[Mapping[str, Any]] = []
    previous: str | None = None
    for index, line in enumerate(raw.splitlines()):
        try:
            event = _bound_node_event(
                prepared, _object(schema.parse_json(line), "node event"), request,
            )
        except schema.T810SchemaError as exc:
            raise T810CoordinatorError(f"{slot_id} node receipt is invalid: {exc}") from exc
        if event["sequence"] != index or event["previous_event_sha256"] != previous:
            _fail(f"{slot_id} node receipt hash chain is invalid")
        events.append(event)
        previous = schema.canonical_sha256(event)
    names = [event["event"] for event in events]
    allowed = (
        ["preflight"], ["preflight", "terminal"],
        ["preflight", "start_ack"], ["preflight", "start_ack", "terminal"],
        ["preflight", "start_ack", "measurement"],
        ["preflight", "start_ack", "measurement", "terminal"],
    )
    if names not in allowed:
        _fail(f"{slot_id} node receipt event order is invalid")
    return NodeReceipt(path, raw, schema.sha256_bytes(raw), tuple(events))


def _wait_for_phase(
    prepared: PreparedGroup, phase: str, *, clock_ns: Clock, sleep: Sleeper,
    timeout_seconds: int | float,
) -> tuple[Mapping[str, NodeReceipt], Mapping[str, int]]:
    if phase not in {"preflight", "start_ack", "terminal"}:
        _fail("unknown node receipt phase")
    submission = _complete_submission(prepared)
    requests = {request["slot_id"]: request for request in submission["requests"]}
    started = clock_ns()
    deadline = started + int(timeout_seconds * 1_000_000_000)
    accepted: dict[str, NodeReceipt] = {}
    received: dict[str, int] = {}
    while True:
        for slot_id, request in requests.items():
            if slot_id in accepted:
                continue
            receipt = _read_node_receipt(prepared, request, missing_ok=True)
            if receipt is None:
                continue
            names = [event["event"] for event in receipt.events]
            ready = False
            if phase == "preflight":
                if names == ["preflight"]:
                    ready = True
                elif (names == ["preflight", "terminal"]
                      and receipt.events[-1]["payload"]["state"] == "pre_release_invalid"):
                    ready = True
                else:
                    _fail(f"{slot_id} published a post-release event before release")
            elif phase == "start_ack":
                ready = "start_ack" in names or "terminal" in names
            else:
                ready = names[-1] == "terminal"
            if ready:
                accepted[slot_id] = receipt
                received[slot_id] = clock_ns()
        if len(accepted) == schema.NODE_COUNT:
            return accepted, received
        now = clock_ns()
        if now >= deadline:
            return accepted, received
        sleep(min(0.1, (deadline - now) / 1_000_000_000))


def evaluate_ready_barrier(
    prepared: PreparedGroup,
    receipts: Mapping[str, NodeReceipt] | Sequence[Mapping[str, Any]], *,
    elapsed_seconds: int | float,
) -> BarrierDecision:
    submission = _complete_submission(prepared)
    if not isinstance(receipts, Mapping):
        requests = {request["slot_id"]: request for request in submission["requests"]}
        converted: dict[str, NodeReceipt] = {}
        for raw in receipts:
            if not isinstance(raw, Mapping):
                continue
            slot_id = raw.get("slot_id")
            if slot_id not in requests or slot_id in converted:
                continue
            try:
                event = _bound_node_event(prepared, raw, requests[slot_id])
            except (schema.T810SchemaError, T810CoordinatorError):
                continue
            encoded = schema.canonical_json_bytes(event) + b"\n"
            converted[slot_id] = NodeReceipt(
                _node_path(prepared, slot_id), encoded, schema.sha256_bytes(encoded), (event,),
            )
        receipts = converted
    if any(request["qsub_rc"] != 0 for request in submission["requests"]):
        return BarrierDecision("cancel", ("submission_failed",), {})
    if len(receipts) < schema.NODE_COUNT:
        status = "waiting" if elapsed_seconds < schema.READY_TIMEOUT_SECONDS else "cancel"
        return BarrierDecision(status, () if status == "waiting" else ("ready_timeout",), {})
    requests = {request["slot_id"]: request for request in submission["requests"]}
    reasons: set[str] = set()
    digests: dict[str, str] = {}
    hostnames: list[str] = []
    for slot_id, request in requests.items():
        receipt = receipts.get(slot_id)
        if receipt is None:
            reasons.add("preflight_failed")
            continue
        event = receipt.events[0]
        if event["event"] != "preflight":
            reasons.add("preflight_failed")
            continue
        digests[slot_id] = receipt.sha256
        if len(receipt.events) == 2:
            reasons.update(receipt.events[-1]["payload"]["reason_codes"])
        payload = event["payload"]
        hostname = payload["actual_hostname"]
        hostnames.append(hostname)
        slot = prepared.launch_intent["slots"][int(slot_id[-2:])]
        if payload["assigned_hostname"] != hostname:
            reasons.add("hostname_mismatch")
        if hostname not in prepared.approved_hostnames:
            reasons.add("unapproved_hostname")
        if (payload["binary_source_sha256"] != slot["binary_sha256"]
                or payload["binary_copy_sha256"] != slot["binary_sha256"]):
            reasons.add("binary_copy_hash_mismatch")
        if (payload["dependency_manifest_sha256"] != slot["expected_dependency_manifest_sha256"]
                or payload["module_list_sha256"] != slot["expected_module_list_sha256"]):
            reasons.add("pre_inventory_mismatch")
        if payload["trace_symbols"] or payload["hardware"]["numa_nodes"] != slot["expected_numa_nodes"]:
            reasons.add("preflight_failed")
        samples = payload["quiet_samples"]
        if len(samples) < 3 or any(sample["load_average_1m"] > 1.0 for sample in samples[-3:]):
            reasons.add("quiet_gate_failed")
        if payload["observed_submission_argv"] != slot["qsub_argv"]:
            reasons.add("submission_argv_mismatch")
        absence = payload["repo_absence"]
        if (absence["package_repo_free"] is not False
                or absence["roots_repo_external"] is not False
                or absence["git_ancestor_absent"] is not True
                or absence["pbs_workdir_repo_external"] is not False
                or not event["limitations"]["repository_absence_not_proven_from_node"]):
            reasons.add("preflight_failed")
        if payload["competing_processes"] or not payload["passed"] or payload["reason_codes"]:
            reasons.add("preflight_failed")
    if len(set(hostnames)) != schema.NODE_COUNT:
        reasons.add("hostname_count_mismatch")
        if len(hostnames) != len(set(hostnames)):
            reasons.add("duplicate_hostname")
    return BarrierDecision("release" if not reasons else "cancel", tuple(sorted(reasons)), digests)


def _publish_marker(
    prepared: PreparedGroup, token: schema.AuthorizationToken, *, kind: str,
    wall_clock: WallClock, reason_codes: Sequence[str] = (),
) -> tuple[Mapping[str, Any], str]:
    _require_token(
        token, preregistration=prepared.preregistration,
        policy_sha256=prepared.launch_intent["policy_sha256"],
        run_kind=prepared.launch_intent["run_kind"],
    )
    if kind == "release":
        if prepared.cancel_path.exists():
            _fail("release forbidden after cancel")
        marker = schema.validate_control_marker({
            "schema_version": schema.CONTROL_MARKER_SCHEMA,
            "group_manifest_sha256": prepared.manifest_sha256,
            "group_id": prepared.launch_intent["group_id"], "kind": "release",
            "published_at": wall_clock(), "nonce": prepared.release_nonce,
        }, expected_release_token_commitment=prepared.manifest["release_token_commitment"])
        path = prepared.release_path
    elif kind == "cancel":
        marker = schema.validate_control_marker({
            "schema_version": schema.CONTROL_MARKER_SCHEMA,
            "group_manifest_sha256": prepared.manifest_sha256,
            "group_id": prepared.launch_intent["group_id"], "kind": "cancel",
            "published_at": wall_clock(),
            "reason_codes": list(dict.fromkeys(reason_codes)),
        })
        path = prepared.cancel_path
    else:
        _fail("unknown control marker kind")
    _write_create_only(token, path, marker)
    return marker, schema.canonical_sha256(marker)


def publish_release(
    prepared: PreparedGroup, token: schema.AuthorizationToken, *, wall_clock: WallClock,
) -> tuple[Mapping[str, Any], str]:
    return _publish_marker(prepared, token, kind="release", wall_clock=wall_clock)


def publish_cancel(
    prepared: PreparedGroup, token: schema.AuthorizationToken,
    reason_codes: Sequence[str], *, wall_clock: WallClock,
) -> tuple[Mapping[str, Any], str]:
    return _publish_marker(
        prepared, token, kind="cancel", reason_codes=reason_codes, wall_clock=wall_clock,
    )


def release_is_still_active(prepared: PreparedGroup, release_sha256: str) -> bool:
    """Revalidate the published release; production calls this before completion wait."""
    if prepared.cancel_path.exists() or not prepared.release_path.exists():
        return False
    marker = schema.validate_control_marker(
        _read_json(prepared.release_path, "release marker"),
        expected_release_token_commitment=prepared.manifest["release_token_commitment"],
    )
    return schema.canonical_sha256(marker) == release_sha256


def evaluate_start_acks(
    prepared: PreparedGroup,
    receipts: Mapping[str, NodeReceipt] | Sequence[tuple[Mapping[str, Any], int]],
    received_ns: Mapping[str, int] | None = None, *, release_marker_sha256: str,
    release_published_ns: int,
) -> AckDecision:
    submission = _complete_submission(prepared)
    requests = {request["slot_id"]: request for request in submission["requests"]}
    if not isinstance(receipts, Mapping):
        converted: dict[str, NodeReceipt] = {}
        converted_times: dict[str, int] = {}
        duplicate = False
        unknown = False
        for raw, timestamp in receipts:
            slot_id = raw.get("slot_id") if isinstance(raw, Mapping) else None
            if slot_id not in requests:
                unknown = True
                continue
            if slot_id in converted:
                duplicate = True
                continue
            try:
                event = _bound_node_event(prepared, raw, requests[slot_id])
            except (schema.T810SchemaError, T810CoordinatorError):
                continue
            encoded = schema.canonical_json_bytes(event) + b"\n"
            converted[slot_id] = NodeReceipt(
                _node_path(prepared, slot_id), encoded, schema.sha256_bytes(encoded), (event,),
            )
            converted_times[slot_id] = timestamp
        receipts = converted
        received_ns = converted_times
    else:
        duplicate = unknown = False
    if received_ns is None:
        _fail("received_ns is required for file-backed acknowledgements")
    reasons: set[str] = set()
    if duplicate:
        reasons.add("ack_duplicate")
    if unknown:
        reasons.add("ack_unknown_slot")
    latencies: dict[str, int] = {}
    digests: dict[str, str] = {}
    for slot_id in requests:
        receipt = receipts.get(slot_id)
        if receipt is None:
            reasons.add("ack_missing")
            continue
        events = {event["event"]: event for event in receipt.events}
        event = events.get("start_ack")
        if event is None:
            terminal = events.get("terminal")
            if terminal is not None:
                reasons.update(terminal["payload"]["reason_codes"])
            else:
                reasons.add("ack_missing")
            continue
        timestamp = received_ns.get(slot_id)
        if (isinstance(timestamp, bool) or not isinstance(timestamp, int)
                or timestamp < release_published_ns):
            reasons.add("release_marker_mismatch")
            continue
        payload = event["payload"]
        if payload["release_marker_sha256"] != release_marker_sha256:
            reasons.add("release_marker_mismatch")
        if not payload["cancel_marker_absent"]:
            reasons.add("cancel_marker_observed")
        scan = payload["pre_measurement_process_scan"]
        if scan["competing_processes"]:
            reasons.add("competing_process_detected")
        if scan["unreadable"]:
            reasons.add("process_observation_unreadable")
        latencies[slot_id] = timestamp - release_published_ns
        digests[slot_id] = receipt.sha256
    if len(latencies) != schema.NODE_COUNT:
        reasons.add("ack_missing")
    spread = max(latencies.values(), default=0)
    if spread > schema.START_SPREAD_MAX_NS:
        reasons.add("start_spread_exceeded")
    return AckDecision(not reasons, tuple(sorted(reasons)), spread, latencies, digests)


def _presence_for_state(
    preregistration: VerifiedT810Preregistration, state: str,
    completed: set[str], reached: set[str], started: set[str] | None = None,
) -> dict[str, list[str]]:
    artifacts = preregistration.projection["artifacts"]
    matrix = artifacts["presence_matrix"][state]
    slots = [f"slot-{index:02d}" for index in range(schema.NODE_COUNT)]
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


def _actual_slot_presence(prepared: PreparedGroup) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for index in range(schema.NODE_COUNT):
        slot = f"slot-{index:02d}"
        root = prepared.output_root / slot
        try:
            entries = list(root.iterdir())
        except OSError as exc:
            raise T810CoordinatorError(f"cannot inspect {slot} presence") from exc
        paths: list[str] = []
        for entry in entries:
            info = entry.lstat()
            if not stat.S_ISREG(info.st_mode) or entry.is_symlink():
                _fail(f"{slot} contains a non-regular artifact")
            paths.append(f"{slot}/{entry.name}")
        result[slot] = sorted(paths)
    return result


def _expected_root_presence(prepared: PreparedGroup, state: str) -> list[str]:
    artifacts = prepared.preregistration.projection["artifacts"]
    expected_files = set(artifacts["root"]["always_files"])
    if state in {"valid", "terminal_reduced"}:
        expected_files.add(artifacts["root"]["conditional_estimate_file"])
    expected_directories = {f"slot-{index:02d}" for index in range(schema.NODE_COUNT)}
    return sorted(
        [f"files/{name}" for name in expected_files]
        + [f"directories/{name}" for name in expected_directories]
    )


def _actual_root_presence(prepared: PreparedGroup) -> list[str]:
    actual: list[str] = []
    try:
        entries = list(prepared.output_root.iterdir())
    except OSError as exc:
        raise T810CoordinatorError("cannot inspect group-root presence") from exc
    for entry in entries:
        info = entry.lstat()
        if entry.is_symlink():
            kind = "symlinks"
        elif stat.S_ISREG(info.st_mode):
            kind = "files"
        elif stat.S_ISDIR(info.st_mode):
            kind = "directories"
        else:
            kind = "other"
        actual.append(f"{kind}/{entry.name}")
    # terminal-state is the immediately following create-only publication.
    if not prepared.terminal_path.exists():
        actual.append(f"files/{prepared.terminal_path.name}")
    return sorted(actual)


def _add_root_presence(
    prepared: PreparedGroup, state: str,
    expected: dict[str, list[str]], actual: dict[str, list[str]],
) -> None:
    expected["group-root"] = _expected_root_presence(prepared, state)
    actual["group-root"] = _actual_root_presence(prepared)


def _terminal_limitations(prepared: PreparedGroup, receipts: Mapping[str, NodeReceipt]) -> list[str]:
    values = set(prepared.limitations)
    for receipt in receipts.values():
        for event in receipt.events:
            values.update(name for name, present in event["limitations"].items() if present)
    return sorted(values)


def verify_completion(
    prepared: PreparedGroup, receipts: Mapping[str, NodeReceipt], *,
    release_event_sha256: str, start_spread_ns: int,
    pre_validator_receipt_sha256: str, post_validator_receipt_sha256: str,
) -> Mapping[str, Any]:
    submission = _complete_submission(prepared)
    requests = {request["slot_id"]: request for request in submission["requests"]}
    if set(receipts) != set(requests):
        _fail("completion requires one file-backed terminal receipt per slot")
    completed: set[str] = set()
    started: set[str] = set()
    integrity_reasons: set[str] = set()
    terminal_by_slot: dict[str, Mapping[str, Any]] = {}
    receipt_hashes: dict[str, str] = {}
    for slot_id, receipt in receipts.items():
        if receipt.events[-1]["event"] != "terminal":
            _fail(f"{slot_id} node receipt is not terminal")
        terminal = receipt.events[-1]
        terminal_by_slot[slot_id] = terminal
        receipt_hashes[slot_id] = receipt.sha256
        output_receipt = _read_regular_bytes(
            prepared.output_root / slot_id / _NODE_RECEIPT_NAME,
            f"{slot_id} preserved node receipt",
        )
        if output_receipt != receipt.raw:
            _fail(f"{slot_id} preserved node receipt differs from monitored bytes")

    # C-6: state 1/2/3 is aggregated before any completion-count reduction.
    priority = [
        "pre_release_invalid", "post_release_pre_measurement_invalid",
        "incomplete_after_start",
    ]
    selected_failure = next((
        state for state in priority
        if any(event["payload"]["state"] == state for event in terminal_by_slot.values())
    ), None)
    if selected_failure is not None:
        reasons = {
            reason for event in terminal_by_slot.values()
            if event["payload"]["state"] == selected_failure
            for reason in event["payload"]["reason_codes"]
        }
        state = selected_failure
    else:
        reasons = set()
        state = "valid"

    for slot_id, receipt in receipts.items():
        events = {event["event"]: event for event in receipt.events}
        terminal_payload = terminal_by_slot[slot_id]["payload"]
        measurement = events.get("measurement")
        if terminal_payload["measurement_started"]:
            started.add(slot_id)
        # A terminal_reduced dropout keeps its artifacts for presence auditing,
        # but protocol section 5.4 excludes it from completed-job integrity.
        if terminal_payload["state"] != "valid":
            continue
        if measurement is None:
            integrity_reasons.add("completed_rounds_missing")
            continue
        payload = measurement["payload"]
        rounds = payload["rounds"]
        if (terminal_payload["completed_rounds"] != schema.ROUND_COUNT
                or len(rounds) != schema.ROUND_COUNT or payload["benchmark_rc"] != 0
                or any(item["exit_code"] != 0 for item in rounds)):
            integrity_reasons.add("completed_rounds_missing")
            continue
        slot = prepared.launch_intent["slots"][int(slot_id[-2:])]
        if payload["binary_after_sha256"] != slot["binary_sha256"]:
            integrity_reasons.add("binary_after_hash_mismatch")
            continue
        completed.add(slot_id)

    if selected_failure is None:
        if integrity_reasons:
            state, reasons = "incomplete_after_start", integrity_reasons
        elif len(completed) <= schema.NODE_COUNT - 2:
            state, reasons = "incomplete_after_start", {"insufficient_completions"}
        elif len(completed) == schema.NODE_COUNT - 1:
            noncomplete = set(requests) - completed
            if all(
                terminal_by_slot[slot]["payload"]["state"] == "terminal_reduced"
                and terminal_by_slot[slot]["payload"]["reason_codes"] == ["single_job_dropped"]
                for slot in noncomplete
            ):
                state, reasons = "terminal_reduced", {"single_job_dropped"}
            else:
                state, reasons = "incomplete_after_start", {"completed_rounds_missing"}
        elif len(completed) == schema.NODE_COUNT:
            state, reasons = "valid", {"all_jobs_complete"}

    terminal_completed = completed
    if state in {"pre_release_invalid", "post_release_pre_measurement_invalid"}:
        terminal_completed = set()
    expected_presence = _presence_for_state(
        prepared.preregistration, state, terminal_completed, set(receipts), started,
    )
    actual_presence = _actual_slot_presence(prepared)
    _add_root_presence(prepared, state, expected_presence, actual_presence)
    presence_valid = expected_presence == actual_presence
    if not presence_valid and state in {"valid", "terminal_reduced"}:
        state, reasons = "incomplete_after_start", {"presence_matrix_mismatch"}
        expected_presence = _presence_for_state(
            prepared.preregistration, state, completed, set(receipts), started,
        )
        _add_root_presence(prepared, state, expected_presence, actual_presence)
        presence_valid = expected_presence == actual_presence
    slots = list(requests)
    value = {
        "schema_version": schema.TERMINAL_STATE_SCHEMA,
        "group_manifest_sha256": prepared.manifest_sha256,
        "attempt_ordinal": prepared.launch_intent["attempt_ordinal"], "state": state,
        "reason_codes": sorted(reasons), "release_event_sha256": release_event_sha256,
        "start_spread_ns": start_spread_ns,
        "completed_slot_ids": sorted(terminal_completed),
        "dropped_slot_ids": sorted(set(slots) - terminal_completed),
        "node_receipt_sha256_by_slot": receipt_hashes,
        "expected_presence": expected_presence, "actual_presence": actual_presence,
        "presence_valid": presence_valid,
        "pre_validator_receipt_sha256": pre_validator_receipt_sha256,
        "post_validator_receipt_sha256": post_validator_receipt_sha256,
        "retry_allowed": schema.retry_allowed(state, prepared.launch_intent["attempt_ordinal"]),
        "limitations": _terminal_limitations(prepared, receipts),
    }
    return schema.validate_terminal_state(value)


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
            result=result, attempt_nonce=validator_kwargs["attempt_nonce"],
            invocation_nonce=validator_kwargs["pre_invocation_nonce"], phase="pre",
        )
        return BaselineEnvelope(result.baseline, result.baseline_digest, result.lineage, digest)
    except (KeyError, TypeError, ValueError):
        return None


def _run_validator(
    validator: Validator, preregistration: VerifiedT810Preregistration,
    validator_kwargs: Mapping[str, Any], *, claimed_state: str,
    previous_baseline: BaselineEnvelope | None,
) -> Any:
    kwargs = dict(validator_kwargs)
    kwargs.update({
        "preregistration": preregistration, "claimed_state": claimed_state,
        "previous_baseline": previous_baseline,
    })
    return validator(**kwargs)


def _early_terminal(
    prepared: PreparedGroup, state: str, reasons: Sequence[str], *,
    release_sha256: str | None, spread_ns: int | None,
    receipts: Mapping[str, NodeReceipt], pre_digest: str, post_digest: str,
) -> Mapping[str, Any]:
    slots = [f"slot-{index:02d}" for index in range(schema.NODE_COUNT)]
    expected = _presence_for_state(prepared.preregistration, state, set(), set(receipts))
    actual = _actual_slot_presence(prepared)
    _add_root_presence(prepared, state, expected, actual)
    receipt_map = {slot: receipts[slot].sha256 if slot in receipts else None for slot in slots}
    if state != "pre_release_invalid" and any(value is None for value in receipt_map.values()):
        _fail("post-release terminal state lacks an exact node receipt")
    value = {
        "schema_version": schema.TERMINAL_STATE_SCHEMA,
        "group_manifest_sha256": prepared.manifest_sha256,
        "attempt_ordinal": prepared.launch_intent["attempt_ordinal"], "state": state,
        "reason_codes": list(reasons), "release_event_sha256": release_sha256,
        "start_spread_ns": spread_ns, "completed_slot_ids": [], "dropped_slot_ids": slots,
        "node_receipt_sha256_by_slot": receipt_map,
        "expected_presence": expected, "actual_presence": actual,
        "presence_valid": expected == actual,
        "pre_validator_receipt_sha256": pre_digest,
        "post_validator_receipt_sha256": post_digest,
        "retry_allowed": schema.retry_allowed(state, prepared.launch_intent["attempt_ordinal"]),
        "limitations": _terminal_limitations(prepared, receipts),
    }
    return schema.validate_terminal_state(value)


def _coordinate_authorized(
    config: Mapping[str, Any], preregistration: VerifiedT810Preregistration,
    authorization: schema.AuthorizationToken, *, scheduler_run: SchedulerRun,
    clock_ns: Clock, sleep: Sleeper, wall_clock: WallClock, validator: Validator,
    repository_roots: Sequence[Path],
) -> CoordinationResult:
    document = decode_config(config)
    prepared = prepare_group(
        document, preregistration, authorization, repository_roots=repository_roots,
    )
    initial_ns = clock_ns()
    _append_coordinator_event(
        prepared, authorization, "manifest_committed",
        {"manifest_sha256": prepared.manifest_sha256},
        wall_time=wall_clock(), monotonic_ns=initial_ns,
    )
    validator_kwargs = document["validator_kwargs"]
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
    receipts: Mapping[str, NodeReceipt] = {}
    state = "pre_release_invalid"
    reasons: tuple[str, ...] = ("pre_inventory_mismatch",)
    terminal: Mapping[str, Any] | None = None
    if _validator_ok(pre):
        submission = submit_group(
            prepared, authorization, scheduler_run=scheduler_run, wall_clock=wall_clock,
        )
        ready_receipts, ready_times = _wait_for_phase(
            prepared, "preflight", clock_ns=clock_ns, sleep=sleep,
            timeout_seconds=schema.READY_TIMEOUT_SECONDS,
        )
        receipts = ready_receipts
        elapsed = (max(ready_times.values(), default=initial_ns) - initial_ns) / 1_000_000_000
        barrier = evaluate_ready_barrier(prepared, ready_receipts, elapsed_seconds=elapsed)
        for slot_id, digest in barrier.receipt_sha256_by_slot.items():
            _append_coordinator_event(
                prepared, authorization, "ready_received", {
                    "receipt_sha256": digest, "accepted": barrier.status == "release",
                    "reason_codes": [] if barrier.status == "release" else list(barrier.reason_codes),
                }, wall_time=wall_clock(), monotonic_ns=ready_times[slot_id], slot_id=slot_id,
            )
        if barrier.status != "release":
            reasons = barrier.reason_codes or ("ready_timeout",)
            _, cancel_sha = publish_cancel(
                prepared, authorization, reasons, wall_clock=wall_clock,
            )
            _append_coordinator_event(
                prepared, authorization, "cancel_published", {
                    "marker_sha256": cancel_sha, "reason_codes": list(reasons),
                }, wall_time=wall_clock(), monotonic_ns=clock_ns(),
            )
        else:
            release_ns = clock_ns()
            _, release_sha = publish_release(
                prepared, authorization, wall_clock=wall_clock,
            )
            _append_coordinator_event(
                prepared, authorization, "release_published",
                {"marker_sha256": release_sha},
                wall_time=wall_clock(), monotonic_ns=release_ns,
            )
            ack_receipts, ack_times = _wait_for_phase(
                prepared, "start_ack", clock_ns=clock_ns, sleep=sleep,
                timeout_seconds=schema.READY_TIMEOUT_SECONDS,
            )
            receipts = ack_receipts
            ack = evaluate_start_acks(
                prepared, ack_receipts, ack_times,
                release_marker_sha256=release_sha, release_published_ns=release_ns,
            )
            spread = ack.spread_ns
            for slot_id, digest in ack.receipt_sha256_by_slot.items():
                _append_coordinator_event(
                    prepared, authorization, "start_ack_received", {
                        "receipt_sha256": digest, "received_monotonic_ns": ack_times[slot_id],
                        "latency_ns": ack.latency_ns_by_slot[slot_id],
                        "accepted": ack.accepted, "reason_codes": list(ack.reason_codes),
                    }, wall_time=wall_clock(), monotonic_ns=ack_times[slot_id], slot_id=slot_id,
                )
            if not ack.accepted:
                state, reasons = "post_release_pre_measurement_invalid", ack.reason_codes
                _, cancel_sha = publish_cancel(
                    prepared, authorization, reasons, wall_clock=wall_clock,
                )
                _append_coordinator_event(
                    prepared, authorization, "cancel_published", {
                        "marker_sha256": cancel_sha, "reason_codes": list(reasons),
                    }, wall_time=wall_clock(), monotonic_ns=clock_ns(),
                )
            else:
                if not release_is_still_active(prepared, release_sha):
                    _fail("release marker changed before completion wait")
                terminal_receipts, terminal_times = _wait_for_phase(
                    prepared, "terminal", clock_ns=clock_ns, sleep=sleep,
                    timeout_seconds=schema.READY_TIMEOUT_SECONDS,
                )
                if len(terminal_receipts) != schema.NODE_COUNT:
                    _fail("terminal node receipt timeout")
                receipts = terminal_receipts
                placeholder = schema.canonical_sha256({"post-validator": "pending"})
                terminal = verify_completion(
                    prepared, terminal_receipts, release_event_sha256=release_sha,
                    start_spread_ns=spread, pre_validator_receipt_sha256=pre_digest,
                    post_validator_receipt_sha256=placeholder,
                )
                state, reasons = terminal["state"], tuple(terminal["reason_codes"])
                for slot_id, receipt in terminal_receipts.items():
                    _append_coordinator_event(
                        prepared, authorization, "completion_received", {
                            "receipt_sha256": receipt.sha256,
                            "accepted": state in {"valid", "terminal_reduced"},
                            "reason_codes": [] if state in {"valid", "terminal_reduced"}
                            else list(reasons),
                        }, wall_time=wall_clock(), monotonic_ns=terminal_times[slot_id],
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
            receipts=receipts, pre_digest=pre_digest, post_digest=post_digest,
        )
    else:
        terminal = dict(terminal)
        terminal["post_validator_receipt_sha256"] = post_digest
        if not _validator_ok(post) and terminal["state"] in {"valid", "terminal_reduced"}:
            terminal["state"] = "incomplete_after_start"
            terminal["reason_codes"] = ["post_inventory_mismatch"]
            terminal["retry_allowed"] = False
        terminal = schema.validate_terminal_state(terminal)
    _append_coordinator_event(
        prepared, authorization, "terminal_decided", {
            "terminal_state_sha256": schema.canonical_sha256(terminal),
        }, wall_time=wall_clock(), monotonic_ns=clock_ns(),
    )
    _write_create_only(authorization, prepared.terminal_path, terminal)
    return CoordinationResult(prepared, submission, terminal)


def coordinate(
    config: Mapping[str, Any], preregistration: VerifiedT810Preregistration,
    witness: Mapping[str, Any] | None,
) -> CoordinationResult:
    document = decode_config(config)
    policy, policy_sha256 = load_admission_policy(document["admission_policy_path"])
    _require_fully_ratified(policy)
    intent = document["launch_intent"]
    if intent["policy_sha256"] != policy_sha256:
        _fail("launch intent policy digest mismatch")
    token = _authorization_token(
        witness, preregistration=preregistration, policy_sha256=policy_sha256,
        run_kind=intent["run_kind"],
    )
    roots = repository_roots_from_git_identity(
        document["validator_kwargs"]["approved_git_identity"],
    )
    return _coordinate_authorized(
        document, preregistration, token, scheduler_run=_subprocess_scheduler,
        clock_ns=time.monotonic_ns, sleep=time.sleep,
        wall_clock=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        validator=validate_t810, repository_roots=roots,
    )


def _subprocess_scheduler(
    token: schema.AuthorizationToken, prepared: PreparedGroup, argv: Sequence[str], *, cwd: str,
    env: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    if not isinstance(token, schema.AuthorizationToken):
        _fail("AuthorizationToken is required by subprocess scheduler")
    if not isinstance(prepared, PreparedGroup):
        _fail("PreparedGroup is required by subprocess scheduler")
    selected = next((
        slot for slot in prepared.launch_intent["slots"]
        if tuple(argv) == _canonical_qsub_argv(
            slot, policy=prepared.admission_policy,
            run_kind=prepared.launch_intent["run_kind"],
        )
    ), None)
    if selected is None or cwd != str(prepared.work_root) or env:
        _fail("subprocess scheduler inputs are not the prepared canonical submission")
    _assert_canonical_job_script(selected)
    _assert_staged_file_identities(selected)
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
        approval = _exact(
            _load_cli_json(args.approval_receipt, "approval receipt"),
            {"artifact_sha256", "approval_id", "schema_version"}, "approval receipt",
        )
        preregistration = load_t810_preregistration(
            Path(args.preregistration),
            approval_receipt=ApprovalReceipt(
                artifact_sha256=approval["artifact_sha256"],
                approval_id=approval["approval_id"],
                schema_version=approval["schema_version"],
            ),
        )
        config = decode_config(_load_cli_json(args.config, "coordinator config"))
        witness = _load_cli_json(args.authorization_witness, "launch authorization witness")
        coordinate(config, preregistration, witness)
    except (KeyError, OSError, TypeError, ValueError, T810CoordinatorError):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
