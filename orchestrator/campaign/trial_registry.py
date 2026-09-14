# -*- coding: utf-8 -*-
"""Phase 3 8c trial manifest registration and acceptance gates.

The v2 receipt projects the execution binding already checked against report,
run-start, historical input derivation, and cell descriptor bytes.  Approval
authority remains unresolved, so acceptance is still structurally
non-certifying.
"""
from __future__ import annotations

import argparse
import dataclasses
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import threading
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath as _PurePosixPath
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from .autonomous_trial_completeness import (
    AutonomousTrialCompletenessError,
    assert_campaign_layer3_chain,
    assert_autonomous_trial_completeness,
    assert_execution_digest_chain,
    is_exact_campaignless_failure_fallback_cell,
    is_exact_cell_admission_failure_decision,
    verify_s8c_cross_binding,
)
from ..holdout_observation import HoldoutCondition
from . import s8b_holdout_freeze
from . import s8c_preregistration
from . import s8c_acceptance_receipt
from . import s8c_arm_inputs
from . import attempt_registry_core as _attempt_core

if TYPE_CHECKING:
    from .reflux_formal_consumer import OriginTerminalProjection
    from .reflux_origin_binding import OriginBindingCapability




MANIFEST_SCHEMA_VERSION = "p3-8c-trial-manifest/v2"
REGISTRATION_SCHEMA_VERSION = "p3-8c-trial-registration/v2"
DEFAULT_REGISTRY_PATH = Path("output/s8c-trial-registry/registry.jsonl")
DEFAULT_EFFECTIVE_BINDING_PATH = Path(
    "output/s8c-preregistration/prereg-effective-binding.v1.json"
)
DEFAULT_ATTEMPT_REGISTRY_PATH = Path(
    "output/s8c-preregistration/attempt-registry.jsonl"
)
_ATTEMPT_REGISTRY_SCHEMA_VERSION_V1 = "p3-8c-attempt-registry/v1"
_ATTEMPT_REGISTRY_SCHEMA_VERSION_V2 = "p3-8c-attempt-registry/v2"
ATTEMPT_REGISTRY_SCHEMA_VERSION = "p3-8c-attempt-registry/v3"
_ATTEMPT_REGISTRY_SCHEMA_VERSIONS = frozenset({
    _ATTEMPT_REGISTRY_SCHEMA_VERSION_V1,
    _ATTEMPT_REGISTRY_SCHEMA_VERSION_V2,
    ATTEMPT_REGISTRY_SCHEMA_VERSION,
})
EFFECTIVE_BINDING_SCHEMA_VERSION = "p3-8c-prereg-effective-binding/v1"
DEFAULT_LIFECYCLE_PATH = Path("output/s8c-trial-registry/lifecycle.jsonl")
LIFECYCLE_SCHEMA_VERSION = "p3-8c-trial-lifecycle/v2"
ARMS = ("on", "off", "swapped")
HOLDOUTS = ("H1", "H2")
REGISTERED_FORMAL_NON_CERTIFYING_MODE = "registered-formal-non-certifying"
A1_NON_CERTIFYING_WORKLOADS = (
    "write-heavy", "balanced", "read-heavy",
)


def _holdout_bindings_from_freeze() -> Mapping[str, Mapping[str, str | int]]:
    bindings: dict[str, Mapping[str, str | int]] = {}
    for workload, frozen in s8b_holdout_freeze.HOLDOUTS.items():
        ycsb = frozen["ycsb"]
        condition = HoldoutCondition(
            candidate_id=frozen["candidate_id"],
            ycsb_zipf_skew=ycsb[s8b_holdout_freeze.SKEW_KEY],
            ycsb_rratio=ycsb[s8b_holdout_freeze.RRATIO_KEY],
            ycsb_rmw=ycsb[s8b_holdout_freeze.RMW_KEY],
            records=frozen["records"],
            threads=frozen["threads"],
        )
        bindings[condition.candidate_id] = MappingProxyType({
            "workload": workload,
            "ycsb_zipf_skew": condition.ycsb_zipf_skew,
            "ycsb_rratio": condition.ycsb_rratio,
            "ycsb_rmw": condition.ycsb_rmw,
            "records": condition.records,
            "threads": condition.threads,
        })
    return MappingProxyType(bindings)


HOLDOUT_BINDINGS: Mapping[str, Mapping[str, str | int]] = (
    _holdout_bindings_from_freeze()
)
HOLDOUT_WORKLOADS = frozenset(
    binding["workload"] for binding in HOLDOUT_BINDINGS.values()
)

_TRIAL_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_MANIFEST_KEYS = frozenset({"schema_version", "prereg_commit", "trials"})
_TRIAL_KEYS = frozenset({
    "trial_id", "arm", "holdout", "campaign_id", "generations",
})
_REGISTRATION_KEYS = frozenset({
    "schema_version", "manifest_sha256", "prereg_commit",
    "prereg_content_commit", "prereg_effective_commit", "trials",
})
_EFFECTIVE_BINDING_KEYS = frozenset({
    "schema_version", "prereg_content_commit", "manifest_path",
    "manifest_sha256", "freeze_id", "attempt_registry_path",
    "attempt_registry_initial_sha256",
})
_TRIAL_BINDING_SEAL = object()
_TRIAL_ARM_EXECUTION_SEAL = object()
_TRIAL_LAUNCH_ADMISSION_SEAL = object()
_TRIAL_LIFECYCLE_TOKEN_SEAL = object()
_ATTEMPT_SLOT_CAPABILITY_SEAL = object()
_A1_NON_CERTIFYING_PROJECTION_SEAL = object()

ATTEMPT_STATUSES = (
    "observed", "retryable-failure", "terminal-failure", "not-consumed",
)
ATTEMPT_RETRYABLE_FAILURE_REASONS = frozenset({
    "preempted", "wall-timeout", "node-failure", "launcher-failure",
})
_ATTEMPT_V1_GENESIS_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "manifest_path",
    "manifest_sha256", "root_path", "retryable_failure_reasons", "slots",
})
_ATTEMPT_V1_V2_SLOT_KEYS = frozenset({
    "slot_id", "trial_id", "arm", "holdout", "campaign_id",
    "replicate_index", "attempt_index", "schedule_row_sha256",
})
_ATTEMPT_SLOT_KEYS = _ATTEMPT_V1_V2_SLOT_KEYS | {"prereg_generation"}
_ATTEMPT_CHAIN_KEYS = frozenset({
    "event_index", "previous_event_sha256", "event_sha256",
})
_ATTEMPT_V1_START_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "prereg_content_commit", "prereg_effective_commit",
    "run_start_receipt_sha256", "process_identity", "schedule_row_sha256",
    "started_at",
})
_ATTEMPT_V1_CLASSIFICATION_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "prereg_content_commit", "prereg_effective_commit",
    "classification_receipt_sha256", "capability_digest_sha256",
    "authority_id", "authority_policy_sha256", "external_evidence_sha256",
    "classified_at", "failure_reason", "performance_output_read",
})
_ATTEMPT_V1_TERMINAL_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "prereg_content_commit", "prereg_effective_commit",
    "classification_receipt_sha256", "terminal_status", "raw_output_sha256",
    "report_sha256", "observation_sha256", "primary_value", "failure_reason",
    "finished_at", "schedule_row_sha256", "process_identity",
})
_ATTEMPT_GENESIS_KEYS = _ATTEMPT_V1_GENESIS_KEYS | _ATTEMPT_CHAIN_KEYS
_ATTEMPT_START_KEYS = _ATTEMPT_V1_START_KEYS | _ATTEMPT_CHAIN_KEYS
_ATTEMPT_PRE_OBSERVATION_SEAL_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "start_event_sha256", "run_start_receipt_sha256", "process_identity",
    "schedule_row_sha256",
}) | _ATTEMPT_CHAIN_KEYS
_ATTEMPT_CLASSIFICATION_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "prereg_content_commit", "prereg_effective_commit",
    "classification_receipt_sha256", "capability_digest_sha256",
    "authority_id", "authority_policy_sha256", "external_evidence_sha256",
    "classified_at", "pre_observation_failure_reason",
    "pre_observation_seal_sha256",
}) | _ATTEMPT_CHAIN_KEYS
_ATTEMPT_OBSERVATION_START_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "classification_event_sha256",
}) | _ATTEMPT_CHAIN_KEYS
_ATTEMPT_TERMINAL_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "prereg_content_commit", "prereg_effective_commit",
    "classification_receipt_sha256", "terminal_status", "raw_output_sha256",
    "report_sha256", "observation_sha256", "primary_value", "failure_reason",
    "pre_observation_failure_reason_echo", "observation_start_event_sha256",
    "finished_at", "schedule_row_sha256", "process_identity",
}) | _ATTEMPT_CHAIN_KEYS
_PROCESS_IDENTITY_KEYS = frozenset({
    "pid", "starttime", "execution_uuid",
})
_LIFECYCLE_START_BASE_KEYS = frozenset({
    "schema_version", "event", "trial_id", "run_root", "mode",
    "manifest_sha256", "prereg_commit", "prereg_content_commit",
    "prereg_effective_commit", "measurement_head",
    "activation_report_digest_sha256", "launch_admission_sha256", "slot_id",
    "schedule_row_sha256", "process_identity",
})
_LIFECYCLE_START_KEYS = frozenset({
    _LIFECYCLE_START_BASE_KEYS,
    _LIFECYCLE_START_BASE_KEYS | {"origin_run_plan_sha256"},
})
_LIFECYCLE_TERMINAL_BASE_KEYS = frozenset({
    "schema_version", "event", "trial_id", "terminal_status",
    "report_sha256", "attempt_journal_sha256", "prereg_commit",
    "prereg_content_commit", "prereg_effective_commit", "slot_id",
    "classification_receipt_sha256", "raw_output_sha256",
})
_LIFECYCLE_TERMINAL_KEYS = frozenset({
    _LIFECYCLE_TERMINAL_BASE_KEYS,
    _LIFECYCLE_TERMINAL_BASE_KEYS | {"origin_terminal_projection"},
    _LIFECYCLE_TERMINAL_BASE_KEYS | {"failure_reason"},
})
_ORIGIN_BINDING_KEYS = frozenset({
    "authority_blob_sha256", "source_closure_sha256", "origin_id", "cell_key",
    "authority_workload", "axis_semantics_sha256", "verifier_policy_sha256",
    "environment_contract_sha256", "campaign_id", "trial_workload",
    "measurement_head", "store_scope", "issuer_seal",
})
_LAUNCH_ADMISSION_BASE_KEYS = frozenset({
    "mode", "certifying", "reason_code", "trial_id", "workloads", "binding",
    "activation_report_digest_sha256", "prereg_content_commit",
    "prereg_effective_commit",
})
_LAUNCH_ADMISSION_EXPLORATORY_KEYS = frozenset(
    _LAUNCH_ADMISSION_BASE_KEYS
    - {"prereg_content_commit", "prereg_effective_commit"}
)
_LAUNCH_ADMISSION_KEYS = frozenset({
    _LAUNCH_ADMISSION_BASE_KEYS,
    _LAUNCH_ADMISSION_BASE_KEYS | {"origin_binding"},
    _LAUNCH_ADMISSION_EXPLORATORY_KEYS,
})
_ORIGIN_WORKLOAD_KEYS = frozenset({"descriptor_sha256", "records", "threads"})
_ORIGIN_TERMINAL_PROJECTION_KEYS = frozenset({
    "schema_version", "reason_code", "formal_receipt_sha256",
    "evidence_root_sha256", "authority_blob_sha256", "origin_id", "cell_key",
    "terminal_payload_sha256", "arm_binding_digest_sha256",
})
_FORMAL_REASON_CODES = frozenset({
    "FC01", "FC02", "FC03", "FC04", "FC05a", "FC05b", "FC05c", "FC06",
    "FC07", "FC09", "FC10", "P6Unavailable",
})
_GIT_ENV_ALLOW = frozenset({
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
    "SYSTEMROOT",
    "TMPDIR",
})


class TrialRegistryError(RuntimeError):
    """A fail-closed trial registry gate rejected its input."""


def _fail(gate: str, message: str) -> None:
    raise TrialRegistryError(f"[{gate}] {message}")


@dataclasses.dataclass(frozen=True, slots=True)
class TrialSpec:
    trial_id: str
    arm: str
    holdout: str
    campaign_id: str
    generations: int


@dataclasses.dataclass(frozen=True, slots=True)
class TrialManifest:
    schema_version: str
    prereg_commit: str
    trials: tuple[TrialSpec, ...]
    sha256: str
    raw_bytes: bytes = dataclasses.field(repr=False, compare=False)


@dataclasses.dataclass(frozen=True, slots=True)
class TrialRegistration:
    schema_version: str
    manifest_sha256: str
    prereg_commit: str
    prereg_content_commit: str
    prereg_effective_commit: str
    trials: tuple[TrialSpec, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class PreregEffectiveBinding:
    """The effective-commit record stored in commit C.

    The record deliberately omits C itself.  C is proven from Git as the
    commit containing this blob, so putting C in the blob would create a
    self-reference.  ``raw_bytes`` is an in-memory parser witness and is not
    part of the JSON record.
    """

    schema_version: str
    prereg_content_commit: str
    manifest_path: str
    manifest_sha256: str
    freeze_id: str
    attempt_registry_path: str
    attempt_registry_initial_sha256: str
    raw_bytes: bytes = dataclasses.field(repr=False, compare=False)


@dataclasses.dataclass(frozen=True, slots=True)
class TrialBinding:
    manifest_sha256: str
    prereg_commit: str
    prereg_content_commit: str
    prereg_effective_commit: str
    measurement_head: str
    trial_id: str
    arm: str
    holdout: str
    campaign_id: str
    workload: str
    ycsb_rratio: str
    _seal: object = dataclasses.field(repr=False, compare=False)


@dataclasses.dataclass(frozen=True, slots=True)
class TrialArmExecutionBinding:
    """Registry-issued binding from a declared arm to immutable input bytes."""

    binding: TrialBinding
    resolved_input: s8c_arm_inputs.ResolvedArmInput
    canonical_input_bytes: bytes = dataclasses.field(repr=False)
    input_schema_version: str
    content_digest_sha256: str
    arm_binding_digest_sha256: str
    _seal: object = dataclasses.field(repr=False, compare=False)


@dataclasses.dataclass(frozen=True, slots=True)
class TrialLaunchAdmission:
    mode: Literal[
        "registered-effective",
        "registered-formal-non-certifying",
        "explicit-unregistered-exploratory",
    ]
    certifying: bool
    reason_code: str
    trial_id: str
    workloads: tuple[str, ...]
    binding: TrialBinding | None
    activation_report_digest_sha256: str | None
    _seal: object = dataclasses.field(repr=False, compare=False)


@dataclasses.dataclass(frozen=True, slots=True)
class A1RegisteredNonCertifyingProjection:
    """A-1 producer 専用の sealed registered non-certifying projection。

    この値は supported process 内の型取り違えを防ぐだけで、外部 authority、
    certifying capability、秘密 custody、または別 process の認証を表さない。
    """

    mode: Literal["registered-formal-non-certifying"]
    certifying: bool
    study_id: str
    policy_sha256: str
    preregistration_sha256: str
    source_commit: str
    workloads: tuple[str, ...]
    campaign_ids: tuple[str, ...]
    _seal: object = dataclasses.field(repr=False, compare=False)


@dataclasses.dataclass(frozen=True, slots=True)
class TrialLifecycleToken:
    """単一 lifecycle ledger 内だけの start-once token。

    committed ledger の append-only 履歴は単一 Git repository 内で検査する。
    この token は、同じ ledger と repository history を共有しない別 clone を横断する
    project-global な一回性を保証しない。
    """

    repository_root: Path = dataclasses.field(repr=False, compare=False)
    lifecycle_path: Path
    trial_id: str
    run_root: str
    start_row_sha256: str
    launch_admission_sha256: str
    prereg_content_commit: str
    prereg_effective_commit: str
    slot_id: str
    origin_run_plan_sha256: str | None
    _seal: object = dataclasses.field(repr=False, compare=False)


@dataclasses.dataclass(slots=True)
class _TrialLifecycleCapabilityState:
    token: TrialLifecycleToken
    repository_root: Path
    lifecycle_path: Path
    trial_id: str
    run_root: str
    start_row_sha256: str
    launch_admission_sha256: str
    prereg_content_commit: str
    prereg_effective_commit: str
    slot_id: str
    schedule_row_sha256: str
    process_identity: Mapping[str, Any]
    origin_binding: OriginBindingCapability | None
    origin_run_plan_sha256: str | None
    consumed: bool = False
    started_once: bool = False
    restart_forbidden: bool = False


_TRIAL_LIFECYCLE_CAPABILITIES: dict[int, _TrialLifecycleCapabilityState] = {}
_TRIAL_LIFECYCLE_CAPABILITIES_LOCK = threading.Lock()


@dataclasses.dataclass(frozen=True, slots=True)
class AttemptSlotCapability:
    """Capability issued when a pre-registered slot is reserved.

    The capability binds the slot and all immutable schedule identity to P/C.
    The API that classifies a failure intentionally has no performance-output
    parameter.  The v2 chain proves internal consistency of registered events,
    including tampering and reordering detection, not the OS-level fact that a
    trusted launcher acted before reading independent performance output.
    """

    repository_root: Path = dataclasses.field(repr=False, compare=False)
    registry_path: Path = dataclasses.field(repr=False, compare=False)
    freeze_id: str
    slot_id: str
    trial_id: str
    arm: str
    holdout: str
    campaign_id: str
    prereg_generation: int
    replicate_index: int
    attempt_index: int
    schedule_row_sha256: str
    prereg_commit: str
    prereg_content_commit: str
    prereg_effective_commit: str
    pre_observation_seal_sha256: str
    capability_digest_sha256: str
    _seal: object = dataclasses.field(repr=False, compare=False)
    _classification_receipt_sha256: str | None = dataclasses.field(
        default=None, init=False, repr=False, compare=False,
    )
    _classification_owner: tuple[int, int] | None = dataclasses.field(
        default=None, init=False, repr=False, compare=False,
    )


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptedTrial:
    trial_id: str
    status: str
    measurement_head: str


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptanceSummary:
    manifest_sha256: str
    trials: tuple[AcceptedTrial, ...]
    receipt_path: str
    receipt_sha256: str
    certifying: bool = False
    arm_binding: str = "execution-bound"


@dataclasses.dataclass(slots=True)
class _LoadedReport:
    report: dict[str, Any]
    report_path: Path
    report_bytes: bytes
    journal_path: Path
    journal_fd: int
    journal_bytes: bytes
    events: list[Mapping[str, Any]]

    def assert_snapshot_unchanged(self) -> None:
        info = os.fstat(self.journal_fd)
        current = bytearray()
        offset = 0
        while offset < info.st_size:
            chunk = os.pread(
                self.journal_fd,
                min(1024 * 1024, info.st_size - offset),
                offset,
            )
            if not chunk:
                _fail("journal-snapshot", "journal fd read stopped early")
            current.extend(chunk)
            offset += len(chunk)
        if bytes(current) != self.journal_bytes:
            _fail("journal-snapshot", "journal fd bytes changed during acceptance")
        try:
            rebound = self.journal_path.stat()
        except OSError as exc:
            raise TrialRegistryError(
                "[journal-snapshot] journal path disappeared during acceptance"
            ) from exc
        if (rebound.st_dev, rebound.st_ino) != (info.st_dev, info.st_ino):
            _fail("journal-snapshot", "journal path changed during acceptance")

    def close(self) -> None:
        os.close(self.journal_fd)


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TrialRegistryError(f"[json] value is not canonical JSON: {exc}") from exc


_ATTEMPT_ZERO_SHA256 = "0" * 64


def _attempt_event_sha256(row: Mapping[str, Any]) -> str:
    """Hash one attempt event using this module's canonical JSON contract."""
    return _attempt_core_call(_attempt_core.event_sha256, row)


def _attempt_v2_event_row(
    row: Mapping[str, Any],
    *,
    event_index: int,
    previous_event_sha256: str,
) -> dict[str, Any]:
    """Attach and calculate the v2 chain fields for one event row."""
    return _attempt_core_call(
        _attempt_core.chained_event_row,
        row,
        event_index=event_index,
        previous_event_sha256=previous_event_sha256,
    )


def _attempt_v2_previous_hash(rows: Sequence[Mapping[str, Any]]) -> str:
    """Return the current v2 chain tip, or the genesis zero hash."""
    return _attempt_core.previous_event_sha256(rows)


def _attempt_pre_observation_seal_payload(
    start: Mapping[str, Any],
    *,
    freeze_id: str,
    slot_id: str,
) -> dict[str, Any]:
    """Build the seal from verified start evidence, not caller-supplied state.

    The resulting row participates in internal consistency checks for
    tampering and reordering.  It does not prove at the OS level that a
    trusted launcher acted before reading an independent external fact.
    """
    return {
        "schema_version": ATTEMPT_REGISTRY_SCHEMA_VERSION,
        "event": "pre-observation-seal",
        "freeze_id": freeze_id,
        "slot_id": slot_id,
        "start_event_sha256": start["event_sha256"],
        "run_start_receipt_sha256": start["run_start_receipt_sha256"],
        "process_identity": dict(start["process_identity"]),
        "schedule_row_sha256": start["schedule_row_sha256"],
    }


def _reject_constant(value: str) -> None:
    _fail("json", f"non-finite JSON number is forbidden: {value}")


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("json", f"duplicate object key: {key!r}")
        result[key] = value
    return result


def _decode_json(data: bytes, *, label: str) -> Any:
    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except TrialRegistryError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail("json", f"{label} is not strict UTF-8 JSON: {exc}")


def _read_regular_bytes(path: Path, *, gate: str, label: str) -> bytes:
    path = Path(path)
    try:
        before = path.lstat()
    except OSError as exc:
        raise TrialRegistryError(f"[{gate}] {label} cannot be stated: {path}") from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        _fail(gate, f"{label} must be a regular non-symlink file: {path}")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
        try:
            opened = os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode):
                _fail(gate, f"{label} changed away from a regular file: {path}")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            after = os.fstat(fd)
        finally:
            os.close(fd)
    except TrialRegistryError:
        raise
    except OSError as exc:
        raise TrialRegistryError(f"[{gate}] {label} cannot be read: {path}") from exc
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after:
        _fail(gate, f"{label} changed while it was being read: {path}")
    return b"".join(chunks)


def _exact_keys(value: Mapping[str, Any], expected: frozenset[str], *, label: str) -> None:
    actual = frozenset(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        _fail("schema", f"{label} key set differs: missing={missing}, unknown={unknown}")


def _validate_origin_binding_record(
    record: object,
    *,
    trial: TrialSpec | None = None,
    measurement_head: str | None = None,
    gate: str,
) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        _fail(gate, "origin_binding must be a non-null object")
    if frozenset(record) != _ORIGIN_BINDING_KEYS:
        _fail(gate, "origin_binding exact keys differ")
    workload = record.get("authority_workload")
    if not isinstance(workload, Mapping) or frozenset(workload) != _ORIGIN_WORKLOAD_KEYS:
        _fail(gate, "origin authority_workload exact keys differ")
    for field in (
        "authority_blob_sha256", "source_closure_sha256",
        "axis_semantics_sha256", "verifier_policy_sha256",
        "environment_contract_sha256",
    ):
        value = record.get(field)
        if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
            _fail(gate, f"origin_binding {field} is invalid")
    descriptor = workload.get("descriptor_sha256")
    if type(descriptor) is not str or _SHA256_RE.fullmatch(descriptor) is None:
        _fail(gate, "origin authority descriptor is invalid")
    for field in ("records", "threads"):
        value = workload.get(field)
        if type(value) is not int or value < 1:
            _fail(gate, f"origin authority {field} is invalid")
    for field in ("origin_id", "cell_key", "campaign_id", "trial_workload"):
        value = record.get(field)
        if type(value) is not str or not value:
            _fail(gate, f"origin_binding {field} is invalid")
    commit = record.get("measurement_head")
    if type(commit) is not str or _COMMIT_RE.fullmatch(commit) is None:
        _fail(gate, "origin_binding measurement_head is invalid")
    if (
        record.get("store_scope") != "fixture"
        or record.get("issuer_seal") != "launch-admission-gate/v1"
    ):
        _fail(gate, "origin_binding issuer projection is invalid")
    if trial is not None:
        expected_workload = HOLDOUT_BINDINGS[trial.holdout]["workload"]
        if (
            record.get("campaign_id") != trial.campaign_id
            or record.get("trial_workload") != expected_workload
        ):
            _fail(gate, "origin_binding differs from the registered trial")
    if measurement_head is not None and commit != measurement_head:
        _fail(gate, "origin_binding measurement_head differs from the report")
    return dict(record)


def _validate_origin_terminal_projection(
    value: object,
    *,
    gate: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail(gate, "origin_terminal_projection must be an object")
    if frozenset(value) != _ORIGIN_TERMINAL_PROJECTION_KEYS:
        _fail(gate, "origin_terminal_projection exact keys differ")
    reason = value.get("reason_code")
    if reason not in _FORMAL_REASON_CODES:
        _fail(gate, "origin terminal reason_code is outside the closed set")
    rejected = reason != "P6Unavailable"
    for field in ("formal_receipt_sha256", "evidence_root_sha256"):
        digest = value.get(field)
        if rejected:
            if digest is not None:
                _fail(gate, f"rejected origin terminal {field} must be null")
        elif type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
            _fail(gate, f"P6Unavailable origin terminal {field} is invalid")
    for field in (
        "authority_blob_sha256",
        "terminal_payload_sha256",
        "arm_binding_digest_sha256",
    ):
        digest = value.get(field)
        if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
            _fail(gate, f"origin terminal {field} is invalid")
    for field in ("origin_id", "cell_key"):
        token = value.get(field)
        if type(token) is not str or not token:
            _fail(gate, f"origin terminal {field} is invalid")
    if value.get("schema_version") != "OriginTerminalProjection/v1":
        _fail(gate, "origin terminal schema_version is invalid")
    return dict(value)


def _parse_trials(
    value: Any,
    *,
    label: str,
    require_canonical_order: bool = False,
) -> tuple[TrialSpec, ...]:
    if not isinstance(value, list):
        _fail("schema", f"{label} must be an array")
    if len(value) != 6:
        _fail("trial-universe", f"{label} must contain exactly 6 trials")
    trials: list[TrialSpec] = []
    for index, raw_trial in enumerate(value):
        if not isinstance(raw_trial, Mapping):
            _fail("schema", f"{label}[{index}] must be an object")
        _exact_keys(raw_trial, _TRIAL_KEYS, label=f"{label}[{index}]")
        trial_id = raw_trial["trial_id"]
        arm = raw_trial["arm"]
        holdout = raw_trial["holdout"]
        campaign_id = raw_trial["campaign_id"]
        generations = raw_trial["generations"]
        if not isinstance(trial_id, str) or _TRIAL_ID_RE.fullmatch(trial_id) is None:
            _fail("field", f"{label}[{index}].trial_id is not lexically valid")
        if not isinstance(arm, str) or arm not in ARMS:
            _fail("field", f"{label}[{index}].arm is outside the closed set")
        if not isinstance(holdout, str) or holdout not in HOLDOUTS:
            _fail("field", f"{label}[{index}].holdout is outside the closed set")
        if not isinstance(campaign_id, str) or not campaign_id:
            _fail("field", f"{label}[{index}].campaign_id must be a non-empty string")
        if not (type(generations) is int and generations == 2):
            _fail("field", f"{label}[{index}].generations must be the integer 2")
        trials.append(TrialSpec(trial_id, arm, holdout, campaign_id, generations))
    if len({item.trial_id for item in trials}) != len(trials):
        _fail("uniqueness", f"{label} reuses a trial_id")
    if len({item.campaign_id for item in trials}) != len(trials):
        _fail("uniqueness", f"{label} reuses a campaign_id")
    expected_universe = {(holdout, arm) for holdout in HOLDOUTS for arm in ARMS}
    actual_universe = {(item.holdout, item.arm) for item in trials}
    if actual_universe != expected_universe:
        _fail("trial-universe", f"{label} is not the H1/H2 x on/off/swapped product")
    holdout_order = {value: index for index, value in enumerate(HOLDOUTS)}
    arm_order = {value: index for index, value in enumerate(ARMS)}
    canonical = tuple(sorted(
        trials,
        key=lambda item: (holdout_order[item.holdout], arm_order[item.arm]),
    ))
    if require_canonical_order and tuple(trials) != canonical:
        _fail("registration-binding", f"{label} is not in canonical trial order")
    return canonical


def load_trial_manifest(path: Path) -> TrialManifest:
    """Load and validate one exact six-trial preregistration manifest."""
    raw_bytes = _read_regular_bytes(Path(path), gate="manifest-read", label="manifest")
    value = _decode_json(raw_bytes, label="manifest")
    if not isinstance(value, Mapping):
        _fail("schema", "manifest root must be an object")
    _exact_keys(value, _MANIFEST_KEYS, label="manifest")
    if value["schema_version"] != MANIFEST_SCHEMA_VERSION:
        _fail("schema", "manifest schema_version is not supported")
    prereg_commit = value["prereg_commit"]
    if not isinstance(prereg_commit, str) or _COMMIT_RE.fullmatch(prereg_commit) is None:
        _fail("field", "manifest.prereg_commit is not a 40-digit lowercase commit ID")
    trials = _parse_trials(value["trials"], label="manifest.trials")
    return TrialManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        prereg_commit=prereg_commit,
        trials=trials,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        raw_bytes=raw_bytes,
    )


def _trial_dict(trial: TrialSpec) -> dict[str, str | int]:
    return {
        "trial_id": trial.trial_id,
        "arm": trial.arm,
        "holdout": trial.holdout,
        "campaign_id": trial.campaign_id,
        "generations": trial.generations,
    }


def _registration_dict(registration: TrialRegistration) -> dict[str, Any]:
    return {
        "schema_version": registration.schema_version,
        "manifest_sha256": registration.manifest_sha256,
        "prereg_commit": registration.prereg_commit,
        "prereg_content_commit": registration.prereg_content_commit,
        "prereg_effective_commit": registration.prereg_effective_commit,
        "trials": [_trial_dict(trial) for trial in registration.trials],
    }


def _registration_for(
    manifest: TrialManifest,
    *,
    prereg_content_commit: str,
    prereg_effective_commit: str,
) -> TrialRegistration:
    if _COMMIT_RE.fullmatch(prereg_content_commit) is None:
        _fail(
            "registration-binding",
            "prereg_content_commit is not a full lowercase commit ID",
        )
    if _COMMIT_RE.fullmatch(prereg_effective_commit) is None:
        _fail(
            "registration-binding",
            "prereg_effective_commit is not a full lowercase commit ID",
        )
    return TrialRegistration(
        schema_version=REGISTRATION_SCHEMA_VERSION,
        manifest_sha256=manifest.sha256,
        prereg_commit=manifest.prereg_commit,
        prereg_content_commit=prereg_content_commit,
        prereg_effective_commit=prereg_effective_commit,
        trials=manifest.trials,
    )


def _load_registry_bytes(data: bytes, *, label: str) -> tuple[TrialRegistration, ...]:
    if not data or not data.endswith(b"\n"):
        _fail("registry-framing", f"{label} must be non-empty and newline terminated")
    registrations: list[TrialRegistration] = []
    for lineno, line in enumerate(data.splitlines(), 1):
        if not line:
            _fail("registry-framing", f"{label} has a blank line at {lineno}")
        value = _decode_json(line, label=f"{label} line {lineno}")
        if not isinstance(value, Mapping):
            _fail("registry-framing", f"{label} line {lineno} is not an object")
        if _canonical_json_bytes(value) != line:
            _fail("registry-canonical", f"{label} line {lineno} is not canonical JSON")
        _exact_keys(value, _REGISTRATION_KEYS, label=f"{label} line {lineno}")
        if value["schema_version"] != REGISTRATION_SCHEMA_VERSION:
            _fail("schema", f"{label} line {lineno} has an unsupported schema_version")
        manifest_sha256 = value["manifest_sha256"]
        prereg_commit = value["prereg_commit"]
        prereg_content_commit = value["prereg_content_commit"]
        prereg_effective_commit = value["prereg_effective_commit"]
        if not isinstance(manifest_sha256, str) or _SHA256_RE.fullmatch(manifest_sha256) is None:
            _fail("field", f"{label} line {lineno} has an invalid manifest_sha256")
        if not isinstance(prereg_commit, str) or _COMMIT_RE.fullmatch(prereg_commit) is None:
            _fail("field", f"{label} line {lineno} has an invalid prereg_commit")
        if (
            not isinstance(prereg_content_commit, str)
            or _COMMIT_RE.fullmatch(prereg_content_commit) is None
        ):
            _fail("field", f"{label} line {lineno} has an invalid prereg_content_commit")
        if (
            not isinstance(prereg_effective_commit, str)
            or _COMMIT_RE.fullmatch(prereg_effective_commit) is None
        ):
            _fail("field", f"{label} line {lineno} has an invalid prereg_effective_commit")
        registrations.append(TrialRegistration(
            schema_version=REGISTRATION_SCHEMA_VERSION,
            manifest_sha256=manifest_sha256,
            prereg_commit=prereg_commit,
            prereg_content_commit=prereg_content_commit,
            prereg_effective_commit=prereg_effective_commit,
            trials=_parse_trials(
                value["trials"],
                label=f"{label} line {lineno}.trials",
                require_canonical_order=True,
            ),
        ))
    _assert_registry_unique(tuple(registrations))
    return tuple(registrations)


def _assert_registry_unique(registrations: tuple[TrialRegistration, ...]) -> None:
    manifest_hashes: set[str] = set()
    content_commits: set[str] = set()
    effective_commits: set[str] = set()
    trial_ids: set[str] = set()
    campaign_ids: set[str] = set()
    for registration in registrations:
        if registration.manifest_sha256 in manifest_hashes:
            _fail("registry-index", "registry reuses a manifest_sha256")
        manifest_hashes.add(registration.manifest_sha256)
        if registration.prereg_content_commit in content_commits:
            _fail("registry-index", "registry reuses a prereg_content_commit")
        if registration.prereg_effective_commit in effective_commits:
            _fail("registry-index", "registry reuses a prereg_effective_commit")
        content_commits.add(registration.prereg_content_commit)
        effective_commits.add(registration.prereg_effective_commit)
        for trial in registration.trials:
            if trial.trial_id in trial_ids:
                _fail("registry-index", f"registry reuses trial_id {trial.trial_id!r}")
            if trial.campaign_id in campaign_ids:
                _fail("registry-index", f"registry reuses campaign_id {trial.campaign_id!r}")
            trial_ids.add(trial.trial_id)
            campaign_ids.add(trial.campaign_id)


def load_trial_registry(path: Path) -> tuple[TrialRegistration, ...]:
    """Load a canonical, globally unique registration JSONL file."""
    data = _read_regular_bytes(Path(path), gate="registry-read", label="registry")
    return _load_registry_bytes(data, label="registry")


def _git_env() -> dict[str, str]:
    env = {
        key: value for key, value in os.environ.items()
        if key in _GIT_ENV_ALLOW
    }
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_LITERAL_PATHSPECS"] = "1"
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _git(
    repository_root: Path,
    args: Sequence[str],
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", os.fspath(repository_root), *args],
        env=_git_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _repository_root(path: Path) -> Path:
    try:
        root = Path(path).resolve(strict=True)
    except OSError as exc:
        raise TrialRegistryError(f"[repo-path] repository root cannot be resolved: {path}") from exc
    if not root.is_dir():
        _fail("repo-path", f"repository root is not a directory: {root}")
    result = _git(root, ("rev-parse", "--show-toplevel"))
    if result.returncode != 0:
        raise TrialRegistryError("[git] repository root is not a Git work tree")
    try:
        actual = Path(result.stdout.decode("utf-8").strip()).resolve(strict=True)
    except (OSError, UnicodeDecodeError) as exc:
        raise TrialRegistryError("[git] Git returned an invalid repository root") from exc
    if actual != root:
        _fail("repo-path", f"repository_root is not the Git top level: {root}")
    return root


def _repo_relative(path: Path, repository_root: Path, *, label: str) -> tuple[Path, str]:
    try:
        resolved = Path(path).resolve(strict=True)
    except OSError as exc:
        raise TrialRegistryError(f"[repo-path] {label} cannot be resolved: {path}") from exc
    try:
        relative = resolved.relative_to(repository_root)
    except ValueError:
        _fail("repo-path", f"{label} is outside repository_root: {resolved}")
    if relative == Path("."):
        _fail("repo-path", f"{label} cannot be repository_root")
    return resolved, relative.as_posix()


def _registry_relative_target(
    path: Path,
    repository_root: Path,
) -> tuple[Path, Path, str]:
    """Validate the registry's lexical tracked-worktree namespace."""
    raw = Path(path)
    candidate = Path(os.path.abspath(os.fspath(
        raw if raw.is_absolute() else repository_root / raw
    )))
    try:
        relative = candidate.relative_to(repository_root)
    except ValueError:
        _fail("registry-path", f"registry is outside repository_root: {candidate}")
    if relative == Path(".") or relative.name in {"", ".", ".."}:
        _fail("registry-path", "registry path must name a file")
    if ".git" in relative.parts:
        _fail("registry-path", "registry path must not contain a .git component")
    return candidate, relative, relative.as_posix()


def _registry_target(
    path: Path,
    repository_root: Path,
    *,
    create_parent: bool,
) -> tuple[Path, str]:
    path, _relative_path, relative = _registry_relative_target(
        Path(path), repository_root,
    )
    if path.exists() or path.is_symlink():
        if path.is_symlink():
            _fail("registry-path", f"registry must not be a symlink: {path}")
        resolved, resolved_relative = _repo_relative(
            path, repository_root, label="registry",
        )
        if resolved_relative != relative:
            _fail("registry-path", "registry path traverses a symlink component")
        return resolved, relative
    parent = path.parent
    existing_ancestor = parent
    while not existing_ancestor.exists() and not existing_ancestor.is_symlink():
        if existing_ancestor == existing_ancestor.parent:
            break
        existing_ancestor = existing_ancestor.parent
    try:
        existing_ancestor.resolve(strict=True).relative_to(repository_root)
    except (OSError, ValueError) as exc:
        raise TrialRegistryError(
            "[registry-path] registry parent real path is outside repository"
        ) from exc
    if create_parent:
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise TrialRegistryError(f"[registry-path] registry parent cannot be created: {parent}") from exc
    try:
        real_parent = parent.resolve(strict=True)
        real_parent.relative_to(repository_root)
    except (OSError, ValueError) as exc:
        raise TrialRegistryError("[registry-path] registry parent real path is outside repository") from exc
    resolved = real_parent / path.name
    return resolved, relative


def _canonical_lifecycle_target(
    path: Path,
    repository_root: Path,
    *,
    create_parent: bool,
) -> tuple[Path, str]:
    """Resolve only the repository's fixed lifecycle ledger authority."""
    _candidate, _relative_path, relative = _registry_relative_target(
        Path(path), repository_root,
    )
    if relative != DEFAULT_LIFECYCLE_PATH.as_posix():
        _fail(
            "lifecycle-path",
            "lifecycle_path must name the canonical repository ledger",
        )
    return _registry_target(
        DEFAULT_LIFECYCLE_PATH,
        repository_root,
        create_parent=create_parent,
    )


def _directory_open_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _open_registry_parent(
    repository_root: Path,
    relative_parent: Path,
    *,
    create: bool,
) -> int:
    """Open each parent component relative to an anchored repository fd."""
    flags = _directory_open_flags()
    try:
        current_fd = os.open(repository_root, flags)
    except OSError as exc:
        raise TrialRegistryError(
            f"[registry-path] repository root cannot be opened: {exc}"
        ) from exc
    try:
        for component in relative_parent.parts:
            try:
                next_fd = os.open(component, flags, dir_fd=current_fd)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(component, 0o755, dir_fd=current_fd)
                next_fd = os.open(component, flags, dir_fd=current_fd)
            info = os.fstat(next_fd)
            if not stat.S_ISDIR(info.st_mode):
                os.close(next_fd)
                _fail("registry-path", "registry parent component is not a directory")
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except TrialRegistryError:
        os.close(current_fd)
        raise
    except OSError as exc:
        os.close(current_fd)
        raise TrialRegistryError(
            f"[registry-path] registry parent cannot be opened safely: {exc}"
        ) from exc


def resolve_measurement_commit(repository_root: Path) -> str:
    """Resolve the operation's measurement HEAD exactly once."""
    root = _repository_root(repository_root)
    result = _git(root, ("rev-parse", "--verify", "HEAD^{commit}"))
    if result.returncode != 0:
        raise TrialRegistryError("[git] HEAD cannot be resolved to a commit")
    try:
        commit_id = result.stdout.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise TrialRegistryError("[git] HEAD resolution returned non-ASCII output") from exc
    if _COMMIT_RE.fullmatch(commit_id) is None:
        _fail("git", "HEAD did not resolve to a 40-digit lowercase commit ID")
    return commit_id


def require_commit_object(repository_root: Path, commit_id: str) -> None:
    """Require a full lowercase SHA-1 that resolves to that exact commit."""
    root = _repository_root(repository_root)
    if not isinstance(commit_id, str) or _COMMIT_RE.fullmatch(commit_id) is None:
        _fail("commit", "commit ID is not 40-digit lowercase hexadecimal")
    result = _git(root, ("rev-parse", "--verify", f"{commit_id}^{{commit}}"))
    if result.returncode != 0:
        _fail("commit", f"commit object does not exist: {commit_id}")
    try:
        resolved = result.stdout.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise TrialRegistryError("[git] commit resolution returned non-ASCII output") from exc
    if resolved != commit_id:
        _fail("commit", f"commit resolution changed object identity: {commit_id}")


def _assert_not_shallow(repository_root: Path) -> None:
    result = _git(repository_root, ("rev-parse", "--is-shallow-repository"))
    if result.returncode != 0:
        raise TrialRegistryError("[git] shallow-repository state cannot be determined")
    if result.stdout.strip() != b"false":
        _fail("ancestry", "shallow repositories are not accepted")


def _assert_no_grafts_or_replace_refs(repository_root: Path) -> None:
    """Reject Git history rewriting inputs before any ancestry proof."""
    git_path = _git(repository_root, ("rev-parse", "--git-path", "info/grafts"))
    if git_path.returncode != 0:
        raise TrialRegistryError(
            "[git-operational] Git graft path could not be resolved"
        )
    try:
        graft_path = Path(git_path.stdout.decode("utf-8").strip())
    except UnicodeDecodeError as exc:
        raise TrialRegistryError(
            "[git-operational] Git graft path was not UTF-8"
        ) from exc
    if not graft_path.is_absolute():
        graft_path = repository_root / graft_path
    if graft_path.exists() or graft_path.is_symlink():
        _fail("ancestry", "Git graft files are not accepted")

    replaces = _git(
        repository_root,
        ("for-each-ref", "--format=%(refname)", "refs/replace"),
    )
    if replaces.returncode != 0:
        raise TrialRegistryError(
            "[git-operational] replace-ref enumeration failed"
        )
    if replaces.stdout.splitlines():
        _fail("ancestry", "Git replace refs are not accepted")


def _assert_full_commit_id(commit_id: str, *, label: str) -> None:
    if not isinstance(commit_id, str) or _COMMIT_RE.fullmatch(commit_id) is None:
        _fail("commit", f"{label} must be a 40-digit lowercase commit ID")


def _parents_at_commit(
    repository_root: Path,
    *,
    commit_id: str,
) -> tuple[str, ...]:
    """Read exactly the parent list Git reports for one full commit ID."""
    _assert_full_commit_id(commit_id, label="effective_commit")
    result = _git(
        repository_root,
        ("rev-list", "--parents", "-n", "1", commit_id),
    )
    if result.returncode != 0:
        raise TrialRegistryError(
            "[git-operational] rev-list --parents failed for the effective commit"
        )
    lines = result.stdout.splitlines()
    if len(lines) != 1:
        _fail("ancestry", "effective commit parent query returned no unique row")
    try:
        fields = lines[0].decode("ascii").split()
    except UnicodeDecodeError as exc:
        raise TrialRegistryError(
            "[git-operational] effective commit parent query was not ASCII"
        ) from exc
    if not fields or fields[0] != commit_id:
        _fail("ancestry", "effective commit parent query changed the commit identity")
    parents = tuple(fields[1:])
    if any(_COMMIT_RE.fullmatch(parent) is None for parent in parents):
        _fail("ancestry", "effective commit parent query returned an invalid parent")
    return parents


def assert_effective_commit_exact_parent(
    repository_root: Path,
    *,
    content_commit: str,
    effective_commit: str,
) -> None:
    """Require a normal commit C whose sole parent is exactly P.

    A root commit, merge commit, ref/short/non-lowercase argument, failed
    ``rev-list`` query, shallow repository, graft, replace ref, or other parent
    is rejected.  A commit C with one parent P is accepted, for example when P
    contains the manifest and C adds only the effective binding record.
    """
    root = _repository_root(repository_root)
    _assert_full_commit_id(content_commit, label="content_commit")
    _assert_full_commit_id(effective_commit, label="effective_commit")
    _assert_no_grafts_or_replace_refs(root)
    _assert_not_shallow(root)
    require_commit_object(root, content_commit)
    require_commit_object(root, effective_commit)
    parents = _parents_at_commit(root, commit_id=effective_commit)
    if len(parents) == 0:
        _fail("ancestry", "effective commit is a root commit")
    if len(parents) != 1:
        _fail("ancestry", "effective commit is a merge commit")
    if parents[0] != content_commit:
        _fail("ancestry", "effective commit parent is not the exact content commit")


def _assert_ancestor(
    repository_root: Path,
    *,
    ancestor: str,
    descendant: str,
    gate: str,
    message: str,
) -> None:
    require_commit_object(repository_root, ancestor)
    require_commit_object(repository_root, descendant)
    _assert_not_shallow(repository_root)
    result = _git(repository_root, ("merge-base", "--is-ancestor", ancestor, descendant))
    if result.returncode == 0:
        return
    if result.returncode == 1:
        _fail(gate, message)
    stderr = result.stderr.decode("utf-8", errors="replace").strip()
    raise TrialRegistryError(
        f"[git-operational] merge-base --is-ancestor failed with rc={result.returncode}: {stderr}"
    )


def assert_prereg_ancestor(
    repository_root: Path,
    *,
    prereg_commit: str,
    measurement_commit: str,
) -> None:
    """Require preregistration to be an ancestor of the measurement commit."""
    root = _repository_root(repository_root)
    _assert_ancestor(
        root,
        ancestor=prereg_commit,
        descendant=measurement_commit,
        gate="ancestry",
        message="prereg_commit is not an ancestor of measurement_head",
    )


def _blob_at_commit(
    repository_root: Path,
    *,
    commit_id: str,
    relative_path: str,
) -> bytes | None:
    if relative_path.startswith("/") or relative_path in {"", ".", ".."}:
        _fail("repo-path", "Git blob path is not repository-relative")
    listing = _git(repository_root, (
        "ls-tree", "-z", "--full-name", commit_id, "--", relative_path,
    ))
    if listing.returncode != 0:
        raise TrialRegistryError("[git-operational] committed path existence check failed")
    entries = [entry for entry in listing.stdout.split(b"\0") if entry]
    if not entries:
        return None
    if len(entries) != 1:
        _fail("committed-mode", "committed path did not resolve to one tree entry")
    metadata, separator, entry_path = entries[0].partition(b"\t")
    fields = metadata.split()
    if separator != b"\t" or len(fields) != 3:
        raise TrialRegistryError("[git-operational] committed tree entry is malformed")
    mode, object_type, object_id = fields
    if entry_path != os.fsencode(relative_path):
        _fail("committed-mode", "committed tree entry path differs from the literal path")
    if object_type != b"blob" or mode not in {b"100644", b"100755"}:
        _fail("committed-mode", "committed path is not a regular file entry")
    result = _git(repository_root, ("cat-file", "blob", object_id.decode("ascii")))
    if result.returncode != 0:
        raise TrialRegistryError("[git-operational] committed blob cannot be read")
    return result.stdout


def _validate_binding_relative_path(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value or value.startswith("/"):
        _fail("effective-binding", f"{label} must be a relative repository path")
    path = Path(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        _fail("effective-binding", f"{label} is not a safe repository path")
    if ".git" in path.parts:
        _fail("effective-binding", f"{label} must not contain a .git component")
    return path.as_posix()


def _parse_effective_binding_bytes(
    data: bytes,
    *,
    label: str,
) -> PreregEffectiveBinding:
    value = _decode_json(data, label=label)
    if not isinstance(value, Mapping):
        _fail("effective-binding", f"{label} root must be an object")
    if _canonical_json_bytes(value) != data:
        _fail("effective-binding", f"{label} is not canonical JSON")
    _exact_keys(value, _EFFECTIVE_BINDING_KEYS, label=label)
    if value.get("schema_version") != EFFECTIVE_BINDING_SCHEMA_VERSION:
        _fail("effective-binding", f"{label} has an unsupported schema_version")
    content = value.get("prereg_content_commit")
    if not isinstance(content, str) or _COMMIT_RE.fullmatch(content) is None:
        _fail("effective-binding", f"{label}.prereg_content_commit is invalid")
    manifest_path = _validate_binding_relative_path(
        value.get("manifest_path"), label=f"{label}.manifest_path",
    )
    for field in ("manifest_sha256", "attempt_registry_initial_sha256"):
        digest = value.get(field)
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            _fail("effective-binding", f"{label}.{field} is invalid")
    freeze_id = value.get("freeze_id")
    if not isinstance(freeze_id, str) or not freeze_id or len(freeze_id) > 128:
        _fail("effective-binding", f"{label}.freeze_id is invalid")
    attempt_path = _validate_binding_relative_path(
        value.get("attempt_registry_path"),
        label=f"{label}.attempt_registry_path",
    )
    if attempt_path != DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix():
        _fail("effective-binding", "attempt_registry_path is not the canonical path")
    return PreregEffectiveBinding(
        schema_version=EFFECTIVE_BINDING_SCHEMA_VERSION,
        prereg_content_commit=content,
        manifest_path=manifest_path,
        manifest_sha256=value["manifest_sha256"],
        freeze_id=freeze_id,
        attempt_registry_path=attempt_path,
        attempt_registry_initial_sha256=value["attempt_registry_initial_sha256"],
        raw_bytes=data,
    )


def load_effective_binding_at_commit(
    repository_root: Path,
    effective_commit: str,
    manifest_path: Path,
    manifest: TrialManifest | None = None,
) -> PreregEffectiveBinding:
    """Load the fixed effective-binding blob from commit C.

    A missing or non-canonical binding blob is rejected, and a binding whose
    P-side manifest bytes/digest disagree is rejected.  A C blob containing
    the exact record, with P's manifest and genesis bytes matching its hashes,
    is accepted; C itself is intentionally not recorded in the JSON.
    """
    root = _repository_root(repository_root)
    _assert_full_commit_id(effective_commit, label="effective_commit")
    require_commit_object(root, effective_commit)
    binding_bytes = _blob_at_commit(
        root,
        commit_id=effective_commit,
        relative_path=DEFAULT_EFFECTIVE_BINDING_PATH.as_posix(),
    )
    if binding_bytes is None:
        _fail(
            "effective-binding",
            "effective binding blob is absent from effective commit",
        )
    binding = _parse_effective_binding_bytes(
        binding_bytes, label="effective binding blob",
    )
    _assert_full_commit_id(binding.prereg_content_commit, label="content_commit")
    _repo_path, manifest_relative = _repo_relative(
        Path(manifest_path), root, label="manifest",
    )
    if manifest_relative != binding.manifest_path:
        _fail("effective-binding", "binding manifest_path differs from manifest argument")
    if manifest is None:
        manifest = load_trial_manifest(Path(manifest_path))
    manifest_blob = _blob_at_commit(
        root,
        commit_id=binding.prereg_content_commit,
        relative_path=manifest_relative,
    )
    if manifest_blob is None:
        _fail("effective-binding", "manifest blob is absent from content commit")
    if hashlib.sha256(manifest_blob).hexdigest() != binding.manifest_sha256:
        _fail("effective-binding", "manifest blob differs from binding manifest_sha256")
    if manifest is not None:
        if (
            manifest.sha256 != binding.manifest_sha256
            or manifest.raw_bytes != manifest_blob
        ):
            _fail("effective-binding", "loaded manifest differs from effective binding")
    attempt_blob = _blob_at_commit(
        root,
        commit_id=binding.prereg_content_commit,
        relative_path=binding.attempt_registry_path,
    )
    if attempt_blob is None:
        _fail("effective-binding", "attempt registry genesis blob is absent from content commit")
    if hashlib.sha256(attempt_blob).hexdigest() != binding.attempt_registry_initial_sha256:
        _fail(
            "effective-binding",
            "attempt registry genesis bytes differ from binding initial hash",
        )
    return binding


def validate_preregistration_binding(
    repository_root: Path,
    *,
    manifest_path: Path,
    effective_commit: str,
    measurement_commit: str,
) -> PreregEffectiveBinding:
    """Validate the complete P/C/H preregistration proof.

    Invalid commit syntax, failed parent enumeration, root/merge/other-parent
    C, missing C binding, shallow/graft/replace history, and P-only ancestry
    are rejected.  A normal C with sole parent P, matching P manifest/genesis
    blobs, and C reachable from measurement HEAD H is accepted.
    """
    root = _repository_root(repository_root)
    _assert_full_commit_id(measurement_commit, label="measurement_commit")
    _assert_no_grafts_or_replace_refs(root)
    _assert_not_shallow(root)
    _assert_full_commit_id(effective_commit, label="effective_commit")
    manifest = load_trial_manifest(Path(manifest_path))
    binding = load_effective_binding_at_commit(
        root,
        effective_commit,
        Path(manifest_path),
        manifest,
    )
    _assert_ancestor(
        root,
        ancestor=manifest.prereg_commit,
        descendant=binding.prereg_content_commit,
        gate="ancestry",
        message="manifest prereg_commit is not an ancestor of prereg_content_commit",
    )
    assert_effective_commit_exact_parent(
        root,
        content_commit=binding.prereg_content_commit,
        effective_commit=effective_commit,
    )
    _assert_ancestor(
        root,
        ancestor=effective_commit,
        descendant=measurement_commit,
        gate="ancestry",
        message="prereg_effective_commit is not an ancestor of measurement_head",
    )
    return binding


def _require_committed_file(
    *,
    repository_root: Path,
    commit_id: str,
    path: Path,
    label: str,
    expected_bytes: bytes,
) -> str:
    _resolved, relative = _repo_relative(path, repository_root, label=label)
    blob = _blob_at_commit(
        repository_root, commit_id=commit_id, relative_path=relative,
    )
    if blob is None:
        _fail("committed-file", f"{label} is absent from commit {commit_id}")
    if blob != expected_bytes:
        _fail("committed-file", f"{label} bytes differ from commit {commit_id}")
    return relative


def _find_registration(
    registrations: tuple[TrialRegistration, ...],
    expected: TrialRegistration,
) -> TrialRegistration:
    selected = [
        item for item in registrations
        if item.manifest_sha256 == expected.manifest_sha256
    ]
    if len(selected) != 1 or selected[0] != expected:
        _fail("registration-binding", "manifest has no single exact registry registration")
    return selected[0]


def _trial_canonical_tuple(trial: TrialSpec) -> tuple[object, ...]:
    """The complete manifest/registry identity, not only trial_id."""
    return (
        trial.trial_id,
        trial.arm,
        trial.holdout,
        trial.campaign_id,
        trial.generations,
    )


def _assert_manifest_registry_trial_set(
    manifest: TrialManifest,
    registration: TrialRegistration,
) -> None:
    """Require the six manifest trials and one registry row to be identical.

    A registry that contains every manifest trial with a changed arm,
    holdout, campaign, or generations is rejected, and a registry with an
    extra or missing trial is rejected.  The report ``cells`` collection is
    intentionally not inspected here; it is a one-run runtime object and is
    checked by a separate helper below.
    """
    expected = tuple(_trial_canonical_tuple(item) for item in manifest.trials)
    actual = tuple(_trial_canonical_tuple(item) for item in registration.trials)
    if len(actual) != len(expected) or set(actual) != set(expected):
        _fail(
            "registration-binding",
            "manifest and registry trial sets differ in canonical trial identity",
        )
    if actual != expected:
        _fail(
            "registration-binding",
            "manifest and registry trial order differs from canonical order",
        )
    if registration.prereg_commit != manifest.prereg_commit:
        _fail("registration-binding", "registry prereg_commit differs from manifest")


def _find_registration_for_manifest(
    registrations: tuple[TrialRegistration, ...],
    manifest: TrialManifest,
    *,
    effective_commit: str | None = None,
    allow_distinct_content_commit: bool = False,
) -> TrialRegistration:
    """Find one manifest row while keeping the P and C identities distinct.

    A registered trial may store the manifest's ``prereg_commit`` as P and a
    later ``prereg_content_commit`` as C.  Forcing equality here would reject
    that valid chain before ``validate_preregistration_binding`` can enforce
    the P-is-an-ancestor-of-C proof.  Callers that perform that proof opt in;
    the strict default remains for direct helper callers without that proof.
    """
    candidates = [
        item for item in registrations
        if item.manifest_sha256 == manifest.sha256
        and item.prereg_commit == manifest.prereg_commit
    ]
    if not allow_distinct_content_commit:
        candidates = [
            item for item in candidates
            if item.prereg_content_commit == manifest.prereg_commit
        ]
    if effective_commit is not None:
        candidates = [
            item for item in candidates
            if item.prereg_effective_commit == effective_commit
        ]
    if len(candidates) != 1:
        _fail("registration-binding", "manifest has no single exact registry registration")
    registration = candidates[0]
    _assert_manifest_registry_trial_set(manifest, registration)
    return registration


def _assert_runtime_report_trial_set(
    loaded: Sequence[_LoadedReport],
    manifest: TrialManifest,
) -> None:
    """Require the six report objects to cover the manifest trial IDs once.

    This is a report-collection check only.  It does not inspect registry rows
    or runtime ``cells``; those are different one-run objects and are checked
    by ``_assert_runtime_report_cells``.
    """
    trial_ids = [item.report.get("trial_id") for item in loaded]
    expected_ids = {trial.trial_id for trial in manifest.trials}
    if (
        any(not isinstance(trial_id, str) for trial_id in trial_ids)
        or len(set(trial_ids)) != len(trial_ids)
        or set(trial_ids) != expected_ids
    ):
        _fail("trial-set", "report trial_id set is not the exact manifest trial set")


def _assert_runtime_report_cells(
    report: Mapping[str, Any],
    *,
    trial: TrialSpec,
) -> list[Mapping[str, Any]]:
    """Validate the independent per-run cell collection (zero or one cell)."""
    expected_workload = HOLDOUT_BINDINGS[trial.holdout]
    cells = report.get("cells")
    if not isinstance(cells, list) or len(cells) > 1:
        _fail("runtime-cell-set", "report cells must contain zero or one cell")
    if not cells:
        return []
    cell = cells[0]
    if not isinstance(cell, Mapping):
        _fail("runtime-cell-set", "report cell is not an object")
    if cell.get("workload") != expected_workload["workload"]:
        _fail("runtime-cell-set", "runtime cell differs from its trial projection")
    if is_exact_campaignless_failure_fallback_cell(cell):
        return [cell]
    flags = cell.get("workload_flags")
    if not isinstance(flags, Mapping):
        _fail(
            "runtime-cell-set",
            "runtime cell differs from its trial projection: "
            "workload_flags is not an object",
        )
    for field in ("ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw"):
        if flags.get(field) != expected_workload[field]:
            _fail(
                "runtime-cell-set",
                "runtime cell differs from its trial projection: "
                f"workload_flags.{field} differs",
            )
    scale = cell.get("perf_config_scale")
    if not isinstance(scale, Mapping):
        _fail(
            "runtime-cell-set",
            "runtime cell differs from its trial projection: "
            "perf_config_scale is not an object",
        )
    for field in ("records", "threads"):
        if scale.get(field) != expected_workload[field]:
            _fail(
                "runtime-cell-set",
                "runtime cell differs from its trial projection: "
                f"perf_config_scale.{field} differs",
            )
    if cell.get("campaign_id") != trial.campaign_id:
        _fail(
            "runtime-cell-set",
            "runtime cell differs from its trial projection: campaign_id differs",
        )
    return [cell]


def _assert_holdout_cell_condition(
    cell: Mapping[str, Any],
    *,
    expected: Mapping[str, str | int],
    campaign_id: str,
    gate: str,
    message: str,
) -> None:
    flags = cell.get("workload_flags")
    if not isinstance(flags, Mapping):
        _fail(gate, f"{message}: workload_flags is not an object")
    for field in ("ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw"):
        if flags.get(field) != expected[field]:
            _fail(gate, f"{message}: workload_flags.{field} differs")
    scale = cell.get("perf_config_scale")
    if not isinstance(scale, Mapping):
        _fail(gate, f"{message}: perf_config_scale is not an object")
    for field in ("records", "threads"):
        if scale.get(field) != expected[field]:
            _fail(gate, f"{message}: perf_config_scale.{field} differs")
    if cell.get("campaign_id") != campaign_id:
        _fail(gate, f"{message}: campaign_id differs")


def append_trial_registration(
    *,
    manifest_path: Path,
    repository_root: Path,
    registry_path: Path,
    prereg_effective_commit: str,
) -> TrialRegistration:
    """Append one manifest registration in a single fsynced critical section."""
    root = _repository_root(repository_root)
    manifest = load_trial_manifest(Path(manifest_path))
    measurement_head = resolve_measurement_commit(root)
    _require_committed_file(
        repository_root=root,
        commit_id=measurement_head,
        path=Path(manifest_path),
        label="manifest",
        expected_bytes=manifest.raw_bytes,
    )
    assert_prereg_ancestor(
        root,
        prereg_commit=manifest.prereg_commit,
        measurement_commit=measurement_head,
    )
    registry, relative_path, relative = _registry_relative_target(
        Path(registry_path), root,
    )
    committed = _blob_at_commit(
        root, commit_id=measurement_head, relative_path=relative,
    )
    effective_commit = prereg_effective_commit
    _assert_full_commit_id(effective_commit, label="prereg_effective_commit")
    effective_binding = validate_preregistration_binding(
        root,
        manifest_path=Path(manifest_path),
        effective_commit=effective_commit,
        measurement_commit=measurement_head,
    )
    registration = _registration_for(
        manifest,
        prereg_content_commit=effective_binding.prereg_content_commit,
        prereg_effective_commit=effective_commit,
    )
    payload = _canonical_json_bytes(_registration_dict(registration)) + b"\n"
    try:
        parent_fd = _open_registry_parent(
            root, relative_path.parent, create=True,
        )
        try:
            try:
                path_info = os.stat(
                    relative_path.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                path_info = None
            if path_info is not None and not stat.S_ISREG(path_info.st_mode):
                _fail("registry-path", "registry must be a regular non-symlink file")
            if committed is None and path_info is not None:
                _fail("append-state", "untracked registry already exists")
            if committed is not None and path_info is None:
                _fail("append-state", "committed registry is missing from the working tree")
            flags = os.O_RDWR | os.O_APPEND
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            if path_info is None:
                flags |= os.O_CREAT | os.O_EXCL
            fd = os.open(
                relative_path.name,
                flags,
                0o644,
                dir_fd=parent_fd,
            )
            try:
                fcntl.flock(fd, fcntl.LOCK_EX)
                rebound_parent_fd = _open_registry_parent(
                    root, relative_path.parent, create=False,
                )
                try:
                    held_parent = os.fstat(parent_fd)
                    rebound_parent = os.fstat(rebound_parent_fd)
                    if (
                        held_parent.st_dev,
                        held_parent.st_ino,
                    ) != (
                        rebound_parent.st_dev,
                        rebound_parent.st_ino,
                    ):
                        _fail(
                            "append-state",
                            "registry parent changed before locked validation",
                        )
                finally:
                    os.close(rebound_parent_fd)
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode):
                    _fail("append-state", "opened registry is not a regular file")
                rebound = os.stat(
                    relative_path.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
                if (rebound.st_dev, rebound.st_ino) != (info.st_dev, info.st_ino):
                    _fail("append-state", "registry path changed before locked validation")
                current = bytearray()
                offset = 0
                while offset < info.st_size:
                    chunk = os.pread(fd, min(1024 * 1024, info.st_size - offset), offset)
                    if not chunk:
                        _fail("append-state", "registry read stopped before fstat size")
                    current.extend(chunk)
                    offset += len(chunk)
                after_read = os.fstat(fd)
                if (
                    info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns
                ) != (
                    after_read.st_dev, after_read.st_ino,
                    after_read.st_size, after_read.st_mtime_ns,
                ):
                    _fail("append-state", "registry changed during locked validation")
                rebound_after_read = os.stat(
                    relative_path.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
                if (
                    rebound_after_read.st_dev,
                    rebound_after_read.st_ino,
                ) != (after_read.st_dev, after_read.st_ino):
                    _fail("append-state", "registry path changed during locked validation")
                current_bytes = bytes(current)
                if committed is None:
                    if current_bytes:
                        _fail("append-state", "first registration did not start from empty bytes")
                    registrations: tuple[TrialRegistration, ...] = ()
                else:
                    if current_bytes != committed:
                        _fail("append-state", "working registry differs from the HEAD blob")
                    registrations = _load_registry_bytes(current_bytes, label="registry")
                _assert_registry_unique((*registrations, registration))
                view = memoryview(payload)
                while view:
                    written = os.write(fd, view)
                    if written <= 0:
                        raise OSError("registry append did not advance")
                    view = view[written:]
                rebound_after_append = os.stat(
                    relative_path.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
                appended = os.fstat(fd)
                if (
                    rebound_after_append.st_dev,
                    rebound_after_append.st_ino,
                ) != (appended.st_dev, appended.st_ino):
                    _fail("append-state", "registry path changed during append")
                os.fsync(fd)
                os.fsync(parent_fd)
            finally:
                os.close(fd)
        finally:
            os.close(parent_fd)
    except TrialRegistryError:
        raise
    except OSError as exc:
        raise TrialRegistryError(f"[append-io] registry append failed: {exc}") from exc
    return registration


def _load_committed_registry(
    *,
    repository_root: Path,
    registry_path: Path,
    commit_id: str,
) -> tuple[tuple[TrialRegistration, ...], bytes, str]:
    registry, relative = _registry_target(
        registry_path, repository_root, create_parent=False,
    )
    working_bytes = _read_regular_bytes(
        registry, gate="registry-read", label="registry",
    )
    committed = _blob_at_commit(
        repository_root, commit_id=commit_id, relative_path=relative,
    )
    if committed is None:
        _fail("committed-registry", "registry is not committed at the operation HEAD")
    if committed != working_bytes:
        _fail("committed-registry", "working registry differs from the operation HEAD blob")
    return _load_registry_bytes(committed, label="committed registry"), committed, relative


def _attempt_digest(value: object, *, label: str, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        _fail("attempt-registry-schema", f"{label} is not a SHA-256 digest")
    return value


def _attempt_text(value: object, *, label: str, max_length: int = 256) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length:
        _fail("attempt-registry-schema", f"{label} is not a bounded non-empty string")
    return value


def _attempt_process_identity(
    value: object,
    *,
    label: str,
) -> dict[str, Any]:
    if type(value) is not dict or frozenset(value) != _PROCESS_IDENTITY_KEYS:
        _fail("attempt-registry-schema", f"{label} exact keys differ")
    pid = value.get("pid")
    if type(pid) is not int or pid < 1:
        _fail("attempt-registry-schema", f"{label}.pid is invalid")
    starttime = value.get("starttime")
    if type(starttime) is bool or not isinstance(starttime, (int, str)):
        _fail("attempt-registry-schema", f"{label}.starttime is invalid")
    if isinstance(starttime, int) and starttime < 0:
        _fail("attempt-registry-schema", f"{label}.starttime is invalid")
    if isinstance(starttime, str) and not starttime:
        _fail("attempt-registry-schema", f"{label}.starttime is invalid")
    execution_uuid = _attempt_text(
        value.get("execution_uuid"), label=f"{label}.execution_uuid",
    )
    return {
        "pid": pid,
        "starttime": starttime,
        "execution_uuid": execution_uuid,
    }


def _attempt_slot_config(slot: Mapping[str, Any]) -> tuple[object, ...]:
    return (
        slot["trial_id"],
        slot["arm"],
        slot["holdout"],
        slot["campaign_id"],
        slot["replicate_index"],
    )


def _parse_attempt_slot(value: object, *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail("attempt-registry-schema", f"{label} is not an object")
    slot_keys = frozenset(value)
    if slot_keys not in {_ATTEMPT_V1_V2_SLOT_KEYS, _ATTEMPT_SLOT_KEYS}:
        expected = (
            _ATTEMPT_SLOT_KEYS
            if "prereg_generation" in value else _ATTEMPT_V1_V2_SLOT_KEYS
        )
        _exact_keys(value, expected, label=label)
    slot_id = _attempt_text(value.get("slot_id"), label=f"{label}.slot_id")
    trial_id = value.get("trial_id")
    if not isinstance(trial_id, str) or _TRIAL_ID_RE.fullmatch(trial_id) is None:
        _fail("attempt-registry-schema", f"{label}.trial_id is invalid")
    arm = value.get("arm")
    if arm not in ARMS:
        _fail("attempt-registry-schema", f"{label}.arm is outside the closed set")
    holdout = value.get("holdout")
    if holdout not in HOLDOUTS:
        _fail("attempt-registry-schema", f"{label}.holdout is outside the closed set")
    campaign_id = _attempt_text(
        value.get("campaign_id"), label=f"{label}.campaign_id",
    )
    prereg_generation = value.get("prereg_generation")
    if (
        "prereg_generation" in value
        and (type(prereg_generation) is not int or prereg_generation < 1)
    ):
        _fail(
            "attempt-registry-schema",
            f"{label}.prereg_generation is invalid",
        )
    replicate_index = value.get("replicate_index")
    attempt_index = value.get("attempt_index")
    for field, raw in (
        ("replicate_index", replicate_index),
        ("attempt_index", attempt_index),
    ):
        if type(raw) is not int or raw < 0:
            _fail("attempt-registry-schema", f"{label}.{field} is invalid")
    schedule_row_sha256 = _attempt_digest(
        value.get("schedule_row_sha256"), label=f"{label}.schedule_row_sha256",
    )
    result = {
        "slot_id": slot_id,
        "trial_id": trial_id,
        "arm": arm,
        "holdout": holdout,
        "campaign_id": campaign_id,
        "replicate_index": replicate_index,
        "attempt_index": attempt_index,
        "schedule_row_sha256": schedule_row_sha256,
    }
    if "prereg_generation" in value:
        result["prereg_generation"] = prereg_generation
    return result


_S8CAttemptBinding = tuple[str, str]


class _S8CSlotCodec:
    exact_keys = _ATTEMPT_SLOT_KEYS

    def parse(self, value: object, *, label: str) -> dict[str, Any]:
        return _parse_attempt_slot(value, label=label)

    def to_json(self, slot: Mapping[str, Any]) -> dict[str, Any]:
        return dict(slot)

    def slot_id(self, slot: Mapping[str, Any]) -> str:
        return slot["slot_id"]

    def series_key(self, slot: Mapping[str, Any]) -> tuple[object, ...]:
        return _attempt_slot_config(slot)

    def attempt_ordinal(self, slot: Mapping[str, Any]) -> int:
        return slot["attempt_index"]

    def schedule_sha256(self, slot: Mapping[str, Any]) -> str:
        return slot["schedule_row_sha256"]


class _S8CBindingCodec:
    event_keys = frozenset({
        "prereg_content_commit", "prereg_effective_commit",
    })

    def parse(
        self, row: Mapping[str, object], *, label: str,
    ) -> _S8CAttemptBinding:
        content = row.get("prereg_content_commit")
        effective = row.get("prereg_effective_commit")
        _assert_full_commit_id(content, label=f"{label}.prereg_content_commit")
        _assert_full_commit_id(effective, label=f"{label}.prereg_effective_commit")
        return content, effective

    def to_event_fields(self, binding: _S8CAttemptBinding) -> dict[str, Any]:
        return {
            "prereg_content_commit": binding[0],
            "prereg_effective_commit": binding[1],
        }

    def identity(self, binding: _S8CAttemptBinding) -> tuple[str, str]:
        return binding

    def capability_payload(
        self,
        *,
        slot: Mapping[str, Any],
        binding: _S8CAttemptBinding,
        freeze_id: str,
    ) -> dict[str, Any]:
        del freeze_id
        payload = {
            "slot_id": slot["slot_id"],
            "trial_id": slot["trial_id"],
            "arm": slot["arm"],
            "holdout": slot["holdout"],
            "campaign_id": slot["campaign_id"],
            "replicate_index": slot["replicate_index"],
            "attempt_index": slot["attempt_index"],
            "schedule_row_sha256": slot["schedule_row_sha256"],
            "prereg_content_commit": binding[0],
            "prereg_effective_commit": binding[1],
        }
        if "prereg_generation" in slot:
            payload["prereg_generation"] = slot["prereg_generation"]
        return payload


_ATTEMPT_V1_RECEIPT_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "capability_digest_sha256", "authority_id", "authority_policy_sha256",
    "external_evidence_sha256", "classified_at", "failure_reason",
    "performance_output_read",
})
_ATTEMPT_RECEIPT_KEYS = frozenset({
    "schema_version", "event", "freeze_id", "slot_id",
    "capability_digest_sha256", "authority_id", "authority_policy_sha256",
    "external_evidence_sha256", "classified_at",
    "pre_observation_failure_reason", "pre_observation_seal_sha256",
})

_ATTEMPT_GENESIS_KEYS_BY_SCHEMA = {
    _ATTEMPT_REGISTRY_SCHEMA_VERSION_V1: _ATTEMPT_V1_GENESIS_KEYS,
    _ATTEMPT_REGISTRY_SCHEMA_VERSION_V2: _ATTEMPT_GENESIS_KEYS,
    ATTEMPT_REGISTRY_SCHEMA_VERSION: _ATTEMPT_GENESIS_KEYS,
}
_ATTEMPT_EVENT_KEYS_BY_SCHEMA = {
    _ATTEMPT_REGISTRY_SCHEMA_VERSION_V1: {
        "start": _ATTEMPT_V1_START_KEYS,
        "classification": _ATTEMPT_V1_CLASSIFICATION_KEYS,
        "terminal": _ATTEMPT_V1_TERMINAL_KEYS,
    },
    _ATTEMPT_REGISTRY_SCHEMA_VERSION_V2: {
        "start": _ATTEMPT_START_KEYS,
        "pre-observation-seal": _ATTEMPT_PRE_OBSERVATION_SEAL_KEYS,
        "classification": _ATTEMPT_CLASSIFICATION_KEYS,
        "observation-start": _ATTEMPT_OBSERVATION_START_KEYS,
        "terminal": _ATTEMPT_TERMINAL_KEYS,
    },
    ATTEMPT_REGISTRY_SCHEMA_VERSION: {
        "start": _ATTEMPT_START_KEYS,
        "pre-observation-seal": _ATTEMPT_PRE_OBSERVATION_SEAL_KEYS,
        "classification": _ATTEMPT_CLASSIFICATION_KEYS,
        "observation-start": _ATTEMPT_OBSERVATION_START_KEYS,
        "terminal": _ATTEMPT_TERMINAL_KEYS,
    },
}
_ATTEMPT_RECEIPT_KEYS_BY_SCHEMA = {
    _ATTEMPT_REGISTRY_SCHEMA_VERSION_V1: _ATTEMPT_V1_RECEIPT_KEYS,
    _ATTEMPT_REGISTRY_SCHEMA_VERSION_V2: _ATTEMPT_RECEIPT_KEYS,
    ATTEMPT_REGISTRY_SCHEMA_VERSION: _ATTEMPT_RECEIPT_KEYS,
}


def _s8c_attempt_genesis_fields(
    freeze_id: str, manifest_path: _PurePosixPath, manifest_sha256: str,
) -> dict[str, Any]:
    return {
        "freeze_id": freeze_id,
        "manifest_path": manifest_path.as_posix(),
        "manifest_sha256": manifest_sha256,
    }


def _s8c_attempt_freeze_id(genesis: Mapping[str, Any]) -> str:
    return genesis["freeze_id"]


def _s8c_attempt_binding_mismatch(
    actual: _S8CAttemptBinding,
    expected: tuple[str | None, str | None],
) -> str | None:
    if expected[0] is not None and actual[0] != expected[0]:
        return "attempt row content commit differs from expected P"
    if expected[1] is not None and actual[1] != expected[1]:
        return "attempt row effective commit differs from expected C"
    return None


_S8C_ATTEMPT_PROFILE = _attempt_core.DomainProfile(
    schema=_attempt_core.SchemaProfile(
        current=ATTEMPT_REGISTRY_SCHEMA_VERSION,
        readable=_ATTEMPT_REGISTRY_SCHEMA_VERSIONS,
        genesis_keys=_ATTEMPT_GENESIS_KEYS_BY_SCHEMA,
        event_keys=_ATTEMPT_EVENT_KEYS_BY_SCHEMA,
        receipt_keys=_ATTEMPT_RECEIPT_KEYS_BY_SCHEMA,
    ),
    layout=_attempt_core.RegistryLayout(
        registry_path=_PurePosixPath(DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix()),
        classification_receipt_dir=_PurePosixPath(
            "output/s8c-trial-registry/classification-receipts"
        ),
    ),
    statuses=ATTEMPT_STATUSES,
    retryable_reasons=ATTEMPT_RETRYABLE_FAILURE_REASONS,
    slot_codec=_S8CSlotCodec(),
    binding_codec=_S8CBindingCodec(),
    transition_policy=_attempt_core.TransitionPolicy(
        require_previous_terminal=True,
        forbid_retry_after_observation=True,
        allow_recovered_abandonment=False,
        max_series_attempts=None,
        require_terminal_reason_equals_classification=False,
        budget_key=None,
        max_consumptions_per_budget_key=None,
    ),
    process_identity_keys=_PROCESS_IDENTITY_KEYS,
    build_genesis_fields=_s8c_attempt_genesis_fields,
    freeze_id_from_genesis=_s8c_attempt_freeze_id,
    binding_conflict_message="attempt rows do not share one P/C pair",
    binding_mismatch=_s8c_attempt_binding_mismatch,
)

_S8C_FORMAL_ATTEMPT_PROFILE = dataclasses.replace(
    _S8C_ATTEMPT_PROFILE,
    transition_policy=dataclasses.replace(
        _S8C_ATTEMPT_PROFILE.transition_policy,
        require_terminal_reason_equals_classification=True,
    ),
)


def _attempt_core_call(function, /, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except _attempt_core.AttemptRegistryCoreError as exc:
        raise TrialRegistryError(str(exc)) from exc


def _attempt_capability_payload(
    *,
    freeze_id: str,
    slot: Mapping[str, Any],
    prereg_content_commit: str,
    prereg_effective_commit: str,
    schema_version: str = ATTEMPT_REGISTRY_SCHEMA_VERSION,
) -> dict[str, Any]:
    payload = {
        "schema_version": schema_version,
        "freeze_id": freeze_id,
        "slot_id": slot["slot_id"],
        "trial_id": slot["trial_id"],
        "arm": slot["arm"],
        "holdout": slot["holdout"],
        "campaign_id": slot["campaign_id"],
        "replicate_index": slot["replicate_index"],
        "attempt_index": slot["attempt_index"],
        "schedule_row_sha256": slot["schedule_row_sha256"],
        "prereg_content_commit": prereg_content_commit,
        "prereg_effective_commit": prereg_effective_commit,
    }
    if schema_version == ATTEMPT_REGISTRY_SCHEMA_VERSION:
        payload["prereg_generation"] = slot["prereg_generation"]
    return payload


def _attempt_capability_digest(
    *,
    freeze_id: str,
    slot: Mapping[str, Any],
    prereg_content_commit: str,
    prereg_effective_commit: str,
    schema_version: str = ATTEMPT_REGISTRY_SCHEMA_VERSION,
) -> str:
    normalized_slot = dict(slot)
    if schema_version in {
        _ATTEMPT_REGISTRY_SCHEMA_VERSION_V1,
        _ATTEMPT_REGISTRY_SCHEMA_VERSION_V2,
    }:
        normalized_slot.pop("prereg_generation", None)
    return _attempt_core_call(
        _attempt_core.capability_digest,
        profile=_S8C_ATTEMPT_PROFILE,
        schema_version=schema_version,
        freeze_id=freeze_id,
        slot=normalized_slot,
        binding=(prereg_content_commit, prereg_effective_commit),
    )


def _assert_attempt_registry_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    repository_root: Path | None = None,
    expected_prereg_content_commit: str | None = None,
    expected_prereg_effective_commit: str | None = None,
) -> tuple[dict[str, Any], ...]:
    """Replay the shared core, then verify 8c receipt storage when requested."""
    expected_binding = (
        None
        if (
            expected_prereg_content_commit is None
            and expected_prereg_effective_commit is None
        )
        else (
            expected_prereg_content_commit,
            expected_prereg_effective_commit,
        )
    )
    checked = _attempt_core_call(
        _attempt_core.assert_registry_rows,
        rows,
        profile=_S8C_ATTEMPT_PROFILE,
        expected_binding=expected_binding,
    )
    if repository_root is not None:
        _assert_attempt_classification_receipts(
            checked,
            repository_root=repository_root,
        )
    return checked


def _assert_attempt_classification_receipts(
    rows: Sequence[Mapping[str, Any]], *, repository_root: Path,
) -> None:
    classifications = {
        row["slot_id"]: row
        for row in rows
        if row.get("event") == "classification"
    }
    for classification in classifications.values():
        receipt_path = (
            repository_root
            / "output/s8c-trial-registry/classification-receipts"
            / f"{classification['classification_receipt_sha256']}.json"
        )
        if not receipt_path.exists():
            _fail("attempt-classification", "classification receipt file is absent")
        receipt = _read_regular_bytes(
            receipt_path,
            gate="attempt-classification",
            label="classification receipt",
        )
        if hashlib.sha256(receipt).hexdigest() != classification[
            "classification_receipt_sha256"
        ]:
            _fail("attempt-classification", "classification receipt digest differs")
        if not receipt.endswith(b"\n"):
            _fail(
                "attempt-classification",
                "classification receipt is not newline terminated",
            )
        receipt_value = _decode_json(receipt[:-1], label="classification receipt")
        expected_receipt_keys = _ATTEMPT_RECEIPT_KEYS_BY_SCHEMA.get(
            classification["schema_version"]
        )
        if expected_receipt_keys is None:
            _fail(
                "attempt-classification",
                "classification receipt schema is unsupported",
            )
        if not isinstance(receipt_value, Mapping):
            _fail("attempt-classification", "classification receipt is not an object")
        if _canonical_json_bytes(receipt_value) + b"\n" != receipt:
            _fail(
                "attempt-classification",
                "classification receipt is not canonical JSON",
            )
        _exact_keys(
            receipt_value, expected_receipt_keys, label="classification receipt",
        )
        if (
            receipt_value.get("schema_version") != classification["schema_version"]
            or receipt_value.get("event") != "classification-receipt"
            or receipt_value.get("freeze_id") != classification["freeze_id"]
            or receipt_value.get("slot_id") != classification["slot_id"]
            or receipt_value.get("capability_digest_sha256")
            != classification["capability_digest_sha256"]
            or receipt_value.get("authority_id") != classification["authority_id"]
            or receipt_value.get("authority_policy_sha256")
            != classification["authority_policy_sha256"]
            or receipt_value.get("external_evidence_sha256")
            != classification["external_evidence_sha256"]
            or receipt_value.get("classified_at") != classification["classified_at"]
        ):
            _fail(
                "attempt-classification",
                "classification receipt is not capability-bound",
            )
        if classification["schema_version"] in {
            _ATTEMPT_REGISTRY_SCHEMA_VERSION_V2,
            ATTEMPT_REGISTRY_SCHEMA_VERSION,
        }:
            if (
                receipt_value.get("pre_observation_failure_reason")
                != classification["pre_observation_failure_reason"]
                or receipt_value.get("pre_observation_seal_sha256")
                != classification["pre_observation_seal_sha256"]
            ):
                _fail(
                    "attempt-classification",
                    "classification receipt is not seal-bound",
                )
        elif (
            receipt_value.get("failure_reason") != classification["failure_reason"]
            or receipt_value.get("performance_output_read") is not False
        ):
            _fail(
                "attempt-classification",
                "classification receipt is not capability-bound",
            )


def _load_attempt_registry_bytes(
    data: bytes,
    *,
    label: str = "attempt registry",
) -> tuple[dict[str, Any], ...]:
    return _attempt_core_call(
        _attempt_core._load_registry_bytes,
        data,
        profile=_S8C_ATTEMPT_PROFILE,
        label=label,
    )


def _attempt_registry_target(
    repository_root: Path,
    registry_path: Path = DEFAULT_ATTEMPT_REGISTRY_PATH,
    *,
    create_parent: bool,
) -> tuple[Path, Path, str]:
    root = _repository_root(repository_root)
    _candidate, relative_path, relative = _registry_relative_target(
        Path(registry_path), root,
    )
    if relative != DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix():
        _fail("attempt-registry-path", "attempt registry path is not canonical")
    target, canonical_relative = _registry_target(
        DEFAULT_ATTEMPT_REGISTRY_PATH, root, create_parent=create_parent,
    )
    return target, relative_path, canonical_relative


def _write_create_only(
    *,
    repository_root: Path,
    relative_path: Path,
    payload: bytes,
    gate: str,
) -> Path:
    parent_fd = _open_registry_parent(
        repository_root, relative_path.parent, create=True,
    )
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(relative_path.name, flags, 0o644, dir_fd=parent_fd)
        except FileExistsError as exc:
            raise TrialRegistryError(f"[{gate}] create-only path already exists") from exc
        total_written = 0
        try:
            view = memoryview(payload)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError("create-only write did not advance")
                total_written += written
                view = view[written:]
            os.fsync(fd)
            os.fsync(parent_fd)
        except BaseException:
            try:
                created = os.fstat(fd)
                if created.st_size == total_written:
                    named = os.stat(
                        relative_path.name, dir_fd=parent_fd,
                        follow_symlinks=False,
                    )
                    if (named.st_dev, named.st_ino) == (created.st_dev, created.st_ino):
                        os.unlink(relative_path.name, dir_fd=parent_fd)
            except OSError:
                pass
            raise
        finally:
            os.close(fd)
    except TrialRegistryError:
        raise
    except OSError as exc:
        raise TrialRegistryError(f"[{gate}] create-only write failed: {exc}") from exc
    finally:
        os.close(parent_fd)
    return repository_root / relative_path


def create_attempt_registry_genesis(
    *,
    repository_root: Path,
    manifest_path: Path,
    manifest_sha256: str,
    freeze_id: str,
    prereg_generation: int,
    slots: Sequence[Mapping[str, Any]],
    retryable_failure_reasons: Sequence[str] = tuple(
        sorted(ATTEMPT_RETRYABLE_FAILURE_REASONS)
    ),
    registry_path: Path = DEFAULT_ATTEMPT_REGISTRY_PATH,
) -> Path:
    """Create the one freeze-wide root before any performance observation.

    A genesis with the complete slot set is accepted only at the canonical
    path when that path is absent; a second genesis, a late slot, or a retry
    reason outside the exact closed set is rejected. A valid first creation
    has one positive ``prereg_generation`` exactly repeated by every slot;
    a missing, different, boolean, or non-positive slot value is rejected.
    """
    root = _repository_root(repository_root)
    _attempt_registry_target(root, registry_path, create_parent=True)
    if not isinstance(manifest_sha256, str) or _SHA256_RE.fullmatch(manifest_sha256) is None:
        _fail("attempt-registry-genesis", "manifest_sha256 is invalid")
    _attempt_text(freeze_id, label="freeze_id")
    if type(prereg_generation) is not int or prereg_generation < 1:
        _fail(
            "attempt-prereg-generation",
            "prereg_generation must be a positive int",
        )
    for index, slot in enumerate(slots):
        if (
            not isinstance(slot, Mapping)
            or type(slot.get("prereg_generation")) is not int
            or slot.get("prereg_generation") != prereg_generation
        ):
            _fail(
                "attempt-prereg-generation",
                "prereg_generation differs from "
                f"slots[{index}].prereg_generation",
            )
    _repo_path, manifest_relative = _repo_relative(
        Path(manifest_path), root, label="manifest",
    )
    reasons = list(retryable_failure_reasons)
    rows = _attempt_core_call(
        _attempt_core.create_attempt_registry_genesis,
        profile=_S8C_ATTEMPT_PROFILE,
        freeze_id=freeze_id,
        manifest_path=_PurePosixPath(manifest_relative),
        manifest_sha256=manifest_sha256,
        slots=slots,
        retryable_failure_reasons=reasons,
    )
    payload = _canonical_json_bytes(rows[0]) + b"\n"
    _candidate, relative_path, _relative = _attempt_registry_target(
        root, registry_path, create_parent=True,
    )
    return _write_create_only(
        repository_root=root,
        relative_path=relative_path,
        payload=payload,
        gate="attempt-registry-genesis",
    )


def _attempt_tree_paths(
    repository_root: Path,
    *,
    commit_id: str,
) -> tuple[tuple[str, bytes], ...]:
    listing = _git(
        repository_root,
        ("ls-tree", "-r", "-z", "--full-tree", commit_id),
    )
    if listing.returncode != 0:
        raise TrialRegistryError("[git-operational] attempt registry tree walk failed")
    result: list[tuple[str, bytes]] = []
    for entry in (item for item in listing.stdout.split(b"\0") if item):
        metadata, separator, entry_path = entry.partition(b"\t")
        fields = metadata.split()
        if separator != b"\t" or len(fields) != 3 or fields[1] != b"blob":
            continue
        try:
            path = entry_path.decode("utf-8")
            blob_id = fields[2].decode("ascii")
        except UnicodeDecodeError as exc:
            raise TrialRegistryError("[git-operational] attempt tree path is not valid UTF-8") from exc
        blob = _git(repository_root, ("cat-file", "blob", blob_id))
        if blob.returncode != 0:
            raise TrialRegistryError("[git-operational] attempt tree blob cannot be read")
        result.append((path, blob.stdout))
    return tuple(result)


def _looks_like_attempt_genesis(data: bytes) -> bool:
    if not data:
        return False
    first_line = data.splitlines()[0]
    if not any(
        schema.encode("ascii") in first_line
        for schema in _ATTEMPT_REGISTRY_SCHEMA_VERSIONS
    ):
        return False
    try:
        value = _decode_json(first_line, label="attempt history root")
    except TrialRegistryError:
        return False
    return (
        isinstance(value, Mapping)
        and value.get("schema_version") in _ATTEMPT_REGISTRY_SCHEMA_VERSIONS
        and value.get("event") == "freeze"
    )


def _assert_attempt_registry_history_append_only(
    *,
    repository_root: Path,
    relative_path: str = DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(),
    current_bytes: bytes | None = None,
) -> bytes | None:
    """Check every ref for one canonical append-only attempt-registry root.

    A canonical root and strict prefix extensions across all refs are accepted;
    a second freeze row, an alternate-path root, deletion/recreation, or a
    root reachable only from an unmerged ref is rejected.  The scan uses
    ``git rev-list --all`` deliberately, so current-HEAD ancestry alone is not
    evidence for this gate.
    """
    if relative_path != DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix():
        _fail("attempt-registry-history", "history path is not canonical")
    root = _repository_root(repository_root)
    _assert_no_grafts_or_replace_refs(root)
    _assert_not_shallow(root)
    commits = _git(root, ("rev-list", "--all", "--topo-order", "--reverse"))
    if commits.returncode != 0:
        raise TrialRegistryError("[git-operational] attempt registry full history walk failed")
    previous: bytes | None = None
    canonical_seen = False
    for raw_commit in commits.stdout.splitlines():
        try:
            commit_id = raw_commit.decode("ascii")
        except UnicodeDecodeError as exc:
            raise TrialRegistryError("[git-operational] attempt history commit is not ASCII") from exc
        _assert_full_commit_id(commit_id, label="attempt history commit")
        tree_paths = _attempt_tree_paths(root, commit_id=commit_id)
        canonical = next((blob for path, blob in tree_paths if path == relative_path), None)
        if canonical is None:
            if canonical_seen:
                _fail("attempt-registry-history", "canonical attempt registry was deleted")
        else:
            canonical_seen = True
            _load_attempt_registry_bytes(canonical, label=f"attempt registry at {commit_id}")
            if previous is not None and canonical != previous and (
                not canonical.startswith(previous) or len(canonical) <= len(previous)
            ):
                _fail(
                    "attempt-registry-history",
                    "attempt registry history is not a strict prefix extension",
                )
            previous = canonical
        for path, blob in tree_paths:
            if path != relative_path and _looks_like_attempt_genesis(blob):
                _fail(
                    "attempt-registry-history",
                    "alternate attempt registry genesis exists on a ref (second root)",
                )
    if current_bytes is not None:
        _load_attempt_registry_bytes(current_bytes, label="working attempt registry")
        if previous is not None and not current_bytes.startswith(previous):
            _fail(
                "attempt-registry-history",
                "working attempt registry does not extend committed history",
            )
    return previous


def load_attempt_registry(
    repository_root: Path,
    *,
    registry_path: Path = DEFAULT_ATTEMPT_REGISTRY_PATH,
    prereg_content_commit: str | None = None,
    prereg_effective_commit: str | None = None,
    freeze_id: str | None = None,
    manifest_path: Path | None = None,
    manifest_sha256: str | None = None,
) -> tuple[dict[str, Any], ...]:
    """Accept the fixed registry when its rows and all-ref history are valid.

    A canonical genesis with strict prefix extensions is accepted; missing,
    replaced, deleted, recreated, or alternate-root history is rejected.
    """
    root = _repository_root(repository_root)
    target, _relative_path, relative = _attempt_registry_target(
        root, registry_path, create_parent=False,
    )
    data = _read_regular_bytes(
        target, gate="attempt-registry-read", label="attempt registry",
    )
    _assert_attempt_registry_history_append_only(
        repository_root=root, relative_path=relative, current_bytes=data,
    )
    rows = _load_attempt_registry_bytes(data)
    genesis = rows[0]
    if freeze_id is not None and genesis["freeze_id"] != freeze_id:
        _fail("attempt-registry-binding", "genesis freeze_id differs from effective binding")
    if manifest_sha256 is not None and genesis["manifest_sha256"] != manifest_sha256:
        _fail("attempt-registry-binding", "genesis manifest_sha256 differs from effective binding")
    if manifest_path is not None:
        _resolved, supplied_relative = _repo_relative(
            Path(manifest_path), root, label="manifest",
        )
        if genesis["manifest_path"] != supplied_relative:
            _fail("attempt-registry-binding", "genesis manifest_path differs from binding")
    _assert_attempt_registry_rows(
        rows,
        repository_root=root,
        expected_prereg_content_commit=prereg_content_commit,
        expected_prereg_effective_commit=prereg_effective_commit,
    )
    return rows


def _assert_locked_attempt_registry_identity(
    *,
    repository_root: Path,
    relative_path: Path,
    parent_fd: int,
    registry_fd: int,
    phase: str,
) -> os.stat_result:
    """Require held parent/file descriptors to remain canonical by name."""
    rebound_parent_fd = _open_registry_parent(
        repository_root, relative_path.parent, create=False,
    )
    try:
        held_parent = os.fstat(parent_fd)
        rebound_parent = os.fstat(rebound_parent_fd)
        if (
            held_parent.st_dev,
            held_parent.st_ino,
        ) != (
            rebound_parent.st_dev,
            rebound_parent.st_ino,
        ):
            _fail(
                "attempt-registry-path",
                f"attempt registry parent changed {phase}",
            )
    finally:
        os.close(rebound_parent_fd)

    info = os.fstat(registry_fd)
    if not stat.S_ISREG(info.st_mode):
        _fail(
            "attempt-registry-path",
            f"attempt registry is not a regular file {phase}",
        )
    try:
        rebound = os.stat(
            relative_path.name,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        _fail(
            "attempt-registry-path",
            f"attempt registry path disappeared {phase}",
        )
    if not stat.S_ISREG(rebound.st_mode):
        _fail(
            "attempt-registry-path",
            f"attempt registry path is not a regular file {phase}",
        )
    if (rebound.st_dev, rebound.st_ino) != (info.st_dev, info.st_ino):
        _fail(
            "attempt-registry-path",
            f"attempt registry path changed {phase}",
        )
    return info


def _read_locked_attempt_registry_fd(
    fd: int,
    *,
    size: int,
    gate: str,
) -> bytes:
    current = bytearray()
    offset = 0
    while offset < size:
        chunk = os.pread(fd, min(1024 * 1024, size - offset), offset)
        if not chunk:
            _fail(gate, "attempt registry read stopped early")
        current.extend(chunk)
        offset += len(chunk)
    return bytes(current)


def _attempt_registry_stat_identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
    )


class _LockedAttemptRegistrySnapshot:
    """A canonical shared-lock snapshot retained through receipt publication."""

    def __init__(
        self,
        *,
        repository_root: Path,
        relative_path: Path,
        parent_fd: int,
        registry_fd: int,
        info: os.stat_result,
        data: bytes,
    ) -> None:
        self.repository_root = repository_root
        self.relative_path = relative_path
        self.parent_fd = parent_fd
        self.registry_fd = registry_fd
        self.identity = _attempt_registry_stat_identity(info)
        self.data = data
        self.closed = False

    def validate(self) -> None:
        if self.closed:
            _fail("attempt-acceptance", "attempt registry snapshot lock is closed")
        before = _assert_locked_attempt_registry_identity(
            repository_root=self.repository_root,
            relative_path=self.relative_path,
            parent_fd=self.parent_fd,
            registry_fd=self.registry_fd,
            phase="during formal acceptance",
        )
        current = _read_locked_attempt_registry_fd(
            self.registry_fd,
            size=before.st_size,
            gate="attempt-acceptance",
        )
        after = os.fstat(self.registry_fd)
        if (
            _attempt_registry_stat_identity(before)
            != _attempt_registry_stat_identity(after)
            or _attempt_registry_stat_identity(after) != self.identity
            or current != self.data
        ):
            _fail(
                "attempt-acceptance",
                "attempt registry snapshot changed during formal acceptance",
            )
        _assert_locked_attempt_registry_identity(
            repository_root=self.repository_root,
            relative_path=self.relative_path,
            parent_fd=self.parent_fd,
            registry_fd=self.registry_fd,
            phase="during formal acceptance",
        )

    def assert_rows(self, rows: Sequence[Mapping[str, Any]]) -> None:
        self.validate()
        replayed = b"".join(
            _canonical_json_bytes(row) + b"\n" for row in rows
        )
        if replayed != self.data:
            _fail(
                "attempt-acceptance",
                "strict rows differ from the locked attempt registry snapshot",
            )

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        os.close(self.registry_fd)
        os.close(self.parent_fd)


def _open_locked_attempt_registry_snapshot(
    *,
    repository_root: Path,
    registry_path: Path,
) -> _LockedAttemptRegistrySnapshot:
    """Open the updater's flock target and retain one shared snapshot."""
    root = _repository_root(repository_root)
    target, relative_path, relative = _attempt_registry_target(
        root, registry_path, create_parent=False,
    )
    if not target.exists() or target.is_symlink():
        _fail("attempt-registry-path", "attempt registry genesis is absent")
    history_tip = _assert_attempt_registry_history_append_only(
        repository_root=root,
        relative_path=relative,
    )
    parent_fd = _open_registry_parent(root, relative_path.parent, create=False)
    registry_fd: int | None = None
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        registry_fd = os.open(
            relative_path.name,
            flags,
            dir_fd=parent_fd,
        )
        fcntl.flock(registry_fd, fcntl.LOCK_SH)
        before = _assert_locked_attempt_registry_identity(
            repository_root=root,
            relative_path=relative_path,
            parent_fd=parent_fd,
            registry_fd=registry_fd,
            phase="after shared lock",
        )
        data = _read_locked_attempt_registry_fd(
            registry_fd,
            size=before.st_size,
            gate="attempt-acceptance",
        )
        after = os.fstat(registry_fd)
        if _attempt_registry_stat_identity(before) != (
            _attempt_registry_stat_identity(after)
        ):
            _fail(
                "attempt-acceptance",
                "attempt registry changed during locked snapshot read",
            )
        _assert_locked_attempt_registry_identity(
            repository_root=root,
            relative_path=relative_path,
            parent_fd=parent_fd,
            registry_fd=registry_fd,
            phase="after shared snapshot read",
        )
        if history_tip is not None and not data.startswith(history_tip):
            _fail(
                "attempt-registry-history",
                "working attempt registry changed under shared lock",
            )
        _load_attempt_registry_bytes(data, label="locked attempt registry snapshot")
        return _LockedAttemptRegistrySnapshot(
            repository_root=root,
            relative_path=relative_path,
            parent_fd=parent_fd,
            registry_fd=registry_fd,
            info=after,
            data=data,
        )
    except BaseException:
        if registry_fd is not None:
            os.close(registry_fd)
        os.close(parent_fd)
        raise


def _locked_attempt_registry_update(
    *,
    repository_root: Path,
    registry_path: Path,
    update,
):
    root = _repository_root(repository_root)
    target, relative_path, relative = _attempt_registry_target(
        root, registry_path, create_parent=False,
    )
    if not target.exists() or target.is_symlink():
        _fail("attempt-registry-path", "attempt registry genesis is absent")
    history_tip = _assert_attempt_registry_history_append_only(
        repository_root=root,
        relative_path=relative,
    )
    parent_fd = _open_registry_parent(root, relative_path.parent, create=False)
    try:
        flags = os.O_RDWR | os.O_APPEND
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(relative_path.name, flags, dir_fd=parent_fd)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            info = _assert_locked_attempt_registry_identity(
                repository_root=root,
                relative_path=relative_path,
                parent_fd=parent_fd,
                registry_fd=fd,
                phase="after exclusive lock",
            )
            current_bytes = _read_locked_attempt_registry_fd(
                fd,
                size=info.st_size,
                gate="attempt-registry-read",
            )
            after_read = os.fstat(fd)
            if _attempt_registry_stat_identity(info) != (
                _attempt_registry_stat_identity(after_read)
            ):
                _fail(
                    "attempt-registry-read",
                    "attempt registry changed during locked read",
                )
            _assert_locked_attempt_registry_identity(
                repository_root=root,
                relative_path=relative_path,
                parent_fd=parent_fd,
                registry_fd=fd,
                phase="after locked read",
            )
            rows = _load_attempt_registry_bytes(current_bytes)
            if history_tip is not None and not current_bytes.startswith(history_tip):
                _fail("attempt-registry-history", "working attempt registry changed under lock")
            payload, result = update(rows)
            before_append = _assert_locked_attempt_registry_identity(
                repository_root=root,
                relative_path=relative_path,
                parent_fd=parent_fd,
                registry_fd=fd,
                phase="after locked update",
            )
            if _attempt_registry_stat_identity(before_append) != (
                _attempt_registry_stat_identity(after_read)
            ):
                _fail(
                    "attempt-registry-read",
                    "attempt registry changed during locked update",
                )
            if payload is not None:
                candidate = current_bytes + payload
                _load_attempt_registry_bytes(candidate, label="attempt registry append")
                _assert_locked_attempt_registry_identity(
                    repository_root=root,
                    relative_path=relative_path,
                    parent_fd=parent_fd,
                    registry_fd=fd,
                    phase="before locked append",
                )
                view = memoryview(payload)
                while view:
                    written = os.write(fd, view)
                    if written <= 0:
                        raise OSError("attempt registry append did not advance")
                    view = view[written:]
                appended = _assert_locked_attempt_registry_identity(
                    repository_root=root,
                    relative_path=relative_path,
                    parent_fd=parent_fd,
                    registry_fd=fd,
                    phase="after locked append",
                )
                if appended.st_size != after_read.st_size + len(payload):
                    _fail(
                        "attempt-registry-io",
                        "attempt registry size differs after locked append",
                    )
                os.fsync(fd)
                os.fsync(parent_fd)
                synced = _assert_locked_attempt_registry_identity(
                    repository_root=root,
                    relative_path=relative_path,
                    parent_fd=parent_fd,
                    registry_fd=fd,
                    phase="after locked append fsync",
                )
                if synced.st_size != appended.st_size:
                    _fail(
                        "attempt-registry-io",
                        "attempt registry size changed after locked append fsync",
                    )
            return result
        finally:
            os.close(fd)
    except TrialRegistryError:
        raise
    except OSError as exc:
        raise TrialRegistryError(f"[attempt-registry-io] update failed: {exc}") from exc
    finally:
        os.close(parent_fd)


def _assert_attempt_capability(capability: AttemptSlotCapability) -> None:
    if (
        type(capability) is not AttemptSlotCapability
        or capability._seal is not _ATTEMPT_SLOT_CAPABILITY_SEAL
    ):
        _fail("attempt-capability", "slot capability was not issued by the registry")
    _assert_full_commit_id(capability.prereg_content_commit, label="prereg_content_commit")
    _assert_full_commit_id(capability.prereg_effective_commit, label="prereg_effective_commit")
    _assert_full_commit_id(capability.prereg_commit, label="prereg_commit")
    _attempt_digest(
        capability.pre_observation_seal_sha256,
        label="pre_observation_seal_sha256",
    )
    if capability.prereg_commit != capability.prereg_content_commit:
        _fail("attempt-capability", "slot capability prereg_commit differs from P")
    slot = {
        "slot_id": capability.slot_id,
        "trial_id": capability.trial_id,
        "arm": capability.arm,
        "holdout": capability.holdout,
        "campaign_id": capability.campaign_id,
        "prereg_generation": capability.prereg_generation,
        "replicate_index": capability.replicate_index,
        "attempt_index": capability.attempt_index,
        "schedule_row_sha256": capability.schedule_row_sha256,
    }
    _parse_attempt_slot(slot, label="issued attempt capability")
    expected = _attempt_capability_digest(
        freeze_id=capability.freeze_id,
        slot=slot,
        prereg_content_commit=capability.prereg_content_commit,
        prereg_effective_commit=capability.prereg_effective_commit,
    )
    if expected != capability.capability_digest_sha256:
        _fail("attempt-capability", "slot capability digest was replaced")


def _reserve_attempt_slot(
    *,
    profile: _attempt_core.DomainProfile[Any, Any],
    repository_root: Path,
    freeze_id: str,
    slot_id: str,
    prereg_content_commit: str,
    prereg_effective_commit: str,
    run_start_receipt_sha256: str,
    process_identity: Mapping[str, Any],
    started_at: str,
    registry_path: Path = DEFAULT_ATTEMPT_REGISTRY_PATH,
) -> AttemptSlotCapability:
    """Consume one declared slot before the first performance observation."""
    root = _repository_root(repository_root)
    _attempt_text(freeze_id, label="freeze_id")
    _assert_full_commit_id(prereg_content_commit, label="prereg_content_commit")
    _assert_full_commit_id(prereg_effective_commit, label="prereg_effective_commit")
    _attempt_digest(run_start_receipt_sha256, label="run_start_receipt_sha256")
    checked_process = _attempt_process_identity(
        dict(process_identity), label="process_identity",
    )
    _attempt_text(started_at, label="started_at")
    binding = (prereg_content_commit, prereg_effective_commit)

    def append_start(rows):
        candidate = _attempt_core_call(
            _attempt_core.reserve_attempt_slot,
            rows,
            profile=profile,
            freeze_id=freeze_id,
            slot_id=slot_id,
            binding=binding,
            run_start_receipt_sha256=run_start_receipt_sha256,
            process_identity=checked_process,
            started_at=started_at,
        )
        slot = next(
            item for item in candidate[0]["slots"] if item["slot_id"] == slot_id
        )
        start, seal = candidate[-2:]
        digest = _attempt_core.capability_digest(
            profile=profile,
            schema_version=ATTEMPT_REGISTRY_SCHEMA_VERSION,
            freeze_id=freeze_id,
            slot=slot,
            binding=binding,
        )
        capability = AttemptSlotCapability(
            repository_root=root,
            registry_path=_attempt_registry_target(
                root, registry_path, create_parent=False,
            )[0],
            freeze_id=freeze_id,
            slot_id=slot["slot_id"],
            trial_id=slot["trial_id"],
            arm=slot["arm"],
            holdout=slot["holdout"],
            campaign_id=slot["campaign_id"],
            prereg_generation=slot["prereg_generation"],
            replicate_index=slot["replicate_index"],
            attempt_index=slot["attempt_index"],
            schedule_row_sha256=slot["schedule_row_sha256"],
            prereg_commit=prereg_content_commit,
            prereg_content_commit=prereg_content_commit,
            prereg_effective_commit=prereg_effective_commit,
            pre_observation_seal_sha256=seal["event_sha256"],
            capability_digest_sha256=digest,
            _seal=_ATTEMPT_SLOT_CAPABILITY_SEAL,
        )
        payload = b"".join(
            _canonical_json_bytes(row) + b"\n"
            for row in (start, seal)
        )
        return payload, capability

    return _locked_attempt_registry_update(
        repository_root=root,
        registry_path=registry_path,
        update=append_start,
    )


def reserve_attempt_slot(
    *,
    repository_root: Path,
    freeze_id: str,
    slot_id: str,
    prereg_content_commit: str,
    prereg_effective_commit: str,
    run_start_receipt_sha256: str,
    process_identity: Mapping[str, Any],
    started_at: str,
    registry_path: Path = DEFAULT_ATTEMPT_REGISTRY_PATH,
) -> AttemptSlotCapability:
    """Consume one declared slot through the compatibility profile."""
    return _reserve_attempt_slot(
        profile=_S8C_ATTEMPT_PROFILE,
        repository_root=repository_root,
        freeze_id=freeze_id,
        slot_id=slot_id,
        prereg_content_commit=prereg_content_commit,
        prereg_effective_commit=prereg_effective_commit,
        run_start_receipt_sha256=run_start_receipt_sha256,
        process_identity=process_identity,
        started_at=started_at,
        registry_path=registry_path,
    )


def reserve_formal_attempt_slot(
    *,
    repository_root: Path,
    freeze_id: str,
    slot_id: str,
    prereg_content_commit: str,
    prereg_effective_commit: str,
    run_start_receipt_sha256: str,
    process_identity: Mapping[str, Any],
    started_at: str,
    registry_path: Path = DEFAULT_ATTEMPT_REGISTRY_PATH,
) -> AttemptSlotCapability:
    """Consume one declared slot after strict replay of the shared prefix."""
    return _reserve_attempt_slot(
        profile=_S8C_FORMAL_ATTEMPT_PROFILE,
        repository_root=repository_root,
        freeze_id=freeze_id,
        slot_id=slot_id,
        prereg_content_commit=prereg_content_commit,
        prereg_effective_commit=prereg_effective_commit,
        run_start_receipt_sha256=run_start_receipt_sha256,
        process_identity=process_identity,
        started_at=started_at,
        registry_path=registry_path,
    )


record_attempt_start = reserve_attempt_slot


def _attempt_receipt_payload(
    *,
    capability: AttemptSlotCapability,
    pre_observation_failure_reason: str | None,
    authority_id: str,
    authority_policy_sha256: str,
    external_evidence_sha256: str,
    classified_at: str,
) -> dict[str, Any]:
    return _attempt_core_call(
        _attempt_core._receipt_payload,
        profile=_S8C_ATTEMPT_PROFILE,
        schema_version=ATTEMPT_REGISTRY_SCHEMA_VERSION,
        freeze_id=capability.freeze_id,
        slot_id=capability.slot_id,
        capability_digest_sha256=capability.capability_digest_sha256,
        pre_observation_failure_reason=pre_observation_failure_reason,
        authority_id=authority_id,
        authority_policy_sha256=authority_policy_sha256,
        external_evidence_sha256=external_evidence_sha256,
        classified_at=classified_at,
        pre_observation_seal_sha256=capability.pre_observation_seal_sha256,
    )


def classify_attempt(
    capability: AttemptSlotCapability,
    *,
    pre_observation_failure_reason: str | None,
    authority_id: str,
    authority_policy_sha256: str,
    external_evidence_sha256: str,
    classified_at: str,
) -> dict[str, Any]:
    """Create one capability-bound classification receipt and append its row."""
    _assert_attempt_capability(capability)
    if pre_observation_failure_reason is not None:
        _attempt_text(
            pre_observation_failure_reason,
            label="pre_observation_failure_reason",
        )
    authority_id = _attempt_text(authority_id, label="authority_id")
    _attempt_digest(authority_policy_sha256, label="authority_policy_sha256")
    _attempt_digest(external_evidence_sha256, label="external_evidence_sha256")
    classified_at = _attempt_text(classified_at, label="classified_at")
    receipt = _attempt_receipt_payload(
        capability=capability,
        pre_observation_failure_reason=pre_observation_failure_reason,
        authority_id=authority_id,
        authority_policy_sha256=authority_policy_sha256,
        external_evidence_sha256=external_evidence_sha256,
        classified_at=classified_at,
    )
    receipt_bytes = _canonical_json_bytes(receipt) + b"\n"
    receipt_digest = hashlib.sha256(receipt_bytes).hexdigest()
    receipt_relative = (
        Path(_S8C_ATTEMPT_PROFILE.layout.classification_receipt_dir)
        / f"{receipt_digest}.json"
    )
    _write_create_only(
        repository_root=capability.repository_root,
        relative_path=receipt_relative,
        payload=receipt_bytes,
        gate="attempt-classification-receipt",
    )
    binding = (
        capability.prereg_content_commit,
        capability.prereg_effective_commit,
    )

    def append_classification(rows):
        candidate, core_receipt = _attempt_core_call(
            _attempt_core.classify_attempt,
            rows,
            profile=_S8C_ATTEMPT_PROFILE,
            freeze_id=capability.freeze_id,
            slot_id=capability.slot_id,
            binding=binding,
            capability_digest_sha256=capability.capability_digest_sha256,
            pre_observation_failure_reason=pre_observation_failure_reason,
            authority_id=authority_id,
            authority_policy_sha256=authority_policy_sha256,
            external_evidence_sha256=external_evidence_sha256,
            classified_at=classified_at,
        )
        if _canonical_json_bytes(core_receipt) != _canonical_json_bytes(receipt):
            _fail(
                "attempt-classification",
                "classification receipt is not capability-bound",
            )
        row = candidate[-1]
        return _canonical_json_bytes(row) + b"\n", dict(core_receipt)

    result = _locked_attempt_registry_update(
        repository_root=capability.repository_root,
        registry_path=capability.registry_path,
        update=append_classification,
    )
    object.__setattr__(capability, "_classification_receipt_sha256", receipt_digest)
    object.__setattr__(
        capability,
        "_classification_owner",
        (os.getpid(), threading.get_ident()),
    )
    return result


classify_attempt_failure = classify_attempt


def begin_attempt_observation(capability: AttemptSlotCapability) -> dict[str, Any]:
    """Append the registry-issued boundary immediately before observation."""
    _assert_attempt_capability(capability)

    def append_observation_start(rows):
        classifications = [
            row for row in rows
            if row.get("event") == "classification"
            and row.get("slot_id") == capability.slot_id
        ]
        if len(classifications) == 1 and classifications[0].get(
            "pre_observation_seal_sha256"
        ) != capability.pre_observation_seal_sha256:
            _fail(
                "attempt-slot",
                "capability pre-observation seal differs from classification",
            )
        candidate = _attempt_core_call(
            _attempt_core.begin_attempt_observation,
            rows,
            profile=_S8C_ATTEMPT_PROFILE,
            freeze_id=capability.freeze_id,
            slot_id=capability.slot_id,
        )
        row = candidate[-1]
        return _canonical_json_bytes(row) + b"\n", dict(row)

    return _locked_attempt_registry_update(
        repository_root=capability.repository_root,
        registry_path=capability.registry_path,
        update=append_observation_start,
    )


def _record_attempt_terminal(
    capability: AttemptSlotCapability,
    *,
    profile: _attempt_core.DomainProfile[Any, Any],
    terminal_status: str,
    raw_output_sha256: str,
    report_sha256: str | None,
    observation_sha256: str | None,
    primary_value: Any,
    finished_at: str,
    failure_reason: str | None = None,
) -> None:
    """Append one immutable terminal row after capability classification."""
    _assert_attempt_capability(capability)
    if terminal_status not in ATTEMPT_STATUSES:
        _fail("attempt-terminal", "terminal_status is outside the closed set")
    _attempt_digest(raw_output_sha256, label="raw_output_sha256")
    _attempt_digest(report_sha256, label="report_sha256", nullable=True)
    _attempt_digest(observation_sha256, label="observation_sha256", nullable=True)
    _attempt_text(finished_at, label="finished_at")
    if failure_reason is not None:
        _attempt_text(failure_reason, label="failure_reason")
    binding = (
        capability.prereg_content_commit,
        capability.prereg_effective_commit,
    )

    def append_terminal(rows):
        classifications = [
            row for row in rows
            if row.get("event") == "classification"
            and row.get("slot_id") == capability.slot_id
        ]
        starts = [
            row for row in rows
            if row.get("event") == "start"
            and row.get("slot_id") == capability.slot_id
        ]
        if len(starts) != 1 or len(classifications) != 1:
            _fail(
                "attempt-terminal",
                "terminal requires one start and one classification",
            )
        classification = classifications[0]
        if classification.get("schema_version") != ATTEMPT_REGISTRY_SCHEMA_VERSION:
            _fail(
                "attempt-phase-order",
                "current terminal cannot bind a legacy classification",
            )
        if classification["pre_observation_seal_sha256"] != (
            capability.pre_observation_seal_sha256
        ):
            _fail(
                "attempt-slot",
                "capability pre-observation seal differs from classification",
            )
        if capability._classification_owner != (os.getpid(), threading.get_ident()):
            _fail(
                "attempt-terminal",
                "terminal append is not owned by the classification executor",
            )
        if capability._classification_receipt_sha256 != (
            classification["classification_receipt_sha256"]
        ):
            _fail(
                "attempt-terminal",
                "terminal append classification receipt differs from capability",
            )
        candidate = _attempt_core_call(
            _attempt_core.record_attempt_terminal,
            rows,
            profile=profile,
            freeze_id=capability.freeze_id,
            slot_id=capability.slot_id,
            binding=binding,
            terminal_status=terminal_status,
            raw_output_sha256=raw_output_sha256,
            report_sha256=report_sha256,
            observation_sha256=observation_sha256,
            primary_value=primary_value,
            finished_at=finished_at,
            failure_reason=failure_reason,
        )
        terminal = candidate[-1]
        return _canonical_json_bytes(terminal) + b"\n", None

    _locked_attempt_registry_update(
        repository_root=capability.repository_root,
        registry_path=capability.registry_path,
        update=append_terminal,
    )


def record_attempt_terminal(
    capability: AttemptSlotCapability,
    *,
    terminal_status: str,
    raw_output_sha256: str,
    report_sha256: str | None,
    observation_sha256: str | None,
    primary_value: Any,
    finished_at: str,
    failure_reason: str | None = None,
) -> None:
    """Append one terminal row through the compatibility profile."""
    _record_attempt_terminal(
        capability,
        profile=_S8C_ATTEMPT_PROFILE,
        terminal_status=terminal_status,
        raw_output_sha256=raw_output_sha256,
        report_sha256=report_sha256,
        observation_sha256=observation_sha256,
        primary_value=primary_value,
        finished_at=finished_at,
        failure_reason=failure_reason,
    )


def record_formal_attempt_terminal(
    capability: AttemptSlotCapability,
    *,
    terminal_status: str,
    raw_output_sha256: str,
    report_sha256: str | None,
    observation_sha256: str | None,
    primary_value: Any,
    finished_at: str,
    failure_reason: str | None = None,
) -> None:
    """Append one terminal row only after strict reason replay succeeds."""
    _record_attempt_terminal(
        capability,
        profile=_S8C_FORMAL_ATTEMPT_PROFILE,
        terminal_status=terminal_status,
        raw_output_sha256=raw_output_sha256,
        report_sha256=report_sha256,
        observation_sha256=observation_sha256,
        primary_value=primary_value,
        finished_at=finished_at,
        failure_reason=failure_reason,
    )


def _assert_attempt_registry_acceptance(
    *,
    profile: _attempt_core.DomainProfile[Any, Any],
    repository_root: Path,
    manifest_path: Path,
    manifest: TrialManifest,
    effective_binding: PreregEffectiveBinding,
    effective_commit: str,
    report_paths: Sequence[Path] = (),
    registry_path: Path = DEFAULT_ATTEMPT_REGISTRY_PATH,
) -> tuple[dict[str, Any], ...]:
    """Require manifest, effective binding, slots, and observed report rows to agree.

    Manifest ``trials`` and runtime report ``cells`` are checked as separate
    objects: a manifest/slot set cannot substitute for a runtime cell, and a
    runtime cell cannot create or remove a pre-registered trial slot.
    """
    root = _repository_root(repository_root)
    if effective_binding.manifest_sha256 != manifest.sha256:
        _fail("attempt-acceptance", "effective binding manifest hash differs")
    rows = load_attempt_registry(
        root,
        registry_path=registry_path,
        prereg_content_commit=effective_binding.prereg_content_commit,
        prereg_effective_commit=effective_commit,
        freeze_id=effective_binding.freeze_id,
        manifest_path=manifest_path,
        manifest_sha256=manifest.sha256,
    )
    rows = _attempt_core_call(
        _attempt_core.assert_registry_rows,
        rows,
        profile=profile,
        expected_binding=(
            effective_binding.prereg_content_commit,
            effective_commit,
        ),
    )
    attempt_registry_file, _relative_path, _relative = _attempt_registry_target(
        root, registry_path, create_parent=False,
    )
    attempt_registry_bytes = _read_regular_bytes(
        attempt_registry_file,
        gate="attempt-acceptance",
        label="attempt registry",
    )
    initial_blob = _blob_at_commit(
        root,
        commit_id=effective_binding.prereg_content_commit,
        relative_path=effective_binding.attempt_registry_path,
    )
    if (
        initial_blob is None
        or hashlib.sha256(initial_blob).hexdigest()
        != effective_binding.attempt_registry_initial_sha256
        or not attempt_registry_bytes.startswith(initial_blob)
    ):
        _fail("attempt-acceptance", "attempt registry does not extend binding genesis")
    genesis = rows[0]
    configs = {
        (
            slot["trial_id"], slot["arm"], slot["holdout"],
            slot["campaign_id"], slot["replicate_index"],
        )
        for slot in genesis["slots"]
        if slot["attempt_index"] == 0
    }
    expected_configs = {
        (trial.trial_id, trial.arm, trial.holdout, trial.campaign_id, 0)
        for trial in manifest.trials
    }
    if configs != expected_configs:
        _fail("attempt-trial-set", "genesis initial slot set differs from manifest trials")
    terminals = {
        row["slot_id"]: row for row in rows if row.get("event") == "terminal"
    }
    slots_by_id = {
        slot["slot_id"]: slot for slot in genesis["slots"]
    }
    seen_report_slots: set[str] = set()
    for report_path in report_paths:
        report_bytes = _read_regular_bytes(
            Path(report_path), gate="attempt-acceptance", label="runtime report",
        )
        report = _decode_json(report_bytes, label="runtime report")
        if not isinstance(report, Mapping):
            _fail("attempt-runtime-cell", "runtime report is not an object")
        slot_id = report.get("slot_id")
        if not isinstance(slot_id, str):
            _fail("attempt-runtime-cell", "runtime report is missing slot_id")
        terminal = terminals.get(slot_id)
        if terminal is None:
            _fail("attempt-runtime-cell", "runtime report has no terminal slot")
        slot = slots_by_id.get(slot_id)
        if slot is None or report.get("trial_id") != slot["trial_id"]:
            _fail("attempt-trial-set", "runtime report slot differs from its trial")
        if slot_id in seen_report_slots:
            _fail("attempt-runtime-cell", "runtime reports reuse one slot")
        seen_report_slots.add(slot_id)
        if report.get("prereg_content_commit") != effective_binding.prereg_content_commit:
            _fail("attempt-runtime-cell", "runtime report P differs from binding")
        if report.get("prereg_effective_commit") != effective_commit:
            _fail("attempt-runtime-cell", "runtime report C differs from registry")
        expected_status = {
            "complete": "observed",
            "partial": "terminal-failure",
            "indeterminate": "not-consumed",
        }.get(report.get("status"))
        if expected_status is not None and terminal["terminal_status"] != expected_status:
            _fail("attempt-terminal", "runtime report status differs from attempt terminal")
        if terminal["report_sha256"] != hashlib.sha256(report_bytes).hexdigest():
            _fail("attempt-artifact", "terminal report hash differs from runtime report")
        report_raw_output = report.get("raw_output_sha256")
        _attempt_digest(report_raw_output, label="runtime report.raw_output_sha256")
        if report_raw_output != terminal["raw_output_sha256"]:
            _fail("attempt-artifact", "terminal raw output hash differs from runtime report")
        if terminal["terminal_status"] == "observed":
            observation_digest = _attempt_digest(
                report.get("observation_sha256"),
                label="runtime report.observation_sha256",
            )
            if observation_digest != terminal["observation_sha256"]:
                _fail("attempt-artifact", "terminal observation hash differs from runtime report")
            if report.get("primary_value") != terminal["primary_value"]:
                _fail("attempt-artifact", "terminal primary value differs from runtime report")
        elif (
            report.get("observation_sha256") is not None
            or report.get("primary_value") is not None
        ):
            _fail(
                "attempt-artifact",
                "non-observed terminal report carries observed values",
            )
    return rows


def assert_attempt_registry_acceptance(
    *,
    repository_root: Path,
    manifest_path: Path,
    manifest: TrialManifest,
    effective_binding: PreregEffectiveBinding,
    effective_commit: str,
    report_paths: Sequence[Path] = (),
    registry_path: Path = DEFAULT_ATTEMPT_REGISTRY_PATH,
) -> tuple[dict[str, Any], ...]:
    """Apply the compatibility replay policy at attempt acceptance."""
    return _assert_attempt_registry_acceptance(
        profile=_S8C_ATTEMPT_PROFILE,
        repository_root=repository_root,
        manifest_path=manifest_path,
        manifest=manifest,
        effective_binding=effective_binding,
        effective_commit=effective_commit,
        report_paths=report_paths,
        registry_path=registry_path,
    )


def assert_formal_attempt_registry_acceptance(
    *,
    repository_root: Path,
    manifest_path: Path,
    manifest: TrialManifest,
    effective_binding: PreregEffectiveBinding,
    effective_commit: str,
    report_paths: Sequence[Path] = (),
    registry_path: Path = DEFAULT_ATTEMPT_REGISTRY_PATH,
) -> tuple[dict[str, Any], ...]:
    """Require strict reason replay before issuing new formal acceptance."""
    return _assert_attempt_registry_acceptance(
        profile=_S8C_FORMAL_ATTEMPT_PROFILE,
        repository_root=repository_root,
        manifest_path=manifest_path,
        manifest=manifest,
        effective_binding=effective_binding,
        effective_commit=effective_commit,
        report_paths=report_paths,
        registry_path=registry_path,
    )


def _derive_launch_binding(
    *,
    manifest_path: Path,
    trial_id: str,
    workloads: Sequence[str],
    repository_root: Path,
    registry_path: Path,
    measurement_head: str,
) -> TrialBinding:
    """Derive one binding at an already pinned measurement commit."""
    root = repository_root
    manifest = load_trial_manifest(Path(manifest_path))
    _require_committed_file(
        repository_root=root,
        commit_id=measurement_head,
        path=Path(manifest_path),
        label="manifest",
        expected_bytes=manifest.raw_bytes,
    )
    registrations, _registry_bytes, _relative = _load_committed_registry(
        repository_root=root,
        registry_path=Path(registry_path),
        commit_id=measurement_head,
    )
    registration = _find_registration_for_manifest(
        registrations,
        manifest,
        allow_distinct_content_commit=True,
    )
    effective_binding = validate_preregistration_binding(
        root,
        manifest_path=Path(manifest_path),
        effective_commit=registration.prereg_effective_commit,
        measurement_commit=measurement_head,
    )
    if effective_binding.prereg_content_commit != registration.prereg_content_commit:
        _fail("registration-binding", "registry P differs from effective binding")
    selected = [trial for trial in manifest.trials if trial.trial_id == trial_id]
    if len(selected) != 1:
        _fail("trial-membership", "trial_id is not in the selected manifest")
    trial = selected[0]
    binding = HOLDOUT_BINDINGS[trial.holdout]
    if list(workloads) != [binding["workload"]]:
        _fail("workload-binding", "workloads do not match the trial holdout singleton")
    return TrialBinding(
        manifest_sha256=manifest.sha256,
        prereg_commit=manifest.prereg_commit,
        prereg_content_commit=registration.prereg_content_commit,
        prereg_effective_commit=registration.prereg_effective_commit,
        measurement_head=measurement_head,
        trial_id=trial.trial_id,
        arm=trial.arm,
        holdout=trial.holdout,
        campaign_id=trial.campaign_id,
        workload=binding["workload"],
        ycsb_rratio=binding["ycsb_rratio"],
        _seal=_TRIAL_BINDING_SEAL,
    )


def load_launch_binding(
    *,
    manifest_path: Path,
    trial_id: str,
    workloads: Sequence[str],
    repository_root: Path,
    registry_path: Path,
) -> TrialBinding:
    """Bind one declared trial to the operation's committed HEAD snapshot."""
    root = _repository_root(repository_root)
    measurement_head = resolve_measurement_commit(root)
    return _derive_launch_binding(
        manifest_path=manifest_path,
        trial_id=trial_id,
        workloads=workloads,
        repository_root=root,
        registry_path=registry_path,
        measurement_head=measurement_head,
    )


def assert_issued_trial_binding(binding: TrialBinding) -> None:
    """Reject caller-constructed values at the CLI-to-runner handoff."""
    if (
        not isinstance(binding, TrialBinding)
        or binding._seal is not _TRIAL_BINDING_SEAL
    ):
        _fail("launch-binding", "binding was not issued by the registry gate")
    for field in (
        "prereg_commit", "prereg_content_commit", "prereg_effective_commit",
        "measurement_head",
    ):
        _assert_full_commit_id(getattr(binding, field), label=f"binding.{field}")


def bind_trial_arm(
    binding: TrialBinding,
    *,
    repository_root: Path,
) -> TrialArmExecutionBinding:
    """Resolve and seal the execution input selected by an issued trial arm."""
    assert_issued_trial_binding(binding)
    expected = HOLDOUT_BINDINGS.get(binding.holdout)
    if (
        expected is None
        or expected.get("workload") != binding.workload
        or expected.get("ycsb_rratio") != binding.ycsb_rratio
    ):
        _fail("arm-input-resolution", "trial holdout projection is inconsistent")
    try:
        resolved = s8c_arm_inputs.resolve_arm_input(
            arm=binding.arm,
            holdout=binding.holdout,
            repository_root=Path(repository_root),
            commit=binding.measurement_head,
        )
    except s8c_arm_inputs.ArmInputError as exc:
        _fail("arm-input-resolution", str(exc))
    if resolved.arm != binding.arm or resolved.holdout != binding.holdout:
        _fail("arm-input-resolution", "resolver returned a different arm or holdout")
    if binding.arm == "on" and resolved.selected_holdout != binding.workload:
        _fail("arm-input-resolution", "on arm differs from the registered workload")
    return TrialArmExecutionBinding(
        binding=binding,
        resolved_input=resolved,
        canonical_input_bytes=resolved.canonical_input_bytes,
        input_schema_version=resolved.input_schema_version,
        content_digest_sha256=resolved.content_digest_sha256,
        arm_binding_digest_sha256=resolved.arm_binding_digest_sha256,
        _seal=_TRIAL_ARM_EXECUTION_SEAL,
    )


def assert_issued_trial_arm_execution(
    arm_execution: TrialArmExecutionBinding,
) -> None:
    """Reject caller construction and mutation of an arm execution capability."""
    if (
        type(arm_execution) is not TrialArmExecutionBinding
        or arm_execution._seal is not _TRIAL_ARM_EXECUTION_SEAL
    ):
        _fail("arm-input-resolution", "arm execution was not issued by the registry")
    assert_issued_trial_binding(arm_execution.binding)
    try:
        resolved = s8c_arm_inputs.assert_issued_resolved_arm_input(
            arm_execution.resolved_input
        )
    except s8c_arm_inputs.ArmInputError as exc:
        _fail("arm-input-resolution", str(exc))
    expected = (
        resolved.canonical_input_bytes,
        resolved.input_schema_version,
        resolved.content_digest_sha256,
        resolved.arm_binding_digest_sha256,
    )
    supplied = (
        arm_execution.canonical_input_bytes,
        arm_execution.input_schema_version,
        arm_execution.content_digest_sha256,
        arm_execution.arm_binding_digest_sha256,
    )
    if supplied != expected:
        _fail("arm-input-resolution", "sealed arm execution fields changed")


def assert_rederived_trial_arm_execution(
    arm_execution: TrialArmExecutionBinding,
    *,
    repository_root: Path,
) -> None:
    """Re-resolve historical bytes and require an exact capability projection."""
    assert_issued_trial_arm_execution(arm_execution)
    fresh = bind_trial_arm(
        arm_execution.binding,
        repository_root=repository_root,
    )
    if fresh.binding is not arm_execution.binding:
        _fail("arm-input-resolution", "fresh binding object identity changed")
    for field in dataclasses.fields(TrialArmExecutionBinding):
        if field.name in {"binding", "_seal"}:
            continue
        if getattr(fresh, field.name) != getattr(arm_execution, field.name):
            _fail("arm-input-resolution", f"arm execution changed: {field.name}")


def arm_execution_record(
    arm_execution: TrialArmExecutionBinding,
) -> dict[str, str]:
    """Project only input schema and the two independent digest layers."""
    assert_issued_trial_arm_execution(arm_execution)
    return {
        "input_schema_version": arm_execution.input_schema_version,
        "content_digest_sha256": arm_execution.content_digest_sha256,
        "arm_binding_digest_sha256": arm_execution.arm_binding_digest_sha256,
    }


def assert_rederived_launch_binding(
    binding: TrialBinding,
    *,
    manifest_path: Path,
    trial_id: str,
    workloads: Sequence[str],
    repository_root: Path,
    registry_path: Path,
) -> None:
    """Require every supplied field to equal a derivation at its pinned commit."""
    assert_issued_trial_binding(binding)
    root = _repository_root(repository_root)
    derived = _derive_launch_binding(
        manifest_path=manifest_path,
        trial_id=trial_id,
        workloads=workloads,
        repository_root=root,
        registry_path=registry_path,
        measurement_head=binding.measurement_head,
    )
    for field in dataclasses.fields(TrialBinding):
        supplied = getattr(binding, field.name)
        expected = getattr(derived, field.name)
        matches = (
            supplied is expected
            if field.name == "_seal"
            else supplied == expected
        )
        if not matches:
            _fail(
                "launch-binding",
                f"supplied binding differs from pinned derivation: {field.name}",
            )


def _validate_launch_inputs(
    *,
    trial_id: str,
    workloads: Sequence[str],
) -> tuple[str, ...]:
    if not isinstance(trial_id, str) or _TRIAL_ID_RE.fullmatch(trial_id) is None:
        _fail("field", "launch trial_id is not lexically valid")
    selected = tuple(workloads)
    if not selected:
        _fail("workloads", "launch workloads must be non-empty")
    if any(type(workload) is not str or not workload for workload in selected):
        _fail("workloads", "launch workload names must be non-empty plain strings")
    if len(selected) != len(set(selected)):
        _fail("workloads", "launch workloads contain duplicates")
    return selected


def _validate_a1_projection_fields(
    *,
    study_id: str,
    policy_sha256: str,
    preregistration_sha256: str,
    source_commit: str,
    workloads: Sequence[str],
    campaign_ids: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if type(study_id) is not str or not study_id:
        _fail("a1-noncertifying", "study_id is invalid")
    for label, digest in (
        ("policy_sha256", policy_sha256),
        ("preregistration_sha256", preregistration_sha256),
    ):
        if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
            _fail("a1-noncertifying", f"{label} is invalid")
    if type(source_commit) is not str or _COMMIT_RE.fullmatch(source_commit) is None:
        _fail("a1-noncertifying", "source_commit is invalid")
    selected_workloads = tuple(workloads)
    selected_campaign_ids = tuple(campaign_ids)
    if selected_workloads != A1_NON_CERTIFYING_WORKLOADS:
        _fail("a1-noncertifying", "workloads differ from the A-1 exact order")
    if (
        len(selected_campaign_ids) != len(A1_NON_CERTIFYING_WORKLOADS)
        or any(type(value) is not str or not value for value in selected_campaign_ids)
        or len(set(selected_campaign_ids)) != len(selected_campaign_ids)
    ):
        _fail("a1-noncertifying", "campaign_ids are not an exact unique triple")
    return selected_workloads, selected_campaign_ids


def issue_a1_registered_noncertifying_projection(
    *,
    study_id: str,
    policy_sha256: str,
    preregistration_sha256: str,
    source_commit: str,
    workloads: Sequence[str],
    campaign_ids: Sequence[str],
) -> A1RegisteredNonCertifyingProjection:
    """A-1 exact producer inputsから sealed non-certifying projectionを発行する。"""
    selected_workloads, selected_campaign_ids = _validate_a1_projection_fields(
        study_id=study_id,
        policy_sha256=policy_sha256,
        preregistration_sha256=preregistration_sha256,
        source_commit=source_commit,
        workloads=workloads,
        campaign_ids=campaign_ids,
    )
    return A1RegisteredNonCertifyingProjection(
        mode=REGISTERED_FORMAL_NON_CERTIFYING_MODE,
        certifying=False,
        study_id=study_id,
        policy_sha256=policy_sha256,
        preregistration_sha256=preregistration_sha256,
        source_commit=source_commit,
        workloads=selected_workloads,
        campaign_ids=selected_campaign_ids,
        _seal=_A1_NON_CERTIFYING_PROJECTION_SEAL,
    )


def assert_issued_a1_registered_noncertifying_projection(
    projection: A1RegisteredNonCertifyingProjection,
) -> None:
    """A-1 registry gate が発行した exact projection だけを受理する。"""
    if (
        type(projection) is not A1RegisteredNonCertifyingProjection
        or projection._seal is not _A1_NON_CERTIFYING_PROJECTION_SEAL
        or projection.mode != REGISTERED_FORMAL_NON_CERTIFYING_MODE
        or projection.certifying is not False
    ):
        _fail("a1-noncertifying", "projection was not issued by the A-1 gate")
    _validate_a1_projection_fields(
        study_id=projection.study_id,
        policy_sha256=projection.policy_sha256,
        preregistration_sha256=projection.preregistration_sha256,
        source_commit=projection.source_commit,
        workloads=projection.workloads,
        campaign_ids=projection.campaign_ids,
    )


def a1_registered_noncertifying_record(
    projection: A1RegisteredNonCertifyingProjection,
) -> dict[str, Any]:
    """lock/sidecar が共有する sealed A-1 projection record を返す。"""
    assert_issued_a1_registered_noncertifying_projection(projection)
    return {
        "mode": projection.mode,
        "certifying": projection.certifying,
        "study_id": projection.study_id,
        "policy_sha256": projection.policy_sha256,
        "preregistration_sha256": projection.preregistration_sha256,
        "source_commit": projection.source_commit,
        "campaign_ids": list(projection.campaign_ids),
    }


def admit_unregistered_exploratory(
    *,
    trial_id: str,
    workloads: Sequence[str],
    allow_unregistered_exploratory: bool,
    repository_root: Path,
    registry_path: Path,
) -> TrialLaunchAdmission:
    """Admit an explicitly opted-in, non-holdout, non-certifying launch."""
    selected = _validate_launch_inputs(trial_id=trial_id, workloads=workloads)
    root = _repository_root(repository_root)
    if allow_unregistered_exploratory is not True:
        _fail(
            "u4-exploratory-opt-in",
            "unregistered exploratory launch requires explicit opt-in",
        )
    holdouts = sorted(set(selected) & HOLDOUT_WORKLOADS)
    if holdouts:
        _fail(
            "u4-holdout-workload",
            f"holdout workloads cannot use exploratory admission: {holdouts}",
        )
    registry_path = Path(registry_path)
    if not registry_path.is_absolute():
        registry_path = root / registry_path
    working_present = registry_path.exists() or registry_path.is_symlink()
    measurement_head = resolve_measurement_commit(root)
    if working_present:
        registrations, _bytes, _relative = _load_committed_registry(
            repository_root=root,
            registry_path=registry_path,
            commit_id=measurement_head,
        )
    else:
        _candidate, _relative_path, relative = _registry_relative_target(
            registry_path, root,
        )
        committed = _blob_at_commit(
            root, commit_id=measurement_head, relative_path=relative,
        )
        if committed is None:
            registrations = ()
        else:
            registrations = _load_registry_bytes(
                committed, label="committed registry",
            )
    registered = {
        trial.trial_id for registration in registrations for trial in registration.trials
    }
    if trial_id in registered:
        _fail(
            "exploratory-registry",
            "registered trial_id cannot run without its manifest",
        )
    return TrialLaunchAdmission(
        mode="explicit-unregistered-exploratory",
        certifying=False,
        reason_code="explicit-unregistered-exploratory",
        trial_id=trial_id,
        workloads=selected,
        binding=None,
        activation_report_digest_sha256=None,
        _seal=_TRIAL_LAUNCH_ADMISSION_SEAL,
    )


def admit_registered_launch(
    *,
    effective_preregistration: s8c_preregistration.EffectivePreregistration,
    manifest_path: Path,
    trial_id: str,
    workloads: Sequence[str],
    repository_root: Path,
    registry_path: Path,
) -> TrialLaunchAdmission:
    """Admit one registered launch after exact activation recomputation."""
    selected = _validate_launch_inputs(trial_id=trial_id, workloads=workloads)
    root = _repository_root(repository_root)
    manifest = load_trial_manifest(Path(manifest_path))
    if (
        not isinstance(
            effective_preregistration,
            s8c_preregistration.EffectivePreregistration,
        )
        or effective_preregistration.commit != manifest.prereg_commit
    ):
        _fail(
            "effective-preregistration",
            "manifest prereg_commit requires an exact EffectivePreregistration capability",
        )
    try:
        s8c_preregistration.require_effective_preregistration(
            effective_preregistration,
            repo_root=root,
            commit=manifest.prereg_commit,
        )
    except s8c_preregistration.PreregistrationError as exc:
        _fail("effective-preregistration", f"{exc.reason}: {exc}")
    binding = load_launch_binding(
        manifest_path=Path(manifest_path),
        trial_id=trial_id,
        workloads=selected,
        repository_root=root,
        registry_path=Path(registry_path),
    )
    return TrialLaunchAdmission(
        mode="registered-effective",
        certifying=False,
        reason_code="registered-effective-non-certifying",
        trial_id=trial_id,
        workloads=selected,
        binding=binding,
        activation_report_digest_sha256=(
            effective_preregistration.report_digest_sha256
        ),
        _seal=_TRIAL_LAUNCH_ADMISSION_SEAL,
    )


def admit_registered_formal_noncertifying(
    *,
    allow_formal_noncertifying: bool,
    manifest_path: Path,
    trial_id: str,
    workloads: Sequence[str],
    repository_root: Path,
    registry_path: Path,
) -> TrialLaunchAdmission:
    """Admit an explicitly opted-in registered formal non-certifying launch."""
    selected = _validate_launch_inputs(trial_id=trial_id, workloads=workloads)
    root = _repository_root(repository_root)
    if allow_formal_noncertifying is not True:
        _fail(
            "formal-noncertifying-opt-in",
            "formal non-certifying launch requires explicit opt-in",
        )

    manifest = load_trial_manifest(Path(manifest_path))
    try:
        s8c_preregistration.validate_condition_freeze_at(
            root,
            manifest.prereg_commit,
        )
    except s8c_preregistration.PreregistrationError as exc:
        _fail(
            "formal-noncertifying-condition-freeze",
            f"{exc.reason}: {exc}",
        )

    binding = load_launch_binding(
        manifest_path=Path(manifest_path),
        trial_id=trial_id,
        workloads=selected,
        repository_root=root,
        registry_path=Path(registry_path),
    )
    return TrialLaunchAdmission(
        mode=REGISTERED_FORMAL_NON_CERTIFYING_MODE,
        certifying=False,
        reason_code=REGISTERED_FORMAL_NON_CERTIFYING_MODE,
        trial_id=trial_id,
        workloads=selected,
        binding=binding,
        activation_report_digest_sha256=None,
        _seal=_TRIAL_LAUNCH_ADMISSION_SEAL,
    )


def assert_issued_trial_launch_admission(
    admission: TrialLaunchAdmission,
) -> None:
    """Reject caller-constructed launch admission values."""
    if (
        not isinstance(admission, TrialLaunchAdmission)
        or admission._seal is not _TRIAL_LAUNCH_ADMISSION_SEAL
    ):
        _fail("launch-admission", "admission was not issued by the registry gate")
    if admission.mode not in {
        "registered-effective",
        REGISTERED_FORMAL_NON_CERTIFYING_MODE,
        "explicit-unregistered-exploratory",
    }:
        _fail("launch-admission", "admission mode is outside the closed set")
    if admission.certifying is not False:
        _fail("launch-admission", "this wiring wave cannot issue certifying launches")
    _validate_launch_inputs(
        trial_id=admission.trial_id,
        workloads=admission.workloads,
    )
    if admission.mode == "registered-effective":
        if admission.binding is None:
            _fail("launch-admission", "registered admission is missing its binding")
        assert_issued_trial_binding(admission.binding)
        if (
            _COMMIT_RE.fullmatch(admission.binding.prereg_content_commit) is None
            or _COMMIT_RE.fullmatch(admission.binding.prereg_effective_commit) is None
        ):
            _fail("launch-admission", "registered admission has invalid P/C binding")
        if admission.reason_code != "registered-effective-non-certifying":
            _fail("launch-admission", "registered admission reason_code is inconsistent")
        if admission.binding.trial_id != admission.trial_id:
            _fail("launch-admission", "registered admission trial_id is inconsistent")
        if admission.workloads != (admission.binding.workload,):
            _fail("launch-admission", "registered admission workload is inconsistent")
        if (
            admission.activation_report_digest_sha256 is None
            or _SHA256_RE.fullmatch(admission.activation_report_digest_sha256) is None
        ):
            _fail("launch-admission", "registered admission has no activation digest")
    elif admission.mode == REGISTERED_FORMAL_NON_CERTIFYING_MODE:
        if admission.binding is None:
            _fail(
                "launch-admission",
                "formal non-certifying admission is missing its binding",
            )
        assert_issued_trial_binding(admission.binding)
        if (
            _COMMIT_RE.fullmatch(admission.binding.prereg_content_commit) is None
            or _COMMIT_RE.fullmatch(admission.binding.prereg_effective_commit) is None
        ):
            _fail(
                "launch-admission",
                "formal non-certifying admission has invalid P/C binding",
            )
        if admission.reason_code != REGISTERED_FORMAL_NON_CERTIFYING_MODE:
            _fail(
                "launch-admission",
                "formal non-certifying admission reason_code is inconsistent",
            )
        if admission.binding.trial_id != admission.trial_id:
            _fail(
                "launch-admission",
                "formal non-certifying admission trial_id is inconsistent",
            )
        if admission.workloads != (admission.binding.workload,):
            _fail(
                "launch-admission",
                "formal non-certifying admission workload is inconsistent",
            )
        if admission.activation_report_digest_sha256 is not None:
            _fail(
                "launch-admission",
                "formal non-certifying admission has an activation digest",
            )
    else:
        if (
            admission.reason_code != "explicit-unregistered-exploratory"
            or admission.binding is not None
            or admission.activation_report_digest_sha256 is not None
            or set(admission.workloads) & HOLDOUT_WORKLOADS
        ):
            _fail("launch-admission", "exploratory admission fields are inconsistent")


def launch_admission_record(
    admission: TrialLaunchAdmission,
    *,
    origin_binding: OriginBindingCapability | None = None,
) -> dict[str, Any]:
    """Return the shared exact record, omitting unissued origin projection."""
    assert_issued_trial_launch_admission(admission)
    binding = admission.binding
    binding_record = None
    if binding is not None:
        binding_record = {
            field: getattr(binding, field)
            for field in (
                "manifest_sha256", "prereg_commit", "prereg_content_commit",
                "prereg_effective_commit", "measurement_head",
                "trial_id", "arm", "holdout", "campaign_id", "workload",
                "ycsb_rratio",
            )
        }
    record = {
        "mode": admission.mode,
        "certifying": admission.certifying,
        "reason_code": admission.reason_code,
        "trial_id": admission.trial_id,
        "workloads": list(admission.workloads),
        "binding": binding_record,
        "activation_report_digest_sha256": (
            admission.activation_report_digest_sha256
        ),
    }
    if binding is not None:
        record["prereg_content_commit"] = binding.prereg_content_commit
        record["prereg_effective_commit"] = binding.prereg_effective_commit
    if origin_binding is not None:
        from . import reflux_origin_binding

        origin_record = (
            reflux_origin_binding.origin_binding_capability_record(origin_binding)
        )
        if (
            binding is None
            or admission.mode not in {
                "registered-effective",
                REGISTERED_FORMAL_NON_CERTIFYING_MODE,
            }
            or origin_record["campaign_id"] != binding.campaign_id
            or origin_record["trial_workload"] != binding.workload
            or origin_record["measurement_head"] != binding.measurement_head
        ):
            _fail(
                "launch-admission",
                "origin capability differs from the registered launch binding",
            )
        record["origin_binding"] = origin_record
    return record


def assert_rederived_launch_admission(
    admission: TrialLaunchAdmission,
    *,
    effective_preregistration,
    manifest_path: Path | None,
    trial_id: str,
    workloads: Sequence[str],
    allow_unregistered_exploratory: bool,
    allow_formal_noncertifying: bool = False,
    repository_root: Path,
    registry_path: Path,
    origin_binding: OriginBindingCapability | None = None,
) -> None:
    """Require a supplied admission to equal a fresh public-gate derivation."""
    assert_issued_trial_launch_admission(admission)
    if manifest_path is None:
        if effective_preregistration is not None:
            _fail("launch-admission", "exploratory launch received formal capability")
        derived = admit_unregistered_exploratory(
            trial_id=trial_id,
            workloads=workloads,
            allow_unregistered_exploratory=allow_unregistered_exploratory,
            repository_root=repository_root,
            registry_path=registry_path,
        )
    elif allow_formal_noncertifying:
        derived = admit_registered_formal_noncertifying(
            allow_formal_noncertifying=allow_formal_noncertifying,
            manifest_path=manifest_path,
            trial_id=trial_id,
            workloads=workloads,
            repository_root=repository_root,
            registry_path=registry_path,
        )
    else:
        derived = admit_registered_launch(
            effective_preregistration=effective_preregistration,
            manifest_path=manifest_path,
            trial_id=trial_id,
            workloads=workloads,
            repository_root=repository_root,
            registry_path=registry_path,
        )
    if launch_admission_record(
        admission, origin_binding=origin_binding,
    ) != launch_admission_record(
        derived, origin_binding=origin_binding,
    ):
        _fail("launch-admission", "supplied admission differs from fresh derivation")


def _load_lifecycle_rows(data: bytes) -> tuple[dict[str, Any], ...]:
    if data and not data.endswith(b"\n"):
        _fail("lifecycle-framing", "lifecycle ledger is not newline terminated")
    rows: list[dict[str, Any]] = []
    starts: set[str] = set()
    terminals: set[str] = set()
    start_by_trial: dict[str, Mapping[str, Any]] = {}
    for lineno, line in enumerate(data.splitlines(), 1):
        if not line:
            _fail("lifecycle-framing", f"lifecycle ledger has a blank line at {lineno}")
        value = _decode_json(line, label=f"lifecycle line {lineno}")
        if not isinstance(value, Mapping):
            _fail("lifecycle-schema", f"lifecycle line {lineno} is not an object")
        if _canonical_json_bytes(value) != line:
            _fail("lifecycle-canonical", f"lifecycle line {lineno} is not canonical JSON")
        if value.get("schema_version") != LIFECYCLE_SCHEMA_VERSION:
            _fail("lifecycle-schema", f"lifecycle line {lineno} has bad schema_version")
        event = value.get("event")
        if event == "start":
            if frozenset(value) not in _LIFECYCLE_START_KEYS:
                _fail(
                    "lifecycle-schema",
                    f"lifecycle line {lineno} start exact keys differ",
                )
        elif event == "terminal":
            if frozenset(value) not in _LIFECYCLE_TERMINAL_KEYS:
                _fail(
                    "lifecycle-schema",
                    f"lifecycle line {lineno} terminal exact keys differ",
                )
        else:
            _fail("lifecycle-schema", f"lifecycle line {lineno} has unknown event")
        trial_id = value.get("trial_id")
        if not isinstance(trial_id, str) or _TRIAL_ID_RE.fullmatch(trial_id) is None:
            _fail("lifecycle-schema", f"lifecycle line {lineno} has invalid trial_id")
        if event == "start":
            if trial_id in starts:
                _fail("lifecycle-duplicate-start", f"trial_id already started: {trial_id}")
            starts.add(trial_id)
            if value["mode"] not in {
                "registered-effective",
                REGISTERED_FORMAL_NON_CERTIFYING_MODE,
            }:
                _fail(
                    "lifecycle-schema",
                    "only registered launches (registered-effective or "
                    "registered-formal-non-certifying) are recorded",
                )
            if not isinstance(value["run_root"], str) or not value["run_root"]:
                _fail("lifecycle-schema", "start run_root must be a non-empty string")
            fields = (
                ("manifest_sha256", _SHA256_RE),
                ("prereg_commit", _COMMIT_RE),
                ("prereg_content_commit", _COMMIT_RE),
                ("prereg_effective_commit", _COMMIT_RE),
                ("measurement_head", _COMMIT_RE),
            )
            if value["mode"] == "registered-effective":
                fields += (
                    ("activation_report_digest_sha256", _SHA256_RE),
                )
            fields += (
                ("launch_admission_sha256", _SHA256_RE),
                ("schedule_row_sha256", _SHA256_RE),
            )
            for field, pattern in fields:
                raw = value[field]
                if not isinstance(raw, str) or pattern.fullmatch(raw) is None:
                    _fail("lifecycle-schema", f"start {field} is invalid")
            if "origin_run_plan_sha256" in value:
                digest = value["origin_run_plan_sha256"]
                if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
                    _fail(
                        "lifecycle-schema",
                        "start origin_run_plan_sha256 is invalid",
                    )
            if (
                value["mode"] == REGISTERED_FORMAL_NON_CERTIFYING_MODE
                and value["activation_report_digest_sha256"] is not None
            ):
                _fail(
                    "lifecycle-schema",
                    "formal non-certifying start has an activation digest",
                )
            _attempt_process_identity(
                value["process_identity"], label=f"lifecycle line {lineno}.process_identity",
            )
            if not value["slot_id"]:
                _fail("lifecycle-schema", "start slot_id is empty")
            start_by_trial[trial_id] = dict(value)
        else:
            if trial_id not in starts:
                _fail("lifecycle-terminal", f"terminal precedes start: {trial_id}")
            if trial_id in terminals:
                _fail("lifecycle-terminal", f"trial_id already has terminal row: {trial_id}")
            terminals.add(trial_id)
            if value["terminal_status"] not in {"complete", "partial", "indeterminate"}:
                _fail("lifecycle-schema", "terminal_status is outside the closed set")
            start = start_by_trial[trial_id]
            start_has_origin = "origin_run_plan_sha256" in start
            terminal_has_origin = "origin_terminal_projection" in value
            origin_failure_without_projection = (
                start_has_origin
                and not terminal_has_origin
                and value["terminal_status"] in {"partial", "indeterminate"}
            )
            if (
                start_has_origin != terminal_has_origin
                and not origin_failure_without_projection
            ):
                _fail(
                    "lifecycle-origin",
                    "start run-plan digest and terminal origin projection "
                    "presence differ",
                )
            if origin_failure_without_projection:
                failure_reason = value.get("failure_reason")
                if type(failure_reason) is not str or not failure_reason:
                    _fail(
                        "lifecycle-origin",
                        "origin failure without terminal projection requires "
                        "a non-empty failure_reason",
                    )
            elif "failure_reason" in value:
                _fail(
                    "lifecycle-origin",
                    "failure_reason is only valid for an origin failure "
                    "without terminal projection",
                )
            for field, pattern in (
                ("prereg_commit", _COMMIT_RE),
                ("prereg_content_commit", _COMMIT_RE),
                ("prereg_effective_commit", _COMMIT_RE),
                ("slot_id", _TRIAL_ID_RE),
                ("classification_receipt_sha256", _SHA256_RE),
                ("raw_output_sha256", _SHA256_RE),
            ):
                raw = value[field]
                if not isinstance(raw, str) or pattern.fullmatch(raw) is None:
                    _fail("lifecycle-schema", f"terminal {field} is invalid")
            if (
                value["prereg_commit"] != value["prereg_content_commit"]
                or value["prereg_content_commit"] != start["prereg_content_commit"]
                or value["prereg_effective_commit"] != start["prereg_effective_commit"]
                or value["slot_id"] != start["slot_id"]
            ):
                _fail("lifecycle-binding", "terminal P/C/slot differs from its start")
            for field in ("report_sha256", "attempt_journal_sha256"):
                raw = value[field]
                if raw is not None and (
                    not isinstance(raw, str) or _SHA256_RE.fullmatch(raw) is None
                ):
                    _fail("lifecycle-schema", f"terminal {field} is invalid")
            if "origin_terminal_projection" in value:
                _validate_origin_terminal_projection(
                    value["origin_terminal_projection"],
                    gate="lifecycle-schema",
                )
        rows.append(dict(value))
    return tuple(rows)


def _lifecycle_history_tip(
    *,
    repository_root: Path,
    relative_path: str,
    current_head: str,
) -> bytes | None:
    """Validate committed append-only history within one Git repository.

    Independent clones and repositories remain outside this guarantee.  Every
    committed version in this repository must be a strict prefix extension;
    deletion followed by recreation and edit followed by revert are rejected.
    """
    result = _git(repository_root, (
        "log", "--format=%H", "--reverse", "--full-history", current_head,
        "--", relative_path,
    ))
    if result.returncode != 0:
        raise TrialRegistryError("[git-operational] lifecycle history walk failed")
    previous: bytes | None = None
    for raw_commit in result.stdout.splitlines():
        try:
            commit_id = raw_commit.decode("ascii")
        except UnicodeDecodeError as exc:
            raise TrialRegistryError(
                "[git-operational] lifecycle history returned non-ASCII"
            ) from exc
        if _COMMIT_RE.fullmatch(commit_id) is None:
            _fail("lifecycle-history", "history returned an invalid commit ID")
        blob = _blob_at_commit(
            repository_root, commit_id=commit_id, relative_path=relative_path,
        )
        if blob is None:
            _fail("lifecycle-history", "lifecycle path was deleted in committed history")
        _load_lifecycle_rows(blob)
        if previous is not None and (
            not blob.startswith(previous) or len(blob) <= len(previous)
        ):
            _fail(
                "lifecycle-history",
                "lifecycle history is not a strict prefix extension",
            )
        previous = blob
    return previous


def _locked_lifecycle_update(
    *,
    repository_root: Path,
    lifecycle_path: Path,
    update,
):
    root = _repository_root(repository_root)
    _candidate, relative_path, relative = _registry_relative_target(
        lifecycle_path, root,
    )
    history_tip = _lifecycle_history_tip(
        repository_root=root,
        relative_path=relative,
        current_head=resolve_measurement_commit(root),
    )
    parent_fd = _open_registry_parent(root, relative_path.parent, create=True)
    try:
        flags = os.O_RDWR | os.O_APPEND | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(relative_path.name, flags, 0o644, dir_fd=parent_fd)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                _fail("lifecycle-path", "lifecycle ledger is not a regular file")
            rebound = os.stat(
                relative_path.name, dir_fd=parent_fd, follow_symlinks=False,
            )
            if (rebound.st_dev, rebound.st_ino) != (info.st_dev, info.st_ino):
                _fail("lifecycle-path", "lifecycle path changed under lock")
            current = bytearray()
            offset = 0
            while offset < info.st_size:
                chunk = os.pread(fd, min(1024 * 1024, info.st_size - offset), offset)
                if not chunk:
                    _fail("lifecycle-read", "lifecycle read stopped before fstat size")
                current.extend(chunk)
                offset += len(chunk)
            rows = _load_lifecycle_rows(bytes(current))
            if history_tip is not None and not bytes(current).startswith(history_tip):
                _fail(
                    "lifecycle-history",
                    "working lifecycle ledger does not extend committed history",
                )
            payload, result = update(rows)
            if payload is not None:
                view = memoryview(payload)
                while view:
                    written = os.write(fd, view)
                    if written <= 0:
                        raise OSError("lifecycle append did not advance")
                    view = view[written:]
                os.fsync(fd)
                os.fsync(parent_fd)
            return result
        finally:
            os.close(fd)
    except TrialRegistryError:
        raise
    except OSError as exc:
        raise TrialRegistryError(f"[lifecycle-io] lifecycle update failed: {exc}") from exc
    finally:
        os.close(parent_fd)


def record_trial_start_once(
    *,
    admission: TrialLaunchAdmission,
    effective_preregistration: s8c_preregistration.EffectivePreregistration | None,
    manifest_path: Path,
    run_root: Path,
    repository_root: Path,
    attempt_slot: AttemptSlotCapability,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    lifecycle_path: Path = DEFAULT_LIFECYCLE_PATH,
    origin_binding: OriginBindingCapability | None = None,
    origin_run_plan_sha256: str | None = None,
) -> TrialLifecycleToken:
    """Atomically record one formal start in a single shared lifecycle ledger.

    Runtime start-once is limited to processes sharing this ledger.  Committed
    append-only history is checked within one Git repository; no guarantee is
    claimed across independent clones or repositories.
    """
    if (origin_binding is None) != (origin_run_plan_sha256 is None):
        _fail(
            "lifecycle-origin",
            "origin binding and run-plan digest presence differ",
        )
    if origin_run_plan_sha256 is not None and (
        type(origin_run_plan_sha256) is not str
        or _SHA256_RE.fullmatch(origin_run_plan_sha256) is None
    ):
        _fail("lifecycle-origin", "origin run-plan digest is invalid")
    assert_rederived_launch_admission(
        admission,
        effective_preregistration=effective_preregistration,
        manifest_path=Path(manifest_path),
        trial_id=admission.trial_id,
        workloads=admission.workloads,
        allow_unregistered_exploratory=False,
        allow_formal_noncertifying=(
            admission.mode == REGISTERED_FORMAL_NON_CERTIFYING_MODE
        ),
        repository_root=repository_root,
        registry_path=registry_path,
        origin_binding=origin_binding,
    )
    if (
        admission.mode not in (
            "registered-effective",
            REGISTERED_FORMAL_NON_CERTIFYING_MODE,
        )
        or admission.binding is None
    ):
        _fail(
            "lifecycle-start",
            "only registered launches (registered-effective or "
            "registered-formal-non-certifying) may start",
        )
    binding = admission.binding
    _assert_attempt_capability(attempt_slot)
    if (
        attempt_slot.repository_root != _repository_root(repository_root)
        or attempt_slot.trial_id != admission.trial_id
        or attempt_slot.prereg_content_commit != binding.prereg_content_commit
        or attempt_slot.prereg_effective_commit != binding.prereg_effective_commit
    ):
        _fail("lifecycle-start", "attempt slot differs from launch binding")
    admission_sha256 = hashlib.sha256(
        _canonical_json_bytes(
            launch_admission_record(admission, origin_binding=origin_binding)
        )
        ).hexdigest()
    attempt_rows = load_attempt_registry(
        attempt_slot.repository_root,
        registry_path=attempt_slot.registry_path,
        prereg_content_commit=binding.prereg_content_commit,
        prereg_effective_commit=binding.prereg_effective_commit,
        freeze_id=attempt_slot.freeze_id,
    )
    attempt_starts = [
        item for item in attempt_rows
        if item.get("event") == "start" and item.get("slot_id") == attempt_slot.slot_id
    ]
    if len(attempt_starts) != 1:
        _fail("lifecycle-start", "attempt slot must be reserved exactly once before lifecycle start")
    attempt_start = attempt_starts[0]
    if attempt_start["run_start_receipt_sha256"] != admission_sha256:
        _fail("lifecycle-start", "attempt run-start receipt differs from launch admission")
    row = {
        "schema_version": LIFECYCLE_SCHEMA_VERSION,
        "event": "start",
        "trial_id": admission.trial_id,
        "run_root": os.path.abspath(os.fspath(run_root)),
        "mode": admission.mode,
        "manifest_sha256": binding.manifest_sha256,
        "prereg_commit": binding.prereg_commit,
        "prereg_content_commit": binding.prereg_content_commit,
        "prereg_effective_commit": binding.prereg_effective_commit,
        "measurement_head": binding.measurement_head,
        "activation_report_digest_sha256": (
            admission.activation_report_digest_sha256
        ),
        "launch_admission_sha256": admission_sha256,
        "slot_id": attempt_slot.slot_id,
        "schedule_row_sha256": attempt_start["schedule_row_sha256"],
        "process_identity": dict(attempt_start["process_identity"]),
    }
    if origin_run_plan_sha256 is not None:
        row["origin_run_plan_sha256"] = origin_run_plan_sha256
    raw = _canonical_json_bytes(row)
    payload = raw + b"\n"
    root = _repository_root(repository_root)
    ledger, _relative = _canonical_lifecycle_target(
        lifecycle_path, root, create_parent=True,
    )

    with _TRIAL_LIFECYCLE_CAPABILITIES_LOCK:
        if any(
            state.repository_root == root
            and state.lifecycle_path == ledger
            and state.trial_id == admission.trial_id
            and state.started_once
            and state.restart_forbidden
            for state in _TRIAL_LIFECYCLE_CAPABILITIES.values()
        ):
            _fail(
                "lifecycle-restart-forbidden",
                f"trial_id is forbidden from restart: {admission.trial_id}",
            )

    def append_start(rows):
        if any(item["event"] == "start" and item["trial_id"] == admission.trial_id for item in rows):
            _fail(
                "lifecycle-start-once",
                f"trial_id already has a start row: {admission.trial_id}",
            )
        token = TrialLifecycleToken(
            repository_root=root,
            lifecycle_path=ledger,
            trial_id=admission.trial_id,
            run_root=row["run_root"],
            start_row_sha256=hashlib.sha256(raw).hexdigest(),
            launch_admission_sha256=admission_sha256,
            prereg_content_commit=binding.prereg_content_commit,
            prereg_effective_commit=binding.prereg_effective_commit,
            slot_id=attempt_slot.slot_id,
            origin_run_plan_sha256=origin_run_plan_sha256,
            _seal=_TRIAL_LIFECYCLE_TOKEN_SEAL,
        )
        state = _TrialLifecycleCapabilityState(
            token=token,
            repository_root=root,
            lifecycle_path=ledger,
            trial_id=admission.trial_id,
            run_root=row["run_root"],
            start_row_sha256=token.start_row_sha256,
            launch_admission_sha256=admission_sha256,
            prereg_content_commit=binding.prereg_content_commit,
            prereg_effective_commit=binding.prereg_effective_commit,
            slot_id=attempt_slot.slot_id,
            schedule_row_sha256=attempt_start["schedule_row_sha256"],
            process_identity=dict(attempt_start["process_identity"]),
            origin_binding=origin_binding,
            origin_run_plan_sha256=origin_run_plan_sha256,
            started_once=True,
        )
        return payload, (token, state)

    token, state = _locked_lifecycle_update(
        repository_root=root,
        lifecycle_path=ledger,
        update=append_start,
    )
    with _TRIAL_LIFECYCLE_CAPABILITIES_LOCK:
        if id(token) in _TRIAL_LIFECYCLE_CAPABILITIES:
            _fail("lifecycle-token", "issued token identity is not unique")
        _TRIAL_LIFECYCLE_CAPABILITIES[id(token)] = state
    return token


def reject_started_trial(
    *,
    trial_id: str,
    repository_root: Path,
    lifecycle_path: Path = DEFAULT_LIFECYCLE_PATH,
) -> None:
    """Reject a second launch before issuing a lifecycle capability.

    The check is deliberately read-only with respect to lifecycle rows.  The
    shared lifecycle lock still makes the observation atomic with the later
    start append, while the existing start-once append remains the final
    race-safe defense.
    """
    if type(trial_id) is not str or _TRIAL_ID_RE.fullmatch(trial_id) is None:
        _fail("lifecycle-start-once", "trial_id is not lexically valid")
    root = _repository_root(repository_root)
    ledger, _relative = _canonical_lifecycle_target(
        lifecycle_path, root, create_parent=True,
    )

    def inspect(rows):
        if any(
            item["event"] == "start" and item["trial_id"] == trial_id
            for item in rows
        ):
            _fail(
                "lifecycle-start-once",
                f"trial_id already has a start row: {trial_id}",
            )
        return None, None

    _locked_lifecycle_update(
        repository_root=root,
        lifecycle_path=ledger,
        update=inspect,
    )


def forbid_trial_restart(token: TrialLifecycleToken) -> None:
    """Consume the in-process restart capability for a started trial.

    The durable start and indeterminate terminal rows remain the cross-process
    refusal proof.  This capability flag makes the no-restart state explicit
    to the process that owns the issued token without adding lifecycle keys.
    """
    if (
        type(token) is not TrialLifecycleToken
        or token._seal is not _TRIAL_LIFECYCLE_TOKEN_SEAL
    ):
        _fail("lifecycle-token", "restart refusal requires an issued lifecycle token")
    with _TRIAL_LIFECYCLE_CAPABILITIES_LOCK:
        state = _TRIAL_LIFECYCLE_CAPABILITIES.get(id(token))
        if state is None or state.token is not token or not state.started_once:
            _fail(
                "lifecycle-token",
                "restart refusal requires the exact started capability",
            )
        state.restart_forbidden = True


def record_trial_terminal(
    token: TrialLifecycleToken,
    *,
    terminal_status: str,
    origin_terminal_projection: OriginTerminalProjection | None = None,
    failure_reason: str | None = None,
) -> None:
    """Consume one start token and append its closed terminal form."""
    if (
        type(token) is not TrialLifecycleToken
        or token._seal is not _TRIAL_LIFECYCLE_TOKEN_SEAL
    ):
        _fail("lifecycle-token", "token was not issued by record_trial_start_once")
    if terminal_status not in {"complete", "partial", "indeterminate"}:
        _fail("lifecycle-terminal", "terminal_status is outside the closed set")
    projection_record = None
    if origin_terminal_projection is not None:
        from . import reflux_formal_consumer

        projection_record = (
            reflux_formal_consumer.origin_terminal_projection_record(
                origin_terminal_projection
            )
        )
    with _TRIAL_LIFECYCLE_CAPABILITIES_LOCK:
        state = _TRIAL_LIFECYCLE_CAPABILITIES.get(id(token))
        if state is None or state.token is not token:
            _fail(
                "lifecycle-token",
                "terminal requires the exact object issued at lifecycle start",
            )
        if state.consumed:
            _fail("lifecycle-token", "lifecycle capability was already consumed")
        origin_failure_without_projection = (
            state.origin_binding is not None
            and projection_record is None
            and terminal_status in {"partial", "indeterminate"}
        )
        if (
            (state.origin_binding is None) != (projection_record is None)
            and not origin_failure_without_projection
        ):
            _fail(
                "lifecycle-origin",
                "origin binding and terminal projection presence differ",
            )
        if origin_failure_without_projection:
            if type(failure_reason) is not str or not failure_reason:
                _fail(
                    "lifecycle-origin",
                    "origin failure without terminal projection requires "
                    "a non-empty failure_reason",
                )
        elif failure_reason is not None:
            _fail(
                "lifecycle-origin",
                "failure_reason is only valid for an origin failure without "
                "terminal projection",
            )
        if state.origin_binding is not None and projection_record is not None:
            from . import reflux_origin_binding

            origin_record = reflux_origin_binding.origin_binding_capability_record(
                state.origin_binding
            )
            terminal_record = projection_record["origin_terminal_projection"]
            if any(
                terminal_record[field] != origin_record[field]
                for field in ("authority_blob_sha256", "origin_id", "cell_key")
            ):
                _fail(
                    "lifecycle-origin",
                    "terminal projection differs from the start origin binding",
                )
        state.consumed = True

    attempt_rows = load_attempt_registry(
        state.repository_root,
        registry_path=(
            state.repository_root / DEFAULT_ATTEMPT_REGISTRY_PATH
        ),
        prereg_content_commit=state.prereg_content_commit,
        prereg_effective_commit=state.prereg_effective_commit,
    )
    attempt_terminals = [
        item for item in attempt_rows
        if item.get("event") == "terminal" and item.get("slot_id") == state.slot_id
    ]
    if len(attempt_terminals) != 1:
        _fail("lifecycle-terminal", "attempt slot terminal row is absent or ambiguous")
    attempt_terminal = attempt_terminals[0]
    expected_attempt_status = {
        "complete": "observed",
        "partial": "terminal-failure",
        "indeterminate": "not-consumed",
    }[terminal_status]
    if attempt_terminal["terminal_status"] != expected_attempt_status:
        _fail("lifecycle-terminal", "lifecycle status differs from attempt status")
    if terminal_status == "indeterminate":
        report_sha256 = None
        attempt_journal_sha256 = None
    else:
        run_root = Path(state.run_root)
        report_bytes = _read_regular_bytes(
            run_root / "report.json",
            gate="lifecycle-terminal-artifact",
            label="terminal report",
        )
        journal_bytes = _read_regular_bytes(
            run_root / "attempts.jsonl",
            gate="lifecycle-terminal-artifact",
            label="attempt journal",
        )
        report_sha256 = hashlib.sha256(report_bytes).hexdigest()
        attempt_journal_sha256 = hashlib.sha256(journal_bytes).hexdigest()
    row = {
        "schema_version": LIFECYCLE_SCHEMA_VERSION,
        "event": "terminal",
        "trial_id": state.trial_id,
        "terminal_status": terminal_status,
        "report_sha256": report_sha256,
        "attempt_journal_sha256": attempt_journal_sha256,
        "prereg_commit": state.prereg_content_commit,
        "prereg_content_commit": state.prereg_content_commit,
        "prereg_effective_commit": state.prereg_effective_commit,
        "slot_id": state.slot_id,
        "classification_receipt_sha256": attempt_terminal[
            "classification_receipt_sha256"
        ],
        "raw_output_sha256": attempt_terminal["raw_output_sha256"],
    }
    if projection_record is not None:
        row.update(projection_record)
    elif origin_failure_without_projection:
        row["failure_reason"] = failure_reason
    payload = _canonical_json_bytes(row) + b"\n"

    def append_terminal(rows):
        starts = [
            item for item in rows
            if item["event"] == "start" and item["trial_id"] == state.trial_id
        ]
        if len(starts) != 1:
            _fail("lifecycle-token", "token start row is absent or ambiguous")
        start_raw = _canonical_json_bytes(starts[0])
        if (
            hashlib.sha256(start_raw).hexdigest() != state.start_row_sha256
            or starts[0]["run_root"] != state.run_root
            or starts[0]["launch_admission_sha256"]
            != state.launch_admission_sha256
        ):
            _fail("lifecycle-token", "token does not match its start row")
        if any(
            item["event"] == "terminal" and item["trial_id"] == state.trial_id
            for item in rows
        ):
            _fail("lifecycle-terminal-once", "trial already has a terminal row")
        return payload, None

    _locked_lifecycle_update(
        repository_root=state.repository_root,
        lifecycle_path=state.lifecycle_path,
        update=append_terminal,
    )


def assert_campaign_binding(
    binding: TrialBinding,
    *,
    arm_execution: TrialArmExecutionBinding,
    actual_campaign_id: str,
) -> None:
    """Compare producer identity only after validating issued input authority."""
    assert_issued_trial_binding(binding)
    assert_issued_trial_arm_execution(arm_execution)
    if arm_execution.binding is not binding:
        _fail("campaign-binding", "arm execution belongs to another binding object")
    if actual_campaign_id != binding.campaign_id:
        _fail("campaign-binding", "producer campaign_id differs from the manifest")


def _open_regular_snapshot(
    path: Path,
    *,
    gate: str,
    label: str,
) -> tuple[int, bytes]:
    """Read one regular-file snapshot while retaining its bound descriptor."""
    path = Path(path)
    try:
        before = path.lstat()
    except OSError as exc:
        raise TrialRegistryError(f"[{gate}] {label} cannot be stated: {path}") from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        _fail(gate, f"{label} must be a regular non-symlink file: {path}")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise TrialRegistryError(f"[{gate}] {label} cannot be opened: {path}") from exc
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode):
            _fail(gate, f"{label} changed away from a regular file: {path}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(fd)
        identity_before = (
            before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns,
        )
        if identity_before != identity_after:
            _fail(gate, f"{label} changed while it was being read: {path}")
        os.lseek(fd, 0, os.SEEK_SET)
        return fd, b"".join(chunks)
    except BaseException:
        os.close(fd)
        raise


def _read_report_and_journal(
    report_path: Path,
) -> _LoadedReport:
    original = Path(report_path)
    report_bytes = _read_regular_bytes(original, gate="report-path", label="report")
    try:
        resolved_report = original.resolve(strict=True)
    except OSError as exc:
        raise TrialRegistryError(f"[report-path] report cannot be resolved: {original}") from exc
    journal = resolved_report.parent / "attempts.jsonl"
    journal_fd, journal_bytes = _open_regular_snapshot(
        journal, gate="report-path", label="attempts journal",
    )
    try:
        expected_report = (journal.resolve(strict=True).parent / "report.json").resolve(strict=True)
    except OSError as exc:
        os.close(journal_fd)
        raise TrialRegistryError("[report-path] report/journal sibling identity cannot be resolved") from exc
    try:
        if resolved_report != expected_report:
            _fail("report-path", "report argument is not the attempts.jsonl sibling report.json")
        report = _decode_json(report_bytes, label="report")
        if not isinstance(report, dict):
            _fail("report-shape", "report root is not an object")
        if not journal_bytes or not journal_bytes.endswith(b"\n"):
            _fail("run-start-binding", "attempt journal is not newline terminated")
        events: list[Mapping[str, Any]] = []
        for lineno, line in enumerate(journal_bytes.splitlines(), 1):
            event = _decode_json(line, label=f"attempt journal line {lineno}")
            if not isinstance(event, Mapping):
                _fail("run-start-binding", f"attempt journal line {lineno} is not an object")
            events.append(event)
        return _LoadedReport(
            report,
            resolved_report,
            report_bytes,
            journal,
            journal_fd,
            journal_bytes,
            events,
        )
    except BaseException:
        os.close(journal_fd)
        raise


def _assert_snapshot_completeness(item: _LoadedReport) -> None:
    """Run the existing path API over a private view of the one read snapshot."""
    with tempfile.TemporaryDirectory(prefix="izanagi-trial-accept-") as raw_dir:
        snapshot_dir = Path(raw_dir)
        os.chmod(snapshot_dir, 0o700)
        snapshot_report_path = snapshot_dir / "report.json"
        fd, raw_path = tempfile.mkstemp(
            prefix="attempts-", suffix=".jsonl", dir=snapshot_dir,
        )
        snapshot_path = Path(raw_path)
        rebound_events = []
        for event in item.events:
            rebound = dict(event)
            if rebound.get("event") == "run-finish":
                rebound["report"] = str(snapshot_report_path)
            rebound_events.append(rebound)
        snapshot_bytes = b"".join(
            _canonical_json_bytes(event) + b"\n" for event in rebound_events
        )
        snapshot_report = dict(item.report)
        snapshot_report["attempt_journal"] = str(snapshot_path)
        snapshot_report["attempt_journal_sha256"] = hashlib.sha256(
            snapshot_bytes
        ).hexdigest()
        try:
            view = memoryview(snapshot_bytes)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError("journal snapshot copy did not advance")
                view = view[written:]
            os.fsync(fd)
        except OSError as exc:
            raise TrialRegistryError(
                f"[journal-snapshot] private snapshot cannot be written: {exc}"
            ) from exc
        finally:
            os.close(fd)
        try:
            snapshot_report_path.write_bytes(_canonical_json_bytes(snapshot_report))
        except OSError as exc:
            raise TrialRegistryError(
                f"[journal-snapshot] private report cannot be written: {exc}"
            ) from exc
        try:
            assert_autonomous_trial_completeness(
                report=snapshot_report,
                attempt_journal=snapshot_path,
            )
        except AutonomousTrialCompletenessError as exc:
            raise TrialRegistryError(f"[terminal-completeness] {exc}") from exc
        expected_hash = hashlib.sha256(item.journal_bytes).hexdigest()
        if item.report.get("attempt_journal_sha256") != expected_hash:
            _fail(
                "terminal-completeness",
                "attempt_journal_sha256 does not match the captured journal bytes",
            )
        journal_reference = item.report.get("attempt_journal")
        if not isinstance(journal_reference, str) or not journal_reference:
            _fail(
                "terminal-completeness",
                "report attempt_journal is not a non-empty path string",
            )
        try:
            same_journal = Path(journal_reference).samefile(item.journal_path)
        except OSError as exc:
            raise TrialRegistryError(
                "[terminal-completeness] report attempt_journal cannot be resolved"
            ) from exc
        if not same_journal:
            _fail(
                "terminal-completeness",
                "report attempt_journal differs from the captured journal path",
            )
        finishes = [
            event for event in item.events if event.get("event") == "run-finish"
        ]
        if len(finishes) != 1:
            _fail(
                "terminal-completeness",
                "captured journal must contain exactly one run-finish event",
            )
        finish_report = finishes[0].get("report")
        if (
            not isinstance(finish_report, str)
            or Path(finish_report).resolve()
            != (item.journal_path.parent / "report.json").resolve()
        ):
            _fail(
                "terminal-completeness",
                "run-finish report differs from the captured report path",
            )


def _assert_history_append_only(
    *,
    repository_root: Path,
    relative_path: str,
    measurement_head: str,
    current_head: str,
    measurement_bytes: bytes,
    current_bytes: bytes,
) -> None:
    _assert_ancestor(
        repository_root,
        ancestor=measurement_head,
        descendant=current_head,
        gate="registry-history",
        message="measurement_head is not an ancestor of current HEAD",
    )
    result = _git(repository_root, (
        "rev-list", "--full-history", "--reverse", "--topo-order",
        f"{measurement_head}..{current_head}", "--", relative_path,
    ))
    if result.returncode != 0:
        raise TrialRegistryError("[git-operational] registry history walk failed")
    previous = measurement_bytes
    for raw_commit in result.stdout.splitlines():
        try:
            commit_id = raw_commit.decode("ascii")
        except UnicodeDecodeError as exc:
            raise TrialRegistryError("[git-operational] history returned non-ASCII commit") from exc
        if _COMMIT_RE.fullmatch(commit_id) is None:
            _fail("registry-history", "history returned an invalid commit ID")
        blob = _blob_at_commit(
            repository_root, commit_id=commit_id, relative_path=relative_path,
        )
        if blob is None:
            _fail("registry-history", "registry path was deleted in committed history")
        if not blob.startswith(previous) or len(blob) <= len(previous):
            _fail("registry-history", "registry history is not a strict prefix extension")
        _load_registry_bytes(blob, label=f"registry at {commit_id}")
        previous = blob
    if previous != current_bytes:
        _fail("registry-history", "history endpoint differs from current registry blob")


def _registry_introduction_commit(
    *,
    repository_root: Path,
    relative_path: str,
    current_head: str,
) -> str:
    """Return the sole commit that introduced the registry path.

    This proves only that the registry path has one history genesis.  It is
    not an approval-authority attestation and must never be interpreted as
    evidence that T-468 approval authority exists.
    """
    result = _git(repository_root, (
        "log", "--format=%H", "--diff-filter=A", "--full-history",
        current_head, "--", relative_path,
    ))
    if result.returncode != 0:
        raise TrialRegistryError(
            "[git-operational] registry introduction history walk failed"
        )
    introductions: list[str] = []
    for raw in result.stdout.splitlines():
        try:
            commit_id = raw.decode("ascii")
        except UnicodeDecodeError as exc:
            raise TrialRegistryError(
                "[git-operational] registry introduction returned non-ASCII"
            ) from exc
        if _COMMIT_RE.fullmatch(commit_id) is None:
            _fail("registry-introduction", "history returned an invalid commit ID")
        if _blob_at_commit(
            repository_root,
            commit_id=commit_id,
            relative_path=relative_path,
        ) is None:
            _fail("registry-introduction", "introduction commit has no registry blob")
        introductions.append(commit_id)
    if len(introductions) != 1:
        _fail(
            "registry-introduction",
            "registry path must have exactly one introduction commit",
        )
    return introductions[0]


def _receipt_lifecycle_snapshot(
    *,
    repository_root: Path,
    lifecycle_path: Path,
    manifest: TrialManifest,
    accepted_by_id: Mapping[str, AcceptedTrial],
    loaded_by_id: Mapping[str, _LoadedReport],
    activation_report_digest_sha256: str,
    attempt_rows: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[bytes, str]:
    lifecycle, relative = _canonical_lifecycle_target(
        lifecycle_path, repository_root, create_parent=False,
    )
    lifecycle_bytes = _read_regular_bytes(
        lifecycle, gate="lifecycle-read", label="lifecycle ledger",
    )
    history_tip = _lifecycle_history_tip(
        repository_root=repository_root,
        relative_path=relative,
        current_head=resolve_measurement_commit(repository_root),
    )
    if history_tip is not None and not lifecycle_bytes.startswith(history_tip):
        _fail(
            "lifecycle-history",
            "working lifecycle ledger does not extend committed history",
        )
    rows = _load_lifecycle_rows(lifecycle_bytes)
    for trial in manifest.trials:
        starts = [
            row for row in rows
            if row["event"] == "start" and row["trial_id"] == trial.trial_id
        ]
        terminals = [
            row for row in rows
            if row["event"] == "terminal" and row["trial_id"] == trial.trial_id
        ]
        if len(starts) != 1:
            _fail(
                "acceptance-lifecycle",
                f"trial {trial.trial_id!r} must have exactly one start row",
            )
        if len(terminals) != 1:
            _fail(
                "acceptance-lifecycle",
                f"trial {trial.trial_id!r} must have exactly one terminal row",
            )
        accepted = accepted_by_id[trial.trial_id]
        item = loaded_by_id[trial.trial_id]
        start = starts[0]
        report_admission = item.report.get("launch_admission")
        report_has_origin_binding = (
            isinstance(report_admission, Mapping)
            and "origin_binding" in report_admission
        )
        if report_has_origin_binding != ("origin_run_plan_sha256" in start):
            _fail(
                "acceptance-lifecycle",
                f"trial {trial.trial_id!r} launch origin binding and lifecycle "
                "run-plan digest presence differ",
            )
        try:
            start_run_root = Path(start["run_root"]).resolve(strict=True)
            report_parent = item.report_path.parent.resolve(strict=True)
            journal_parent = item.journal_path.parent.resolve(strict=True)
        except OSError as exc:
            raise TrialRegistryError(
                "[acceptance-lifecycle] run artifact parent cannot be resolved"
            ) from exc
        if start_run_root != report_parent or start_run_root != journal_parent:
            _fail(
                "acceptance-lifecycle",
                f"trial {trial.trial_id!r} start run_root differs from "
                "report/journal parent",
            )
        if (
            start["manifest_sha256"] != manifest.sha256
            or start["prereg_commit"] != manifest.prereg_commit
            or start["prereg_content_commit"]
            != item.report.get("prereg_content_commit")
            or item.report.get("prereg_effective_commit")
            != start["prereg_effective_commit"]
            or start["measurement_head"] != accepted.measurement_head
            or start["activation_report_digest_sha256"]
            != activation_report_digest_sha256
            or start["launch_admission_sha256"]
            != hashlib.sha256(
                _canonical_json_bytes(item.report["launch_admission"])
            ).hexdigest()
        ):
            _fail(
                "acceptance-lifecycle",
                f"trial {trial.trial_id!r} start row differs from accepted bytes",
            )
        terminal = terminals[0]
        if attempt_rows is not None:
            attempt_starts = [
                row for row in attempt_rows
                if row.get("event") == "start"
                and row.get("slot_id") == start["slot_id"]
            ]
            attempt_terminals = [
                row for row in attempt_rows
                if row.get("event") == "terminal"
                and row.get("slot_id") == start["slot_id"]
            ]
            if len(attempt_starts) != 1 or len(attempt_terminals) != 1:
                _fail(
                    "acceptance-lifecycle",
                    f"trial {trial.trial_id!r} has no exact attempt slot pair",
                )
            attempt_start = attempt_starts[0]
            attempt_terminal = attempt_terminals[0]
            if (
                start["schedule_row_sha256"] != attempt_start["schedule_row_sha256"]
                or _canonical_json_bytes(start["process_identity"])
                != _canonical_json_bytes(attempt_start["process_identity"])
                or terminal["classification_receipt_sha256"]
                != attempt_terminal["classification_receipt_sha256"]
                or terminal["raw_output_sha256"] != attempt_terminal["raw_output_sha256"]
            ):
                _fail(
                    "acceptance-lifecycle",
                    f"trial {trial.trial_id!r} lifecycle slot artifacts differ",
                )
        report_has_origin = "origin_terminal_projection" in item.report
        terminal_has_origin = "origin_terminal_projection" in terminal
        if report_has_origin != terminal_has_origin:
            _fail(
                "acceptance-lifecycle",
                f"trial {trial.trial_id!r} origin terminal projection presence differs",
            )
        if report_has_origin:
            report_projection = _validate_origin_terminal_projection(
                item.report["origin_terminal_projection"],
                gate="acceptance-lifecycle",
            )
            lifecycle_projection = _validate_origin_terminal_projection(
                terminal["origin_terminal_projection"],
                gate="acceptance-lifecycle",
            )
            if _canonical_json_bytes(report_projection) != _canonical_json_bytes(
                lifecycle_projection
            ):
                _fail(
                    "acceptance-lifecycle",
                    f"trial {trial.trial_id!r} origin terminal projection differs",
                )
        if (
            terminal["terminal_status"] != accepted.status
            or terminal["report_sha256"]
            != hashlib.sha256(item.report_bytes).hexdigest()
            or terminal["attempt_journal_sha256"]
            != hashlib.sha256(item.journal_bytes).hexdigest()
        ):
            _fail(
                "acceptance-lifecycle",
                f"trial {trial.trial_id!r} terminal row differs from accepted bytes",
            )
    return lifecycle_bytes, relative


def _expected_registered_launch_admission_record(
    *,
    manifest_path: Path,
    registry_path: Path,
    repository_root: Path,
    trial: TrialSpec,
    measurement_head: str,
    activation_report_digest_sha256: str,
    origin_binding_record: object | None = None,
) -> dict[str, Any]:
    workload = HOLDOUT_BINDINGS[trial.holdout]["workload"]
    manifest = load_trial_manifest(manifest_path)
    manifest_relative = _require_committed_file(
        repository_root=repository_root,
        commit_id=measurement_head,
        path=manifest_path,
        label="manifest",
        expected_bytes=manifest.raw_bytes,
    )
    _registry, registry_relative = _registry_target(
        registry_path, repository_root, create_parent=False,
    )
    registry_bytes = _blob_at_commit(
        repository_root,
        commit_id=measurement_head,
        relative_path=registry_relative,
    )
    if registry_bytes is None:
        _fail("historical-binding", "measurement registry blob is absent")
    registration = _find_registration_for_manifest(
        _load_registry_bytes(registry_bytes, label="measurement registry"),
        manifest,
        allow_distinct_content_commit=True,
    )
    effective_binding = validate_preregistration_binding(
        repository_root,
        manifest_path=manifest_path,
        effective_commit=registration.prereg_effective_commit,
        measurement_commit=measurement_head,
    )
    if effective_binding.prereg_content_commit != registration.prereg_content_commit:
        _fail("historical-binding", "measurement registry P differs from effective binding")
    if manifest_relative == registry_relative:
        _fail("historical-binding", "manifest and registry paths alias")
    binding = {
        "manifest_sha256": manifest.sha256,
        "prereg_commit": manifest.prereg_commit,
        "prereg_content_commit": registration.prereg_content_commit,
        "prereg_effective_commit": registration.prereg_effective_commit,
        "measurement_head": measurement_head,
        "trial_id": trial.trial_id,
        "arm": trial.arm,
        "holdout": trial.holdout,
        "campaign_id": trial.campaign_id,
        "workload": workload,
        "ycsb_rratio": HOLDOUT_BINDINGS[trial.holdout]["ycsb_rratio"],
    }
    record = {
        "mode": "registered-effective",
        "certifying": False,
        "reason_code": "registered-effective-non-certifying",
        "trial_id": trial.trial_id,
        "workloads": [workload],
        "binding": binding,
        "prereg_content_commit": registration.prereg_content_commit,
        "prereg_effective_commit": registration.prereg_effective_commit,
        "activation_report_digest_sha256": activation_report_digest_sha256,
    }
    if origin_binding_record is not None:
        record["origin_binding"] = _validate_origin_binding_record(
            origin_binding_record,
            trial=trial,
            measurement_head=measurement_head,
            gate="acceptance-launch-admission",
        )
    return record


def _expected_registered_arm_execution_record(
    *,
    repository_root: Path,
    trial: TrialSpec,
    measurement_head: str,
) -> dict[str, str]:
    """Independently resolve the historical arm bytes for acceptance."""
    try:
        resolved = s8c_arm_inputs.resolve_arm_input(
            arm=trial.arm,
            holdout=trial.holdout,
            repository_root=repository_root,
            commit=measurement_head,
        )
    except s8c_arm_inputs.ArmInputError as exc:
        _fail("acceptance-arm-execution", str(exc))
    return {
        "input_schema_version": resolved.input_schema_version,
        "content_digest_sha256": resolved.content_digest_sha256,
        "arm_binding_digest_sha256": resolved.arm_binding_digest_sha256,
    }


def _exclusive_create_acceptance_receipt(
    *,
    repository_root: Path,
    manifest_sha256: str,
    value: Mapping[str, Any],
    publication_guard=None,
) -> tuple[str, str]:
    relative_path = Path(
        s8c_acceptance_receipt.DEFAULT_RECEIPT_DIR.as_posix()
    ) / f"{manifest_sha256}.json"
    parent_fd = _open_registry_parent(
        repository_root, relative_path.parent, create=True,
    )
    payload = _canonical_json_bytes(value) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        if publication_guard is not None:
            publication_guard()
        try:
            fd = os.open(relative_path.name, flags, 0o644, dir_fd=parent_fd)
        except FileExistsError as exc:
            raise TrialRegistryError(
                "[receipt-exclusive-create] acceptance receipt already exists"
            ) from exc
        try:
            view = memoryview(payload)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError("receipt write did not advance")
                view = view[written:]
            os.fsync(fd)
            os.fsync(parent_fd)
        finally:
            os.close(fd)
        if publication_guard is not None:
            try:
                publication_guard()
            except BaseException:
                try:
                    os.unlink(relative_path.name, dir_fd=parent_fd)
                    os.fsync(parent_fd)
                except OSError as cleanup_error:
                    raise TrialRegistryError(
                        "[receipt-cleanup] invalidated acceptance receipt "
                        f"cannot be removed: {cleanup_error}"
                    ) from cleanup_error
                raise
    except TrialRegistryError:
        raise
    except OSError as exc:
        raise TrialRegistryError(f"[receipt-io] receipt cannot be created: {exc}") from exc
    finally:
        os.close(parent_fd)
    return relative_path.as_posix(), hashlib.sha256(payload).hexdigest()


def _diagnostic_text_value(value: str) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= 64:
        return repr(value)
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _read_acceptance_measurement_targets(
    loaded: Sequence[_LoadedReport],
) -> tuple[tuple[str, Path, bytes], ...]:
    """Require one shared CCBench/environment target across materialized trials."""
    complete_build_bundle = True
    snapshots: list[tuple[str, Path, bytes]] = []
    targets: list[tuple[str, Path]] = []
    missing_targets: list[tuple[str, Path]] = []
    identities: list[tuple[str, Path, str, str]] = []
    for item in loaded:
        report = item.report
        trial_id = report.get("trial_id")
        do_build = report.get("do_build")
        if type(do_build) is not bool:
            _fail("campaign-chain", "report.do_build is not a bool")
        if do_build is False:
            complete_build_bundle = False
            continue
        cells = report.get("cells")
        if not isinstance(cells, list) or len(cells) > 1:
            _fail(
                "terminal-projection",
                "report cells must contain zero or one cell",
            )
        if not cells:
            _fail(
                "campaign-chain",
                "do_build=True requires a non-empty report.cells list",
            )
        cell = cells[0]
        if not isinstance(cell, Mapping):
            _fail("campaign-chain", "cells[0] is not an object")
        if is_exact_campaignless_failure_fallback_cell(cell):
            complete_build_bundle = False
            continue
        campaign_root_value = cell.get("campaign_root")
        if type(campaign_root_value) is not str or not campaign_root_value:
            _fail(
                "campaign-chain",
                "cells[0].campaign_root is required for build",
            )
        run_root = item.journal_path.resolve().parent
        try:
            declared_campaign_root = Path(campaign_root_value)
            campaign_root = (
                declared_campaign_root
                if declared_campaign_root.is_absolute()
                else run_root / declared_campaign_root
            ).resolve(strict=True)
        except (OSError, ValueError) as exc:
            raise TrialRegistryError(
                "[campaign-chain] cells[0].campaign_root cannot be resolved"
            ) from exc
        if not campaign_root.is_dir():
            _fail("campaign-chain", "cells[0].campaign_root is not a directory")
        layer3_path = campaign_root / "reports" / "layer3_report.json"
        trial_id_text = str(trial_id)
        targets.append((trial_id_text, layer3_path))
        if not layer3_path.exists() and not layer3_path.is_symlink():
            missing_targets.append((trial_id_text, layer3_path))
            continue
        layer3_bytes = _read_regular_bytes(
            layer3_path,
            gate="measurement-target",
            label=f"trial {trial_id!r} layer3 report",
        )
        layer3 = _decode_json(
            layer3_bytes,
            label=f"trial {trial_id!r} layer3 report",
        )
        if not isinstance(layer3, Mapping):
            _fail("measurement-target", f"trial {trial_id!r} layer3 report is not an object")
        meta = layer3.get("meta")
        ccbench_commit = meta.get("ccbench_commit") if isinstance(meta, Mapping) else None
        if not isinstance(ccbench_commit, str) or not ccbench_commit:
            _fail(
                "measurement-target",
                f"trial {trial_id!r} layer3 meta.ccbench_commit is not a non-empty string",
            )
        env_tags = layer3.get("env_tags")
        if type(env_tags) is not list:
            _fail(
                "measurement-target",
                f"trial {trial_id!r} layer3 env_tags is not a list",
            )
        if (
            len(env_tags) != 1
            or not isinstance(env_tags[0], str)
            or not env_tags[0]
        ):
            _fail(
                "measurement-target",
                f"trial {trial_id!r} layer3 env_tags must contain exactly one non-empty string",
            )
        snapshots.append((trial_id_text, layer3_path, layer3_bytes))
        identities.append(
            (trial_id_text, layer3_path, ccbench_commit, env_tags[0])
        )

    if complete_build_bundle and len(snapshots) != 6:
        if snapshots:
            reference_trial_id = snapshots[0][0]
        elif targets:
            reference_trial_id = targets[0][0]
        else:
            reference_trial_id = "<none>"
        missing_detail = ", ".join(
            f"trial {trial_id!r} value=<missing> path={str(path)!r}"
            for trial_id, path in missing_targets
        )
        _fail(
            "measurement-target",
            "complete build bundle requires exactly 6 readable layer3 reports; "
            f"found {len(snapshots)}; reference trial {reference_trial_id!r}; "
            f"missing=[{missing_detail}]",
        )
    if identities:
        baseline_trial_id, baseline_path, baseline_ccbench, baseline_env = identities[0]
        for trial_id, path, ccbench_commit, env_tag in identities[1:]:
            if ccbench_commit != baseline_ccbench:
                _fail(
                    "measurement-target",
                    "layer3 reports do not share one meta.ccbench_commit; "
                    f"baseline trial {baseline_trial_id!r} "
                    f"value={_diagnostic_text_value(baseline_ccbench)} "
                    f"path={str(baseline_path)!r}; differing trial {trial_id!r} "
                    f"value={_diagnostic_text_value(ccbench_commit)} "
                    f"path={str(path)!r}",
                )
            if env_tag != baseline_env:
                _fail(
                    "measurement-target",
                    "layer3 reports do not share one env_tag; "
                    f"baseline trial {baseline_trial_id!r} "
                    f"value={_diagnostic_text_value(baseline_env)} "
                    f"path={str(baseline_path)!r}; differing trial {trial_id!r} "
                    f"value={_diagnostic_text_value(env_tag)} "
                    f"path={str(path)!r}",
                )
    return tuple(snapshots)


def assert_trial_registry_acceptance(
    *,
    effective_preregistration: s8c_preregistration.EffectivePreregistration,
    manifest_path: Path,
    report_paths: Sequence[Path],
    repository_root: Path,
    registry_path: Path,
    lifecycle_path: Path = DEFAULT_LIFECYCLE_PATH,
) -> AcceptanceSummary:
    """Verify formal acceptance and exclusively issue its canonical receipt."""
    if len(report_paths) != 6:
        _fail("report-count", "acceptance requires exactly 6 report paths")
    root = _repository_root(repository_root)
    current_head = resolve_measurement_commit(root)
    manifest = load_trial_manifest(Path(manifest_path))
    if (
        not isinstance(
            effective_preregistration,
            s8c_preregistration.EffectivePreregistration,
        )
        or effective_preregistration.commit != manifest.prereg_commit
    ):
        _fail(
            "effective-preregistration",
            "acceptance requires the manifest's exact EffectivePreregistration",
        )
    try:
        s8c_preregistration.require_effective_preregistration(
            effective_preregistration,
            repo_root=root,
            commit=manifest.prereg_commit,
        )
    except s8c_preregistration.PreregistrationError as exc:
        _fail("effective-preregistration", f"{exc.reason}: {exc}")
    manifest_relative = _require_committed_file(
        repository_root=root,
        commit_id=current_head,
        path=Path(manifest_path),
        label="manifest",
        expected_bytes=manifest.raw_bytes,
    )
    registrations, current_registry_bytes, registry_relative = _load_committed_registry(
        repository_root=root,
        registry_path=Path(registry_path),
        commit_id=current_head,
    )
    registration = _find_registration_for_manifest(
        registrations,
        manifest,
        allow_distinct_content_commit=True,
    )
    effective_binding = validate_preregistration_binding(
        root,
        manifest_path=Path(manifest_path),
        effective_commit=registration.prereg_effective_commit,
        measurement_commit=current_head,
    )
    if effective_binding.prereg_content_commit != registration.prereg_content_commit:
        _fail("registration-binding", "registry P differs from effective binding")
    loaded: list[_LoadedReport] = []
    attempt_snapshot: _LockedAttemptRegistrySnapshot | None = None
    try:
        for path in report_paths:
            loaded.append(_read_report_and_journal(Path(path)))
        _assert_runtime_report_trial_set(loaded, manifest)
        measurement_target_snapshots = _read_acceptance_measurement_targets(loaded)

        manifest_by_id = {trial.trial_id: trial for trial in manifest.trials}
        accepted: list[AcceptedTrial] = []
        no_build_seen = False
        cross_binding_receipts: dict[str, dict[str, Any]] = {}
        history_checked: set[str] = set()
        common_measurement_head: str | None = None
        for item in loaded:
            report = item.report
            events = item.events
            trial_id = report["trial_id"]
            trial = manifest_by_id[trial_id]
            item.assert_snapshot_unchanged()
            if (
                report.get("generation_budget_per_workload")
                != trial.generations
            ):
                _fail(
                    "generation-binding",
                    "report generation_budget_per_workload differs from "
                    f"manifest.trials[{trial_id!r}].generations",
                )
            starts = [event for event in events if event.get("event") == "run-start"]
            if len(starts) != 1:
                _fail("run-start-binding", "journal must contain exactly one run-start event")
            start = starts[0]
            for field in (
                "prereg_commit", "prereg_content_commit",
                "prereg_effective_commit", "measurement_head",
                "manifest_sha256", "slot_id",
            ):
                if field not in report or field not in start or report[field] != start[field]:
                    _fail("run-start-binding", f"report/run-start mismatch or missing field: {field}")
            if report["prereg_commit"] != manifest.prereg_commit:
                _fail("acceptance-binding", "report prereg_commit differs from manifest")
            if report["prereg_content_commit"] != registration.prereg_content_commit:
                _fail(
                    "acceptance-binding",
                    "report prereg_content_commit differs from registry",
                )
            if report["prereg_effective_commit"] != registration.prereg_effective_commit:
                _fail(
                    "acceptance-binding",
                    "report prereg_effective_commit differs from registry",
                )
            if report["manifest_sha256"] != manifest.sha256:
                _fail("acceptance-binding", "report manifest_sha256 differs from manifest bytes")
            if report["slot_id"] != start["slot_id"]:
                _fail("attempt-slot", "report slot_id differs from run-start")
            measurement_head = report["measurement_head"]
            if not isinstance(measurement_head, str) or _COMMIT_RE.fullmatch(measurement_head) is None:
                _fail("acceptance-binding", "report measurement_head is not a full commit ID")
            if common_measurement_head is None:
                common_measurement_head = measurement_head
            elif measurement_head != common_measurement_head:
                _fail(
                    "measurement-head-coherence",
                    "reports do not share one measurement_head",
                )
            _assert_snapshot_completeness(item)
            report_admission = report.get("launch_admission")
            start_admission = start.get("launch_admission")
            if (
                not isinstance(report_admission, Mapping)
                or not isinstance(start_admission, Mapping)
                or dict(report_admission) != dict(start_admission)
            ):
                _fail(
                    "acceptance-launch-admission",
                    "report and run-start launch_admission must exist and match exactly",
                )
            if frozenset(report_admission) not in _LAUNCH_ADMISSION_KEYS:
                _fail(
                    "acceptance-launch-admission",
                    "launch_admission exact keys are not the closed 7/8 alternatives",
                )
            origin_binding_record = None
            if "origin_binding" in report_admission:
                origin_binding_record = _validate_origin_binding_record(
                    report_admission["origin_binding"],
                    trial=trial,
                    measurement_head=measurement_head,
                    gate="acceptance-launch-admission",
                )
            expected_admission = _expected_registered_launch_admission_record(
                manifest_path=Path(manifest_path),
                registry_path=Path(registry_path),
                repository_root=root,
                trial=trial,
                measurement_head=measurement_head,
                activation_report_digest_sha256=(
                    effective_preregistration.report_digest_sha256
                ),
                origin_binding_record=origin_binding_record,
            )
            if dict(report_admission) != expected_admission:
                _fail(
                    "acceptance-launch-admission",
                    "launch_admission differs from the accepted binding derivation",
                )
            has_terminal_projection = "origin_terminal_projection" in report
            if (origin_binding_record is None) != (not has_terminal_projection):
                _fail(
                    "acceptance-origin",
                    "origin binding and terminal projection presence differ",
                )
            terminal_projection = None
            if origin_binding_record is not None:
                terminal_projection = _validate_origin_terminal_projection(
                    report["origin_terminal_projection"],
                    gate="acceptance-origin",
                )
                if any(
                    terminal_projection[field] != origin_binding_record[field]
                    for field in (
                        "authority_blob_sha256", "origin_id", "cell_key",
                    )
                ):
                    _fail(
                        "acceptance-origin",
                        "terminal projection differs from launch origin binding",
                    )
            historical_manifest = _blob_at_commit(
                root, commit_id=measurement_head, relative_path=manifest_relative,
            )
            if historical_manifest != manifest.raw_bytes:
                _fail("historical-binding", "measurement manifest blob differs or is absent")
            historical_registry = _blob_at_commit(
                root, commit_id=measurement_head, relative_path=registry_relative,
            )
            if historical_registry is None:
                _fail("historical-binding", "measurement registry blob is absent")
            historical_registrations = _load_registry_bytes(
                historical_registry, label="measurement registry",
            )
            historical_registration = _find_registration_for_manifest(
                historical_registrations,
                manifest,
                effective_commit=registration.prereg_effective_commit,
                allow_distinct_content_commit=True,
            )
            if (
                historical_registration.prereg_commit != registration.prereg_commit
                or historical_registration.prereg_content_commit
                != registration.prereg_content_commit
                or historical_registration.prereg_effective_commit
                != registration.prereg_effective_commit
            ):
                _fail(
                    "historical-binding",
                    "measurement registry P/C differs from current registration",
                )
            if not current_registry_bytes.startswith(historical_registry):
                _fail("registry-prefix", "measurement registry is not a current registry prefix")
            if measurement_head not in history_checked:
                _assert_history_append_only(
                    repository_root=root,
                    relative_path=registry_relative,
                    measurement_head=measurement_head,
                    current_head=current_head,
                    measurement_bytes=historical_registry,
                    current_bytes=current_registry_bytes,
                )
                history_checked.add(measurement_head)
            report_arm_execution = report.get("arm_execution")
            start_arm_execution = start.get("arm_execution")
            if (
                type(report_arm_execution) is not dict
                or type(start_arm_execution) is not dict
                or report_arm_execution != start_arm_execution
            ):
                _fail(
                    "acceptance-arm-execution",
                    "report and run-start arm_execution must exist and match exactly",
                )
            expected_arm_execution = _expected_registered_arm_execution_record(
                repository_root=root,
                trial=trial,
                measurement_head=measurement_head,
            )
            if report_arm_execution != expected_arm_execution:
                _fail(
                    "acceptance-arm-execution",
                    "arm_execution differs from historical input derivation",
                )
            if (
                terminal_projection is not None
                and terminal_projection["arm_binding_digest_sha256"]
                != expected_arm_execution["arm_binding_digest_sha256"]
            ):
                _fail(
                    "acceptance-origin",
                    "terminal projection differs from arm execution binding",
                )
            expected_workload = HOLDOUT_BINDINGS[trial.holdout]
            if report.get("workloads_requested") != [expected_workload["workload"]]:
                _fail("terminal-projection", "report workload does not match trial holdout")
            cells = report.get("cells")
            if not isinstance(cells, list) or len(cells) > 1:
                _fail("terminal-projection", "report cells must contain zero or one cell")
            if cells:
                cell = cells[0]
                if not isinstance(cell, Mapping):
                    _fail("terminal-projection", "report cell is not an object")
                failure_cell = (
                    is_exact_cell_admission_failure_decision(
                        cell.get("admission_decision")
                    )
                    and is_exact_campaignless_failure_fallback_cell(cell)
                )
                if cell.get("workload") != expected_workload["workload"]:
                    _fail("terminal-projection", "report cell differs from manifest projection")
                if not failure_cell:
                    _assert_holdout_cell_condition(
                        cell,
                        expected=expected_workload,
                        campaign_id=trial.campaign_id,
                        gate="terminal-projection",
                        message="report cell differs from manifest projection",
                    )
            cells = _assert_runtime_report_cells(report, trial=trial)
            if cells:
                cell = cells[0]
                descriptor = cell.get("descriptor")
                descriptor_binding = cell.get("descriptor_binding")
                if failure_cell:
                    descriptor = None
                    descriptor_binding = None
                if not failure_cell and (
                    not isinstance(descriptor, Mapping)
                    or not isinstance(descriptor_binding, Mapping)
                ):
                    _fail(
                        "acceptance-arm-execution",
                        "cell descriptor authority is absent",
                    )
                if not failure_cell:
                    try:
                        descriptor_raw = (
                            s8c_arm_inputs.validate_execution_input_descriptor(descriptor)
                        )
                    except s8c_arm_inputs.ArmInputError as exc:
                        _fail("acceptance-arm-execution", str(exc))
                    descriptor_digest = hashlib.sha256(descriptor_raw).hexdigest()
                    if (
                        descriptor_digest
                        != expected_arm_execution["content_digest_sha256"]
                        or descriptor_binding.get("output_sha256")
                        != descriptor_digest
                    ):
                        _fail(
                            "acceptance-arm-execution",
                            "cell descriptor differs from sealed execution input",
                        )
            status = report.get("status")
            if not isinstance(status, str):
                _fail("terminal-projection", "report status is not a string")
            try:
                assert_execution_digest_chain(
                    report=report,
                    events=events,
                    run_root=item.journal_path.resolve().parent,
                )
            except AutonomousTrialCompletenessError as exc:
                raise TrialRegistryError(f"[terminal-completeness] {exc}") from exc
            do_build = report.get("do_build")
            if type(do_build) is not bool:
                _fail("campaign-chain", "report.do_build is not a bool")
            run_root = item.journal_path.resolve().parent
            if do_build is False:
                no_build_seen = True
                layer3_output_root = None
            else:
                cells = report.get("cells")
                if not isinstance(cells, list) or not cells:
                    _fail(
                        "campaign-chain",
                        "do_build=True requires a non-empty report.cells list",
                    )
                campaign_roots: list[Path] = []
                bypassed_cell_indices: list[int] = []
                for index, cell in enumerate(cells):
                    if not isinstance(cell, Mapping):
                        _fail("campaign-chain", f"cells[{index}] is not an object")
                    if is_exact_campaignless_failure_fallback_cell(cell):
                        bypassed_cell_indices.append(index)
                        continue
                    campaign_root_value = cell.get("campaign_root")
                    if type(campaign_root_value) is not str or not campaign_root_value:
                        _fail(
                            "campaign-chain",
                            f"cells[{index}].campaign_root is required for build",
                        )
                    try:
                        declared_campaign_root = Path(campaign_root_value)
                        campaign_root = (
                            declared_campaign_root
                            if declared_campaign_root.is_absolute()
                            else run_root / declared_campaign_root
                        ).resolve(strict=True)
                    except (OSError, ValueError) as exc:
                        raise TrialRegistryError(
                            f"[campaign-chain] cells[{index}].campaign_root cannot be resolved"
                        ) from exc
                    if not campaign_root.is_dir():
                        _fail(
                            "campaign-chain",
                            f"cells[{index}].campaign_root is not a directory",
                        )
                    campaign_roots.append(campaign_root)
                if campaign_roots:
                    layer3_output_root = campaign_roots[0].parent.parent
                    if any(
                        campaign_root.parent.parent != layer3_output_root
                        for campaign_root in campaign_roots
                    ):
                        _fail(
                            "campaign-chain",
                            "build cells do not share one campaign output root",
                        )
                    report_output_root = run_root.parent.parent
                    if layer3_output_root != report_output_root:
                        _fail(
                            "campaign-chain",
                            "campaign output root differs from report run root",
                        )
                else:
                    layer3_output_root = None
                try:
                    assert_campaign_layer3_chain(
                        report=report,
                        output_root=(
                            layer3_output_root
                            if layer3_output_root is not None
                            else run_root / "_no_campaign_output"
                        ),
                    )
                except AutonomousTrialCompletenessError as exc:
                    raise TrialRegistryError(f"[campaign-chain] {exc}") from exc
                if bypassed_cell_indices:
                    _fail(
                        "campaign-chain",
                        "campaignless failure fallback bypassed Layer-3 "
                        f"validation for cells {bypassed_cell_indices}",
                    )
                if any(
                    not (campaign_root / "reports" / "layer3_report.json").is_file()
                    for campaign_root in campaign_roots
                ):
                    _fail(
                        "campaign-chain",
                        "build cell has no persisted "
                        "reports/layer3_report.json after Layer-3 chain",
                    )
            try:
                cross_binding_receipts[trial_id] = verify_s8c_cross_binding(
                    report=report,
                    events=events,
                    run_root=run_root,
                    output_root=layer3_output_root,
                )
            except AutonomousTrialCompletenessError as exc:
                raise TrialRegistryError(f"[cross-binding] {exc}") from exc
            accepted.append(AcceptedTrial(trial_id, status, measurement_head))
        accepted.sort(key=lambda accepted_trial: accepted_trial.trial_id)
        accepted_by_id = {item.trial_id: item for item in accepted}
        loaded_by_id = {item.report["trial_id"]: item for item in loaded}
        attempt_snapshot = _open_locked_attempt_registry_snapshot(
            repository_root=root,
            registry_path=DEFAULT_ATTEMPT_REGISTRY_PATH,
        )
        attempt_rows = assert_formal_attempt_registry_acceptance(
            repository_root=root,
            manifest_path=Path(manifest_path),
            manifest=manifest,
            effective_binding=effective_binding,
            effective_commit=registration.prereg_effective_commit,
            report_paths=report_paths,
        )
        attempt_snapshot.assert_rows(attempt_rows)
        # Current v3 rows are accepted for new outer-receipt projection.  A
        # readable legacy v1/v2 root is rejected for new formal issuance.
        if attempt_rows[0]["schema_version"] != ATTEMPT_REGISTRY_SCHEMA_VERSION:
            _fail(
                "attempt-prereg-generation",
                "new formal acceptance requires attempt registry schema v3",
            )
        initial_attempt_slots = sorted(
            (
                slot for slot in attempt_rows[0]["slots"]
                if slot["attempt_index"] == 0
            ),
            key=lambda slot: slot["slot_id"],
        )
        attempt_generations = {
            slot["prereg_generation"] for slot in attempt_rows[0]["slots"]
        }
        if not initial_attempt_slots or len(attempt_generations) != 1:
            _fail(
                "attempt-prereg-generation",
                "formal attempt projection is empty or generation-mixed",
            )
        attempt_slot_projection = {
            "prereg_generation": next(iter(attempt_generations)),
            "unit_count": len(initial_attempt_slots),
            "units": [
                {
                    "slot_id": slot["slot_id"],
                    "trial_id": slot["trial_id"],
                    "arm": slot["arm"],
                    "holdout": slot["holdout"],
                    "campaign_id": slot["campaign_id"],
                    "replicate_index": slot["replicate_index"],
                }
                for slot in initial_attempt_slots
            ],
        }
        lifecycle_bytes, lifecycle_relative = _receipt_lifecycle_snapshot(
            repository_root=root,
            lifecycle_path=Path(lifecycle_path),
            manifest=manifest,
            accepted_by_id=accepted_by_id,
            loaded_by_id=loaded_by_id,
            activation_report_digest_sha256=(
                effective_preregistration.report_digest_sha256
            ),
            attempt_rows=attempt_rows,
        )
        introduction_commit = _registry_introduction_commit(
            repository_root=root,
            relative_path=registry_relative,
            current_head=current_head,
        )
        if measurement_target_snapshots:
            baseline_trial_id, baseline_path, baseline_bytes = (
                measurement_target_snapshots[0]
            )
        else:
            baseline_trial_id, baseline_path, baseline_bytes = (
                "<none>",
                Path("<none>"),
                b"",
            )
        for trial_id, layer3_path, expected_bytes in measurement_target_snapshots:
            observed_bytes = _read_regular_bytes(
                layer3_path,
                gate="measurement-target-snapshot",
                label=f"trial {trial_id!r} layer3 report",
            )
            if observed_bytes != expected_bytes:
                _fail(
                    "measurement-target-snapshot",
                    "layer3 report changed during acceptance; "
                    f"baseline trial {baseline_trial_id!r} "
                    f"sha256={hashlib.sha256(baseline_bytes).hexdigest()} "
                    f"path={str(baseline_path)!r}; differing trial {trial_id!r} "
                    f"expected_sha256={hashlib.sha256(expected_bytes).hexdigest()} "
                    f"observed_sha256={hashlib.sha256(observed_bytes).hexdigest()} "
                    f"path={str(layer3_path)!r}",
                )
        receipt_trials: list[dict[str, Any]] = []
        descriptor_proofs: list[bool] = []
        for trial in sorted(manifest.trials, key=lambda item: item.trial_id):
            item = loaded_by_id[trial.trial_id]
            accepted_trial = accepted_by_id[trial.trial_id]
            item.assert_snapshot_unchanged()
            if _read_regular_bytes(
                item.report_path, gate="report-snapshot", label="trial report",
            ) != item.report_bytes:
                _fail(
                    "report-snapshot",
                    f"trial {trial.trial_id!r} report changed during acceptance",
                )
            _resolved_report, report_relative = _repo_relative(
                item.report_path, root, label="trial report",
            )
            _resolved_journal, journal_relative = _repo_relative(
                item.journal_path, root, label="attempt journal",
            )
            receipt_trial = {
                "trial_id": trial.trial_id,
                "arm": trial.arm,
                "holdout": trial.holdout,
                "campaign_id": trial.campaign_id,
                "status": accepted_trial.status,
                "measurement_head": accepted_trial.measurement_head,
                "report_path": report_relative,
                "report_sha256": hashlib.sha256(item.report_bytes).hexdigest(),
                "attempt_journal_path": journal_relative,
                "attempt_journal_sha256": hashlib.sha256(
                    item.journal_bytes
                ).hexdigest(),
                "arm_execution": dict(item.report["arm_execution"]),
                "cross_binding_receipt_sha256": cross_binding_receipts[
                    trial.trial_id
                ]["receipt_sha256"],
            }
            descriptor_proofs.append(len(item.report.get("cells", ())) == 1)
            if "origin_terminal_projection" in item.report:
                receipt_trial["origin_terminal_projection"] = (
                    _validate_origin_terminal_projection(
                        item.report["origin_terminal_projection"],
                        gate="acceptance-trial-projection",
                    )
                )
            receipt_trials.append(receipt_trial)
        reason_codes = sorted(
            s8c_acceptance_receipt.MANDATORY_NON_CERTIFYING_REASONS
        )
        if not all(descriptor_proofs):
            reason_codes.append(
                s8c_acceptance_receipt.C02_ARM_BINDING_UNPROVEN
            )
            reason_codes.sort()
        if no_build_seen:
            reason_codes.append("no-build")
            reason_codes.sort()
        cross_binding_leaf_rows = [
            {
                "trial_id": trial["trial_id"],
                "receipt_sha256": trial["cross_binding_receipt_sha256"],
            }
            for trial in receipt_trials
        ]
        cross_binding_receipt_sha256 = (
            s8c_acceptance_receipt.cross_binding_aggregate_sha256(
                cross_binding_leaf_rows
            )
        )
        receipt_value = {
            "schema_version": s8c_acceptance_receipt.SCHEMA_VERSION,
            "manifest_path": manifest_relative,
            "manifest_sha256": manifest.sha256,
            "prereg_commit": manifest.prereg_commit,
            "prereg_content_commit": effective_binding.prereg_content_commit,
            "prereg_effective_commit": registration.prereg_effective_commit,
            "activation_report_digest_sha256": (
                effective_preregistration.report_digest_sha256
            ),
            "registry_path": registry_relative,
            "registry_blob_sha256": hashlib.sha256(
                current_registry_bytes
            ).hexdigest(),
            "registry_introduction_commit": introduction_commit,
            "lifecycle_path": lifecycle_relative,
            "lifecycle_prefix_bytes": len(lifecycle_bytes),
            "lifecycle_prefix_sha256": hashlib.sha256(
                lifecycle_bytes
            ).hexdigest(),
            "attempt_registry_path": attempt_snapshot.relative_path.as_posix(),
            "attempt_registry_prefix_bytes": len(attempt_snapshot.data),
            "attempt_registry_prefix_sha256": hashlib.sha256(
                attempt_snapshot.data
            ).hexdigest(),
            "attempt_slot_projection": attempt_slot_projection,
            "certifying": False,
            "non_certifying_reason_codes": reason_codes,
            "cross_binding_receipt_sha256": cross_binding_receipt_sha256,
            "trials": receipt_trials,
        }
        receipt_path, receipt_sha256 = _exclusive_create_acceptance_receipt(
            repository_root=root,
            manifest_sha256=manifest.sha256,
            value=receipt_value,
            publication_guard=attempt_snapshot.validate,
        )
        return AcceptanceSummary(
            manifest_sha256=manifest.sha256,
            trials=tuple(accepted),
            receipt_path=receipt_path,
            receipt_sha256=receipt_sha256,
        )
    finally:
        if attempt_snapshot is not None:
            attempt_snapshot.close()
        for item in loaded:
            item.close()


def _summary_dict(summary: AcceptanceSummary) -> dict[str, Any]:
    return {
        "check": "trial-ID completeness (registry)",
        "manifest_sha256": summary.manifest_sha256,
        "receipt_path": summary.receipt_path,
        "receipt_sha256": summary.receipt_sha256,
        "certifying": summary.certifying,
        "arm_binding": summary.arm_binding,
        "trials": [dataclasses.asdict(trial) for trial in summary.trials],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3 8c trial registry")
    subparsers = parser.add_subparsers(dest="command", required=True)
    register = subparsers.add_parser("register", help="append one manifest registration")
    register.add_argument("--manifest", required=True)
    register.add_argument("--repo-root", required=True)
    register.add_argument("--registry", required=True)
    register.add_argument("--effective-commit", required=True)
    accept = subparsers.add_parser("accept", help="verify trial-ID completeness")
    accept.add_argument("--manifest", required=True)
    accept.add_argument("--repo-root", required=True)
    accept.add_argument("--registry", required=True)
    accept.add_argument(
        "--effective-commit",
        help=(
            "exact effective binding commit; when omitted it is derived from "
            "the committed registration"
        ),
    )
    accept.add_argument("reports", nargs="+")
    genesis = subparsers.add_parser(
        "genesis", help="create the formal attempt-registry genesis"
    )
    genesis.add_argument("--manifest", required=True)
    genesis.add_argument("--repo-root", required=True)
    genesis.add_argument("--freeze-id", required=True)
    genesis.add_argument("--prereg-generation", required=True, type=int)
    genesis.add_argument("--slots-file", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "register":
            registration = append_trial_registration(
                manifest_path=Path(args.manifest),
                repository_root=Path(args.repo_root),
                registry_path=Path(args.registry),
                prereg_effective_commit=args.effective_commit,
            )
            output = {
                "manifest_sha256": registration.manifest_sha256,
                "registered_trials": len(registration.trials),
                "commit_required": True,
            }
        elif args.command == "genesis":
            manifest = load_trial_manifest(Path(args.manifest))
            slots = _decode_json(
                _read_regular_bytes(
                    Path(args.slots_file),
                    gate="attempt-registry-genesis",
                    label="slots file",
                ),
                label="slots file",
            )
            if not isinstance(slots, list):
                _fail(
                    "attempt-registry-genesis",
                    "slots file root must be an array",
                )
            attempt_registry_path = create_attempt_registry_genesis(
                repository_root=Path(args.repo_root),
                manifest_path=Path(args.manifest),
                manifest_sha256=manifest.sha256,
                freeze_id=args.freeze_id,
                prereg_generation=args.prereg_generation,
                slots=slots,
            )
            output = {
                "attempt_registry_path": attempt_registry_path.relative_to(
                    Path(args.repo_root).resolve()
                ).as_posix(),
                "manifest_sha256": manifest.sha256,
                "slot_count": len(slots),
            }
        else:
            manifest = load_trial_manifest(Path(args.manifest))
            repository_root = Path(args.repo_root)
            measurement_head = resolve_measurement_commit(repository_root)
            registrations, _registry_bytes, _registry_relative = (
                _load_committed_registry(
                    repository_root=repository_root,
                    registry_path=Path(args.registry),
                    commit_id=measurement_head,
                )
            )
            registration = _find_registration_for_manifest(
                registrations,
                manifest,
                effective_commit=args.effective_commit,
                allow_distinct_content_commit=True,
            )
            effective_commit = registration.prereg_effective_commit
            validate_preregistration_binding(
                repository_root,
                manifest_path=Path(args.manifest),
                effective_commit=effective_commit,
                measurement_commit=measurement_head,
            )
            effective = s8c_preregistration.effective_at(
                repository_root, manifest.prereg_commit,
            )
            summary = assert_trial_registry_acceptance(
                effective_preregistration=effective,
                manifest_path=Path(args.manifest),
                report_paths=[Path(path) for path in args.reports],
                repository_root=repository_root,
                registry_path=Path(args.registry),
            )
            output = _summary_dict(summary)
    except TrialRegistryError as exc:
        parser.error(str(exc))
    print(_canonical_json_bytes(output).decode("utf-8"))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
