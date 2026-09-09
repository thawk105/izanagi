# -*- coding: utf-8 -*-
"""Trusted launch seam for one 8b floor measurement attempt.

The floor campaign supplies immutable reservation inputs, the complete closed
slot set, measurement arguments, a launcher-issued probe capability, and
a terminal builder.  It never receives the sealed measurement token.  This
module alone owns that token and connects the floor path to
:mod:`s8b_attempt_registry`.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import threading
import time
from types import MappingProxyType
from typing import Any, Sequence
import weakref

from orchestrator.calibrator.perf_preflight import use_perf_from_receipt
from orchestrator.calibrator import runner as calibrator_runner

from . import s8b_attempt_registry as attempt_registry
from . import s8b_attempt_profile as profile8b
from .s8b_terminal_evidence import (
    SealedTerminalEvidenceDraft,
    TerminalEvidenceError,
    _OpenedSourceSnapshot,
    _ReservationSourceSnapshot,
    _TerminalSourceSnapshot,
    _opened_source_document,
    _reservation_source_document,
    _snapshot_opened_source,
    _snapshot_reservation_source,
    _snapshot_terminal_source,
    _terminal_source_document,
    seal_terminal_evidence,
)
from .s8b_floor_contract import _SCHEDULE_KEYS, canonical_protocol_sha256


POST_PROBE_COMPETING_REASON = "competing_process"
MEASUREMENT_LAUNCH_FAILURE_REASON = "launch_failure"
_PRE_OUTPUT_EVIDENCE_SCHEMA = "s8b-floor-pre-output-evidence/v2"

_POST_PROBE_ARGV = ("pgrep", "-af", r"ycsb_.*\.exe")
_POST_PROBE_TIMEOUT_S = 120.0
_POST_PROBE_CAPABILITY_SEAL = object()
_CLASSIFICATION_POLICY = {
    "schema": "s8b-floor-pre-output-classification/v1",
    "precedence": ["competing_process", "launch_failure"],
    "probe_argv": list(_POST_PROBE_ARGV), "probe_timeout_s": _POST_PROBE_TIMEOUT_S,
}
_CERTIFIED_MEASUREMENT_KEYWORDS = frozenset({
    "extime",
    "reps",
    "workload",
    "numactl",
    "settle_first",
    "extra_env",
    "timeout_s",
    "require_all_reps",
    "require_complete_metrics",
    "use_perf",
    "holdout_observation_admission",
    "calibration_observation_capability",
    "calibration_observation_phase",
})


class FloorAttemptLauncherError(RuntimeError):
    """The trusted launcher rejected an invalid seam result."""


FloorAttemptRegistryError = attempt_registry.S8BAttemptRegistryError


@dataclass(frozen=True, slots=True)
class FloorAttemptReservation:
    """All durable identity inputs required before measurement capture."""

    repo_root: Path
    profile: object
    binding: object
    slot_id: tuple[str, str, int, int] | tuple[str, str, int, int, int]
    protocol: Mapping[str, object]
    mode: str
    perf_preflight_receipt: Mapping[str, object] | None
    consumption_marker: object | None
    run_start_receipt_sha256: str
    process_identity: Mapping[str, Any]
    started_at: str
    admission_claim_digest: str
    attempt_id: str
    campaign_run_id: str
    manifest_sha256: str
    run_relpath: str
    cell_id: str
    schedule_row_sha256: str
    records: int
    threads: int
    workload: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class FloorAttemptRegistryGenesis:
    """The complete planned-plus-retry slot set fixed before observation."""

    slots: tuple[object, ...]


_FLOOR_ATTEMPT_REGISTRY_PLAN_SEAL = object()


@dataclass(frozen=True, slots=True, init=False)
class FloorAttemptRegistryPlan:
    """Launcher-owned registry profile, binding, genesis, and slot index."""

    _profile: object = field(repr=False)
    _binding: object = field(repr=False)
    _genesis: FloorAttemptRegistryGenesis = field(repr=False)
    _slots_by_key: Mapping[tuple[str, int, int], object] = field(repr=False)
    _seal: object = field(repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class FloorMeasurementCapture:
    """Arguments for the unit-B point-level capture primitive.

    ``keyword_arguments`` contains only optional ``capture_measure_point``
    parameters.  The four leading measurement coordinates cannot be replaced
    through it.
    """

    binary: str
    records: int
    threads: int
    clocks_per_us: int
    keyword_arguments: Mapping[str, object]


@dataclass(frozen=True, slots=True, init=False)
class FloorPostProbeCapability:
    """Launcher-issued capability for its fixed pre/post measurement probe."""

    _probe: Callable[[], Mapping[str, object]] = field(
        repr=False, compare=False
    )
    _seal: object = field(repr=False, compare=False)


class FloorAttemptPreProbe:
    """One-shot launcher-issued result of the fixed pre-measurement probe.

    Only the competition bit is public.  The raw probe result, issuing probe
    capability, and consumption state remain in launcher-private storage.
    """

    __slots__ = ("__competing", "__weakref__")

    @property
    def competing(self) -> bool:
        return self.__competing


class _FloorAttemptPreProbeState:
    __slots__ = ("owner", "probe_before", "post_probe", "used")

    def __init__(
        self,
        owner: FloorAttemptPreProbe,
        *,
        probe_before: dict[str, object],
        post_probe: FloorPostProbeCapability,
    ) -> None:
        self.owner = weakref.ref(owner)
        self.probe_before = probe_before
        self.post_probe = post_probe
        self.used = False


_PRE_PROBE_STATES: weakref.WeakKeyDictionary[
    FloorAttemptPreProbe, _FloorAttemptPreProbeState
] = weakref.WeakKeyDictionary()
_PRE_PROBE_STATES_LOCK = threading.Lock()


@dataclass(frozen=True, slots=True)
class ClassificationAuthority:
    """Pinned identity for the launcher's pre-output classification policy."""

    authority_id: str
    authority_policy_sha256: str


@dataclass(frozen=True, slots=True)
class OpenedFloorAttempt:
    """Post-classification data made available to the terminal builder."""

    measurement: object | None
    failure: Mapping[str, object] | None
    probe_before: Mapping[str, object]
    probe_after: Mapping[str, object] | None
    launch_failures: tuple[object, ...]
    pre_observation_failure_reason: str | None
    external_evidence_sha256: str
    repetition_evidence: tuple[Mapping[str, object], ...]
    expected_use_perf: bool
    reps_expected: int
    measurement_started_monotonic: float
    measurement_finished_monotonic: float
    duration_s: float
    binary_sha256_at_measure: str
    capture_keyword_arguments: Mapping[str, object]
    finished_at: str


@dataclass(frozen=True, slots=True)
class FloorAttemptTerminal:
    """Terminal projection plus the actual output bytes to digest.

    ``raw_output_bytes`` must be the non-empty bytes of the output surface that
    the campaign will retain, such as its canonical session record.  The
    launcher passes those exact bytes to the registry's deferred reader; it
    never substitutes the legacy zero-output sentinel.
    """

    raw_output_bytes: bytes
    terminal_status: str
    report_sha256: str | None
    observation_sha256: str | None
    primary_value: Any
    finished_at: str
    campaign_record: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class FloorAttemptLaunchResult:
    """Completed launcher result.  No captured token is exposed."""

    opened: OpenedFloorAttempt
    terminal: FloorAttemptTerminal


@dataclass(frozen=True, slots=True)
class _LauncherDependencies:
    registry: object
    capture_measure_point: Callable[..., object]


@dataclass(frozen=True, slots=True)
class _ReservationPolicy:
    expected_use_perf: bool
    reps_expected: int
    capture_keyword_arguments: dict[str, object]
    is_v2: bool
    terminal_source_snapshot: _ReservationSourceSnapshot | None


_PRODUCTION_DEPENDENCIES = _LauncherDependencies(
    registry=attempt_registry,
    capture_measure_point=calibrator_runner.capture_measure_point,
)


class _OwnedRawOutput:
    """One-shot output holder installed as the adapter's deferred reader."""

    __slots__ = ("__raw_output",)

    def __init__(self) -> None:
        self.__raw_output: bytes | None = None

    def seal(self, raw_output: object) -> None:
        if self.__raw_output is not None:
            raise FloorAttemptLauncherError("raw output was already sealed")
        if type(raw_output) is not bytes or not raw_output:
            raise FloorAttemptLauncherError(
                "terminal builder must return non-empty raw output bytes"
            )
        self.__raw_output = raw_output

    def read(self) -> bytes:
        if self.__raw_output is None:
            raise FloorAttemptLauncherError(
                "raw output cannot be read before the classified token is opened"
            )
        return self.__raw_output


class _DurablyClassifiedMeasurement:
    """Capability issued only after durable classification returns."""

    __slots__ = ("__captured", "__classification")

    def __init__(self, captured: object | None, classification: object) -> None:
        self.__captured = captured
        self.__classification = classification

    @property
    def classification(self) -> object:
        return self.__classification

    def open(self) -> object | None:
        if self.__captured is None:
            return None
        opener = getattr(self.__captured, "open", None)
        if not callable(opener):
            raise FloorAttemptLauncherError(
                "capture_measure_point did not return an openable token"
            )
        return opener()


def _canonical_json_bytes(value: object, *, label: str) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise FloorAttemptLauncherError(
            f"{label} is not canonical JSON data"
        ) from exc


def _require_floor_attempt_registry_plan(
    value: object,
) -> FloorAttemptRegistryPlan:
    if (
        type(value) is not FloorAttemptRegistryPlan
        or getattr(value, "_seal", None) is not _FLOOR_ATTEMPT_REGISTRY_PLAN_SEAL
    ):
        raise FloorAttemptLauncherError(
            "floor attempt registry plan was not launcher-issued"
        )
    return value


def prepare_floor_attempt_registry_plan(
    *,
    protocol: Mapping[str, object],
    cells: Sequence[Mapping[str, object]],
    schedule: Sequence[Mapping[str, object]],
    freeze_sha256: str,
    protocol_sha256: str,
) -> FloorAttemptRegistryPlan:
    """Build the exact campaign slot closure behind the launcher boundary."""

    retry_slots = protocol.get("retry_slots_per_cell")
    n_sessions = protocol.get("n_sessions")
    if (
        type(retry_slots) is not int
        or retry_slots < 0
        or type(n_sessions) is not int
        or n_sessions <= 0
    ):
        raise FloorAttemptLauncherError(
            "attempt registry plan protocol budget is invalid"
        )
    cell_by_id: dict[str, Mapping[str, object]] = {}
    for cell in cells:
        if not isinstance(cell, Mapping):
            raise FloorAttemptLauncherError(
                "attempt registry plan cells are invalid or duplicate"
            )
        cell_id = cell.get("cell_id")
        if type(cell_id) is not str or cell_id in cell_by_id:
            raise FloorAttemptLauncherError(
                "attempt registry plan cells are invalid or duplicate"
            )
        cell_by_id[cell_id] = cell
    if len(cell_by_id) != len(cells):
        raise FloorAttemptLauncherError(
            "attempt registry plan cells are invalid or duplicate"
        )
    binding = profile8b.S8BAttemptBinding(
        freeze_sha256=freeze_sha256,
        protocol_sha256=protocol_sha256,
        schedule_sha256=hashlib.sha256(
            attempt_registry.core.canonical_json_bytes(list(schedule))
        ).hexdigest(),
    )
    profile = profile8b.make_s8b_v2_domain_profile(
        max_consumptions_per_budget_key=n_sessions + retry_slots,
        recovery_authority_id=attempt_registry.scheduler_accounting.AUTHORITY_ID,
        recovery_authority_policy_sha256=(
            attempt_registry.scheduler_accounting.AUTHORITY_POLICY_SHA256
        ),
    )
    slots: list[object] = []
    slots_by_key: dict[tuple[str, int, int], object] = {}
    rounds_by_cell: dict[str, set[int]] = {
        cell_id: set() for cell_id in cell_by_id
    }
    for schedule_row in schedule:
        if (
            not isinstance(schedule_row, Mapping)
            or set(schedule_row) != set(_SCHEDULE_KEYS)
        ):
            raise FloorAttemptLauncherError(
                "attempt registry plan schedule row is invalid"
            )
        cell_id = schedule_row.get("cell_id")
        round_no = schedule_row.get("round")
        if (
            type(cell_id) is not str
            or cell_id not in cell_by_id
            or type(round_no) is not int
            or round_no <= 0
            or round_no in rounds_by_cell[cell_id]
        ):
            raise FloorAttemptLauncherError(
                "attempt registry plan schedule cell/round is invalid or duplicate"
            )
        rounds_by_cell[cell_id].add(round_no)
        cell = cell_by_id[cell_id]
        schedule_row_sha256 = hashlib.sha256(
            attempt_registry.core.canonical_json_bytes(dict(schedule_row))
        ).hexdigest()
        for measurement_ordinal in range(retry_slots + 1):
            slot = profile8b.S8BV2AttemptSlot(
                freeze_holdout_key=str(cell.get("holdout_id")),
                configuration_id=str(cell.get("configuration_id")),
                repetition=round_no - 1,
                measurement_ordinal=measurement_ordinal,
                attempt_ordinal=0,
                schedule_row_sha256=schedule_row_sha256,
            )
            key = (cell_id, round_no, measurement_ordinal)
            if key in slots_by_key:
                raise FloorAttemptLauncherError(
                    "attempt registry plan slot key is duplicate"
                )
            slots.append(slot)
            slots_by_key[key] = slot
    if any(len(rounds) != n_sessions for rounds in rounds_by_cell.values()):
        raise FloorAttemptLauncherError(
            "attempt registry plan does not cover every cell and repetition"
        )
    plan = object.__new__(FloorAttemptRegistryPlan)
    object.__setattr__(plan, "_profile", profile)
    object.__setattr__(plan, "_binding", binding)
    object.__setattr__(
        plan, "_genesis", FloorAttemptRegistryGenesis(slots=tuple(slots))
    )
    object.__setattr__(
        plan, "_slots_by_key", MappingProxyType(dict(slots_by_key))
    )
    object.__setattr__(plan, "_seal", _FLOOR_ATTEMPT_REGISTRY_PLAN_SEAL)
    return plan


def floor_attempt_registry_plan_slot_ids(
    plan: FloorAttemptRegistryPlan,
) -> tuple[tuple[str, str, int, int, int], ...]:
    """Return an immutable slot-id projection for plan verification."""

    owned = _require_floor_attempt_registry_plan(plan)
    return tuple(
        owned._profile.slot_codec.slot_id(slot)
        for slot in owned._genesis.slots
    )


def floor_attempt_registry_genesis(
    plan: FloorAttemptRegistryPlan,
) -> FloorAttemptRegistryGenesis:
    """Return the immutable launcher genesis for a launcher-issued plan."""

    return _require_floor_attempt_registry_plan(plan)._genesis


def require_floor_attempt_registry_slot(
    plan: FloorAttemptRegistryPlan,
    slot_key: tuple[str, int, int],
) -> None:
    """Fail closed unless a slot belongs to the launcher-issued plan."""

    owned = _require_floor_attempt_registry_plan(plan)
    if slot_key not in owned._slots_by_key:
        raise FloorAttemptLauncherError(
            "certified floor attempt slot is absent from the registry plan"
        )


def floor_attempt_reservation(
    plan: FloorAttemptRegistryPlan,
    *,
    slot_key: tuple[str, int, int],
    repo_root: Path,
    protocol: Mapping[str, object],
    mode: str,
    perf_preflight_receipt: Mapping[str, object] | None,
    consumption_marker: object | None,
    run_start_receipt_sha256: str,
    process_identity: Mapping[str, Any],
    started_at: str,
    admission_claim_digest: str,
    attempt_id: str,
    campaign_run_id: str,
    manifest_sha256: str,
    run_relpath: str,
    cell_id: str,
    records: int,
    threads: int,
    workload: Mapping[str, object],
) -> FloorAttemptReservation:
    """Bind one campaign attempt to a slot in a launcher-issued plan."""

    owned = _require_floor_attempt_registry_plan(plan)
    slot = owned._slots_by_key.get(slot_key)
    if slot is None:
        raise FloorAttemptLauncherError(
            "certified floor attempt slot is absent from the registry plan"
        )
    return FloorAttemptReservation(
        repo_root=Path(repo_root),
        profile=owned._profile,
        binding=owned._binding,
        slot_id=owned._profile.slot_codec.slot_id(slot),
        protocol=protocol,
        mode=mode,
        perf_preflight_receipt=perf_preflight_receipt,
        consumption_marker=consumption_marker,
        run_start_receipt_sha256=run_start_receipt_sha256,
        process_identity=process_identity,
        started_at=started_at,
        admission_claim_digest=admission_claim_digest,
        attempt_id=attempt_id,
        campaign_run_id=campaign_run_id,
        manifest_sha256=manifest_sha256,
        run_relpath=run_relpath,
        cell_id=cell_id,
        schedule_row_sha256=slot.schedule_row_sha256,
        records=records,
        threads=threads,
        workload=workload,
    )


def capture_floor_attempt_registry_prefix(
    repo_root: Path,
    plan: FloorAttemptRegistryPlan,
) -> dict[str, object]:
    """Capture the live prefix for a launcher-issued campaign plan."""

    owned = _require_floor_attempt_registry_plan(plan)
    return attempt_registry.capture_attempt_registry_prefix(
        Path(repo_root), expected_binding=owned._binding
    )


def read_floor_attempt_registry(
    repo_root: Path,
    plan: FloorAttemptRegistryPlan,
) -> tuple[Mapping[str, object], ...]:
    """Read a campaign plan's registry without exposing its adapter profile."""

    owned = _require_floor_attempt_registry_plan(plan)
    return attempt_registry.read_attempt_registry(
        Path(repo_root), profile=owned._profile, binding=owned._binding
    )


def serialize_floor_session_record(record: Mapping[str, object]) -> bytes:
    """Serialize one campaign session with the owned registry profile."""

    return profile8b.serialize_session_line(record)


def canonical_floor_payload_sha256(value: object) -> str:
    """Hash canonical campaign payload bytes at the registry boundary."""

    return hashlib.sha256(
        attempt_registry.core.canonical_json_bytes(value)
    ).hexdigest()


_CLASSIFICATION_AUTHORITY = ClassificationAuthority(
    authority_id="s8b-floor-attempt-launcher/pre-output-classification/v1",
    authority_policy_sha256=hashlib.sha256(_canonical_json_bytes(_CLASSIFICATION_POLICY, label="classification policy")).hexdigest(),
)


def _post_probe(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise FloorAttemptLauncherError("post-probe result is not a mapping")
    result = dict(value)
    if set(result) != {"rc", "stdout", "stderr", "competing"}:
        raise FloorAttemptLauncherError(
            "post-probe result requires the exact four-key schema"
        )
    if (
        type(result["rc"]) is not int
        or type(result["stdout"]) is not str
        or type(result["stderr"]) is not str
        or type(result["competing"]) is not bool
    ):
        raise FloorAttemptLauncherError(
            "post-probe result has invalid exact field types"
        )
    _canonical_json_bytes(result, label="post-probe result")
    return result


def _owned_post_probe() -> Mapping[str, object]:
    """Run the launcher's fixed pre/post measurement competition probe."""
    try:
        raw = subprocess.run(
            list(_POST_PROBE_ARGV),
            capture_output=True,
            text=True,
            timeout=_POST_PROBE_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise FloorAttemptLauncherError(
            f"post-probe could not establish competition state: {exc}"
        ) from exc
    try:
        competitors = calibrator_runner.classify_competing_probe(
            raw.returncode,
            raw.stdout or "",
            raw.stderr or "",
            _POST_PROBE_ARGV,
        )
    except calibrator_runner.CompetingBenchProbeError as exc:
        raise FloorAttemptLauncherError(
            f"post-probe could not establish competition state: {exc}"
        ) from exc
    return {
        "rc": raw.returncode,
        "stdout": raw.stdout or "",
        "stderr": raw.stderr or "",
        "competing": bool(competitors),
    }


def _new_post_probe_capability(
    probe: Callable[[], Mapping[str, object]],
) -> FloorPostProbeCapability:
    capability = object.__new__(FloorPostProbeCapability)
    object.__setattr__(capability, "_probe", probe)
    object.__setattr__(capability, "_seal", _POST_PROBE_CAPABILITY_SEAL)
    return capability


def floor_post_probe_capability() -> FloorPostProbeCapability:
    """Return a capability containing only the launcher-owned fixed probe."""
    return _new_post_probe_capability(_owned_post_probe)


def _post_probe_from_capability(
    capability: FloorPostProbeCapability,
) -> dict[str, object]:
    if (
        type(capability) is not FloorPostProbeCapability
        or capability._seal is not _POST_PROBE_CAPABILITY_SEAL
        or capability._probe is not _owned_post_probe
    ):
        raise FloorAttemptLauncherError(
            "post_probe must be a launcher-issued fixed capability"
        )
    return _post_probe(capability._probe())


def _assert_owned_post_probe_capability(value: object) -> None:
    if (
        type(value) is not FloorPostProbeCapability
        or value._seal is not _POST_PROBE_CAPABILITY_SEAL
        or value._probe is not _owned_post_probe
    ):
        raise FloorAttemptLauncherError(
            "post_probe must be a launcher-issued fixed capability"
        )


def probe_floor_attempt_preconditions(
    *, post_probe: FloorPostProbeCapability,
) -> FloorAttemptPreProbe:
    """Run and seal exactly one launcher-owned pre-measurement probe."""
    _assert_owned_post_probe_capability(post_probe)
    probe_before = _post_probe(post_probe._probe())
    pre_probe = FloorAttemptPreProbe()
    object.__setattr__(
        pre_probe,
        "_FloorAttemptPreProbe__competing",
        probe_before["competing"],
    )
    state = _FloorAttemptPreProbeState(
        pre_probe,
        probe_before=probe_before,
        post_probe=post_probe,
    )
    with _PRE_PROBE_STATES_LOCK:
        _PRE_PROBE_STATES[pre_probe] = state
    return pre_probe


def read_floor_attempt_pre_probe(
    value: FloorAttemptPreProbe,
) -> Mapping[str, object]:
    """Return an immutable raw snapshot without consuming the one-shot seal."""

    if type(value) is not FloorAttemptPreProbe:
        raise FloorAttemptLauncherError(
            "pre_probe must be a launcher-issued sealed pre-probe"
        )
    with _PRE_PROBE_STATES_LOCK:
        state = _PRE_PROBE_STATES.get(value)
        if state is None or state.owner() is not value:
            raise FloorAttemptLauncherError(
                "pre_probe must be a launcher-issued sealed pre-probe"
            )
        _assert_owned_post_probe_capability(state.post_probe)
        probe_before = _post_probe(state.probe_before)
        if value.competing is not probe_before["competing"]:
            raise FloorAttemptLauncherError(
                "pre_probe differs from its launcher-issued seal"
            )
        return MappingProxyType(probe_before)


def _claim_floor_attempt_pre_probe(
    value: object,
) -> tuple[dict[str, object], FloorPostProbeCapability]:
    if type(value) is not FloorAttemptPreProbe:
        raise FloorAttemptLauncherError(
            "pre_probe must be a launcher-issued sealed pre-probe"
        )
    with _PRE_PROBE_STATES_LOCK:
        state = _PRE_PROBE_STATES.get(value)
        if state is None or state.owner() is not value:
            raise FloorAttemptLauncherError(
                "pre_probe must be a launcher-issued sealed pre-probe"
            )
        if state.used:
            raise FloorAttemptLauncherError(
                "pre_probe is one-shot and was already used"
            )
        _assert_owned_post_probe_capability(state.post_probe)
        probe_before = _post_probe(state.probe_before)
        if value.competing is not probe_before["competing"]:
            raise FloorAttemptLauncherError(
                "pre_probe differs from its launcher-issued seal"
            )
        state.used = True
        return probe_before, state.post_probe


def _post_probe_for_test(
    capability: FloorPostProbeCapability,
) -> dict[str, object]:
    if (
        type(capability) is not FloorPostProbeCapability
        or capability._seal is not _POST_PROBE_CAPABILITY_SEAL
        or not callable(capability._probe)
    ):
        raise FloorAttemptLauncherError("test post-probe capability is invalid")
    return _post_probe(capability._probe())


def _launch_failure_evidence(value: object) -> dict[str, object]:
    try:
        exception_type = value.exception_type
        error_number = value.errno
        message = value.message
    except AttributeError as exc:
        raise FloorAttemptLauncherError(
            "captured launch failure has an invalid shape"
        ) from exc
    if (
        not isinstance(exception_type, str)
        or not exception_type
        or (error_number is not None and type(error_number) is not int)
        or not isinstance(message, str)
    ):
        raise FloorAttemptLauncherError(
            "captured launch failure has invalid field values"
        )
    return {
        "exception_type": exception_type,
        "errno": error_number,
        "message": message,
    }


def _captured_launch_failures(captured: object) -> tuple[object, ...]:
    try:
        failures = captured.launch_failures
    except AttributeError as exc:
        raise FloorAttemptLauncherError(
            "capture_measure_point token has no launch_failures surface"
        ) from exc
    if type(failures) is not tuple:
        raise FloorAttemptLauncherError(
            "capture_measure_point launch_failures is not an exact tuple"
        )
    for failure in failures:
        _launch_failure_evidence(failure)
    return failures


def _failure_evidence(
    stage: str,
    failure: BaseException,
    *,
    qualify_timeout: bool = False,
) -> dict[str, object]:
    error_number = getattr(failure, "errno", None)
    if type(error_number) is not int:
        error_number = None
    exception_type = type(failure).__name__
    if qualify_timeout:
        if isinstance(failure, subprocess.TimeoutExpired):
            exception_type = "subprocess.TimeoutExpired"
        elif isinstance(failure, OSError):
            exception_type = "OSError"
        elif isinstance(failure, RuntimeError):
            exception_type = "RuntimeError"
    return {
        "stage": stage,
        "exception_type": exception_type,
        "errno": error_number,
        "message": str(failure),
    }


def _external_evidence_bytes(
    *,
    probe_before: Mapping[str, object],
    probe_after: Mapping[str, object] | None,
    launch_failures: tuple[object, ...],
    capture_failure: Mapping[str, object] | None,
) -> bytes:
    payload = {
        "schema_version": _PRE_OUTPUT_EVIDENCE_SCHEMA,
        "probe_before": _post_probe(probe_before),
        "probe_after": None if probe_after is None else _post_probe(probe_after),
        "launch_failures": [
            _launch_failure_evidence(failure)
            for failure in launch_failures
        ],
        "capture_failure": None if capture_failure is None else dict(capture_failure),
    }
    return _canonical_json_bytes(payload, label="pre-output evidence")


def _external_evidence_sha256(
    *,
    probe_before: Mapping[str, object],
    probe_after: Mapping[str, object] | None,
    launch_failures: tuple[object, ...],
    capture_failure: Mapping[str, object] | None,
) -> str:
    return hashlib.sha256(_external_evidence_bytes(
        probe_before=probe_before,
        probe_after=probe_after,
        launch_failures=launch_failures,
        capture_failure=capture_failure,
    )).hexdigest()


def _pre_observation_failure_reason(
    *,
    probe_before: Mapping[str, object],
    probe_after: Mapping[str, object] | None,
    launch_failures: tuple[object, ...],
    failure: Mapping[str, object] | None,
) -> str | None:
    if (
        probe_before["competing"] is True
        or (probe_after is not None and probe_after["competing"] is True)
    ):
        return POST_PROBE_COMPETING_REASON
    if launch_failures or (
        failure is not None and failure.get("stage") == "capture"
    ):
        return MEASUREMENT_LAUNCH_FAILURE_REASON
    return None


def _contains_callable(value: object, *, seen: set[int] | None = None) -> bool:
    if callable(value):
        return True
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return False
    seen.add(identity)
    if isinstance(value, Mapping):
        return any(
            _contains_callable(key, seen=seen)
            or _contains_callable(item, seen=seen)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_contains_callable(item, seen=seen) for item in value)
    return False


def _checked_measurement_keyword_arguments(
    request: FloorMeasurementCapture,
) -> dict[str, object]:
    if type(request) is not FloorMeasurementCapture:
        raise FloorAttemptLauncherError(
            "measurement request has an invalid type"
        )
    keyword_arguments = dict(request.keyword_arguments)
    unsupported = frozenset(keyword_arguments) - _CERTIFIED_MEASUREMENT_KEYWORDS
    if unsupported:
        raise FloorAttemptLauncherError(
            "measurement keyword arguments are outside the certified allowlist: "
            f"{sorted(unsupported)}"
        )
    if _contains_callable(keyword_arguments):
        raise FloorAttemptLauncherError(
            "measurement keyword arguments contain a callable"
        )
    return {
        key: _snapshot_keyword_argument(value)
        for key, value in keyword_arguments.items()
    }


def _snapshot_keyword_argument(value: object) -> object:
    """Detach one mutable container layer while retaining opaque identities."""
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return value


def _checked_reservation_policy(
    reservation: FloorAttemptReservation,
    measurement: FloorMeasurementCapture,
    *,
    launcher_origin_capability: object | None = None,
) -> _ReservationPolicy:
    """Validate policy before effects and retain the exact capture kwargs copy.

    The v2 schema and consumption-marker capability must appear together.
    """
    if type(reservation) is not FloorAttemptReservation:
        raise FloorAttemptLauncherError(
            "reservation request has an invalid type"
        )
    is_v2 = (
        getattr(reservation.profile, "schema", None)
        is profile8b.S8B_V2_SCHEMA_PROFILE
    )
    if is_v2 is not (reservation.consumption_marker is not None):
        raise FloorAttemptLauncherError(
            "[s8b-launcher-v2-policy] v2 schema and consumption marker differ"
        )
    if is_v2 and (
        type(reservation.slot_id) is not tuple
        or len(reservation.slot_id) != 5
        or type(reservation.schedule_row_sha256) is not str
        or len(reservation.schedule_row_sha256) != 64
        or any(
            character not in "0123456789abcdef"
            for character in reservation.schedule_row_sha256
        )
        or type(reservation.records) is not int
        or reservation.records <= 0
        or type(reservation.threads) is not int
        or reservation.threads <= 0
        or not isinstance(reservation.workload, Mapping)
        or callable(reservation.workload)
    ):
        raise FloorAttemptLauncherError(
            "v2 reservation durable identity is invalid"
        )
    if (
        callable(reservation.protocol)
        or callable(reservation.perf_preflight_receipt)
        or (
            not is_v2
            and (
                _contains_callable(reservation.protocol)
                or _contains_callable(reservation.perf_preflight_receipt)
            )
        )
    ):
        raise FloorAttemptLauncherError(
            "reservation policy contains a callable"
        )
    terminal_source_snapshot: _ReservationSourceSnapshot | None = None
    if is_v2:
        try:
            terminal_source_snapshot = _snapshot_reservation_source(
                reservation,
                launcher_origin_capability=launcher_origin_capability,
            )
            reservation_source = _reservation_source_document(
                terminal_source_snapshot)
        except TerminalEvidenceError as exc:
            raise FloorAttemptLauncherError(
                "reservation policy is not canonical evidence data"
            ) from exc
        protocol = reservation_source["protocol"]
        perf_preflight_receipt = reservation_source[
            "perf_preflight_receipt"
        ]
        workload = reservation_source["workload"]
    else:
        protocol = reservation.protocol
        perf_preflight_receipt = reservation.perf_preflight_receipt
        workload = reservation.workload
    if not isinstance(protocol, Mapping):
        raise FloorAttemptLauncherError("reservation protocol is not a mapping")
    if type(reservation.mode) is not str or reservation.mode not in {"pilot", "official"}:
        raise FloorAttemptLauncherError(
            "reservation mode must be pilot or official"
        )
    if is_v2:
        if (
            measurement.records != reservation.records
            or measurement.threads != reservation.threads
            or _canonical_json_bytes(
                measurement.keyword_arguments.get("workload"),
                label="capture workload",
            )
            != _canonical_json_bytes(
                workload, label="reservation workload",
            )
        ):
            raise FloorAttemptLauncherError(
                "v2 capture coordinates differ from durable identity"
            )
    if (
        perf_preflight_receipt is not None and
        not isinstance(perf_preflight_receipt, Mapping)
    ):
        raise FloorAttemptLauncherError(
            "perf preflight receipt is not a mapping"
        )
    try:
        bound_protocol_sha256 = reservation.binding.protocol_sha256
        actual_protocol_sha256 = canonical_protocol_sha256(protocol)
    except (AttributeError, TypeError, ValueError, RuntimeError) as exc:
        raise FloorAttemptLauncherError(
            "reservation protocol binding is invalid"
        ) from exc
    if actual_protocol_sha256 != bound_protocol_sha256:
        raise FloorAttemptLauncherError(
            "reservation protocol is not bound to binding.protocol_sha256"
        )
    reps_expected = protocol.get("reps")
    if type(reps_expected) is not int or reps_expected <= 0:
        raise FloorAttemptLauncherError(
            "reservation protocol.reps is not a positive exact integer"
        )
    try:
        expected_use_perf = use_perf_from_receipt(
            perf_preflight_receipt
        )
    except (TypeError, ValueError) as exc:
        raise FloorAttemptLauncherError(
            "perf preflight receipt is invalid"
        ) from exc
    if (
        reservation.mode == "official" and
        reservation.perf_preflight_receipt is not None and expected_use_perf
    ):
        raise FloorAttemptLauncherError(
            "official mode cannot use an available perf preflight receipt"
        )
    keyword_arguments = _checked_measurement_keyword_arguments(measurement)
    capture_use_perf = keyword_arguments.get("use_perf", True)
    if (
        type(capture_use_perf) is not bool
        or capture_use_perf is not expected_use_perf
    ):
        raise FloorAttemptLauncherError(
            "capture use_perf differs from the perf preflight receipt"
        )
    capture_reps = keyword_arguments.get("reps", 5)
    if type(capture_reps) is not int or capture_reps != reps_expected:
        raise FloorAttemptLauncherError(
            "capture reps differs from reservation protocol.reps"
        )
    return _ReservationPolicy(
        expected_use_perf=expected_use_perf,
        reps_expected=reps_expected,
        capture_keyword_arguments=keyword_arguments,
        is_v2=is_v2,
        terminal_source_snapshot=terminal_source_snapshot,
    )


def _capture(
    request: FloorMeasurementCapture,
    *,
    keyword_arguments: dict[str, object],
    rep_observations: list[dict[str, object]],
    dependencies: _LauncherDependencies,
) -> object:
    keyword_arguments["rep_observations"] = rep_observations
    return dependencies.capture_measure_point(
        request.binary,
        request.records,
        request.threads,
        request.clocks_per_us,
        **keyword_arguments,
    )


def _reserve(
    request: FloorAttemptReservation,
    *,
    output: _OwnedRawOutput,
    dependencies: _LauncherDependencies,
    launcher_origin_capability: object | None = None,
) -> object:
    if type(request) is not FloorAttemptReservation:
        raise FloorAttemptLauncherError(
            "reservation request has an invalid type"
        )
    keyword_arguments: dict[str, object] = {
        "profile": request.profile,
        "binding": request.binding,
        "slot_id": request.slot_id,
        "run_start_receipt_sha256": request.run_start_receipt_sha256,
        "process_identity": request.process_identity,
        "started_at": request.started_at,
        "admission_claim_digest": request.admission_claim_digest,
        "attempt_id": request.attempt_id,
        "campaign_run_id": request.campaign_run_id,
        "manifest_sha256": request.manifest_sha256,
        "run_relpath": request.run_relpath,
        "cell_id": request.cell_id,
        "deferred_output_reader": output.read,
        "launcher_origin_capability": launcher_origin_capability,
        "consumption_marker": request.consumption_marker,
    }
    return dependencies.registry.reserve_attempt_slot(
        request.repo_root,
        **keyword_arguments,
    )


def _ensure_registry_genesis(
    request: FloorAttemptReservation,
    genesis: FloorAttemptRegistryGenesis,
    *,
    dependencies: _LauncherDependencies,
) -> None:
    """Create once or replay all bytes and verify the closed genesis identity."""
    if type(genesis) is not FloorAttemptRegistryGenesis:
        raise FloorAttemptLauncherError("registry genesis has an invalid type")
    if type(genesis.slots) is not tuple or not genesis.slots:
        raise FloorAttemptLauncherError(
            "registry genesis requires a non-empty exact slot tuple"
        )
    try:
        expected_slots = [
            request.profile.slot_codec.to_json(slot)
            for slot in genesis.slots
        ]
        slot_ids = tuple(
            request.profile.slot_codec.slot_id(slot)
            for slot in genesis.slots
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise FloorAttemptLauncherError(
            "registry genesis slots do not match the reservation profile"
        ) from exc
    if request.slot_id not in slot_ids:
        raise FloorAttemptLauncherError(
            "reservation slot is absent from the closed registry genesis"
        )
    if getattr(request.profile, "schema", None) is profile8b.S8B_V2_SCHEMA_PROFILE:
        selected = [
            slot for slot in genesis.slots
            if request.profile.slot_codec.slot_id(slot) == request.slot_id
        ]
        if (
            len(selected) != 1
            or getattr(selected[0], "schedule_row_sha256", None)
            != request.schedule_row_sha256
        ):
            raise FloorAttemptLauncherError(
                "v2 reservation schedule row differs from closed genesis"
            )

    registry = dependencies.registry
    try:
        registry.create_attempt_registry(
            request.repo_root,
            profile=request.profile,
            slots=genesis.slots,
            binding=request.binding,
        )
    except registry.S8BAttemptRegistryError:
        # An existing create-only target is the expected resume path.  The
        # authoritative reader below still rejects malformed or mismatched
        # bytes, slots, and binding.
        pass
    rows = registry.read_attempt_registry(
        request.repo_root,
        profile=request.profile,
        binding=request.binding,
    )
    if (
        not isinstance(rows, tuple)
        or not rows
        or not isinstance(rows[0], Mapping)
        or rows[0].get("event") != "freeze"
        or rows[0].get("slots") != expected_slots
    ):
        raise FloorAttemptLauncherError(
            "existing registry genesis differs from the complete slot set"
        )


def _begin_observation(
    classification: object,
    *,
    dependencies: _LauncherDependencies,
) -> object:
    registry = dependencies.registry
    if type(classification) is registry.ClassifiedAttempt:
        return registry.begin_attempt_observation(classification)
    if type(classification) is registry.ClassifiedFailure:
        return registry.begin_classified_failure_observation(classification)
    raise FloorAttemptLauncherError(
        "classification did not return an exact durable phase handle"
    )


def _binary_sha256_at_measure(path_value: str) -> str:
    path = Path(path_value)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise FloorAttemptLauncherError("O_NOFOLLOW is unavailable")
    try:
        before = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(before.st_mode):
            raise FloorAttemptLauncherError(
                "measurement binary is not a no-follow regular file"
            )
        fd = os.open(path, os.O_RDONLY | nofollow)
    except FloorAttemptLauncherError:
        raise
    except OSError as exc:
        raise FloorAttemptLauncherError(
            "measurement binary cannot be opened for hashing"
        ) from exc
    digest = hashlib.sha256()
    try:
        opened = os.fstat(fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_dev != before.st_dev
            or opened.st_ino != before.st_ino
        ):
            raise FloorAttemptLauncherError(
                "measurement binary changed while opening"
            )
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        os.close(fd)
    return digest.hexdigest()


def _assert_v2_terminal_launcher_facts(
    terminal: FloorAttemptTerminal | _TerminalSourceSnapshot,
    *,
    duration_s: float,
    finished_at: str,
    binary_sha256_at_measure: str,
) -> None:
    if type(terminal) is _TerminalSourceSnapshot:
        try:
            terminal_source, record, _raw_output = _terminal_source_document(
                terminal)
        except TerminalEvidenceError as exc:
            raise FloorAttemptLauncherError(
                "[s8b-launcher-terminal] campaign record cannot be snapshotted"
            ) from exc
        terminal_finished_at = terminal_source["finished_at"]
    else:
        record = terminal.campaign_record
        if not isinstance(record, Mapping):
            raise FloorAttemptLauncherError(
                "[s8b-launcher-terminal] campaign record is not a mapping"
            )
        terminal_finished_at = terminal.finished_at
    expected = {
        "duration_s": duration_s,
        "binary_sha256_at_measure": binary_sha256_at_measure,
    }
    for field_name, expected_value in expected.items():
        if record.get(field_name) != expected_value:
            raise FloorAttemptLauncherError(
                "[s8b-launcher-terminal] campaign record differs from "
                f"launcher fact: {field_name}"
            )
    if terminal_finished_at != finished_at:
        raise FloorAttemptLauncherError(
            "[s8b-launcher-terminal] finished_at differs from launcher clock"
        )


def _launch_floor_attempt(
    reservation: FloorAttemptReservation,
    registry_genesis: FloorAttemptRegistryGenesis,
    measurement: FloorMeasurementCapture,
    *,
    post_probe_capability: FloorPostProbeCapability,
    post_probe_reader: Callable[
        [FloorPostProbeCapability], dict[str, object]
    ],
    classification_authority: ClassificationAuthority,
    classified_at: Callable[[], str],
    terminal_builder: Callable[[OpenedFloorAttempt], FloorAttemptTerminal],
    dependencies: _LauncherDependencies,
    sealed_terminal_recorder: Callable[
        [object, SealedTerminalEvidenceDraft], None
    ] | None,
    launcher_origin_capability: object | None,
    pre_probe_result: Mapping[str, object] | None = None,
) -> FloorAttemptLaunchResult:
    """Reserve, probe, capture, classify, open, observe, and terminalize.

    ``capture_measure_point`` is invoked only inside this function.  Its token
    remains owned here, is wrapped in a private capability only after
    ``classify_attempt`` returns, and is never returned or passed to the
    campaign.  The probe reason precedence is competing process, launch
    failure, then no pre-output reason.
    """

    if type(classification_authority) is not ClassificationAuthority:
        raise FloorAttemptLauncherError(
            "classification authority has an invalid type"
        )
    if not callable(classified_at):
        raise FloorAttemptLauncherError("classified_at is not callable")
    if not callable(terminal_builder):
        raise FloorAttemptLauncherError("terminal_builder is not callable")
    policy = _checked_reservation_policy(
        reservation,
        measurement,
        launcher_origin_capability=launcher_origin_capability,
    )

    output = _OwnedRawOutput()
    _ensure_registry_genesis(
        reservation, registry_genesis, dependencies=dependencies,
    )
    reserved = _reserve(
        reservation,
        output=output,
        dependencies=dependencies,
        launcher_origin_capability=launcher_origin_capability,
    )
    measurement_started_monotonic = time.monotonic()
    binary_sha256_at_measure = (
        _binary_sha256_at_measure(measurement.binary)
        if policy.is_v2 else ""
    )
    capture_keyword_arguments = dict(policy.capture_keyword_arguments)
    probe_before = (
        post_probe_reader(post_probe_capability)
        if pre_probe_result is None
        else _post_probe(pre_probe_result)
    )
    probe_after: Mapping[str, object] | None = None
    captured: object | None = None
    failure: Mapping[str, object] | None = None
    launch_failures: tuple[object, ...] = ()
    private_rep_sink: list[dict[str, object]] = []
    capture_executed = False
    if probe_before["competing"] is not True:
        capture_executed = True
        try:
            captured = _capture(
                measurement,
                keyword_arguments=policy.capture_keyword_arguments,
                rep_observations=private_rep_sink,
                dependencies=dependencies,
            )
        except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
            failure = _failure_evidence(
                "capture", exc, qualify_timeout=policy.is_v2,
            )
        finally:
            probe_after = post_probe_reader(post_probe_capability)
        if captured is not None:
            launch_failures = _captured_launch_failures(captured)
    reason = _pre_observation_failure_reason(
        probe_before=probe_before,
        probe_after=probe_after,
        launch_failures=launch_failures,
        failure=failure,
    )
    evidence_bytes = _external_evidence_bytes(
        probe_before=probe_before,
        probe_after=probe_after,
        launch_failures=launch_failures,
        capture_failure=failure,
    )
    evidence_sha256 = hashlib.sha256(evidence_bytes).hexdigest()
    registry = dependencies.registry
    classification_extra: dict[str, object] = {}
    if policy.is_v2:
        classification_extra["external_evidence_bytes"] = evidence_bytes
    classification = registry.classify_attempt(
        reserved,
        pre_observation_failure_reason=reason,
        authority_id=classification_authority.authority_id,
        authority_policy_sha256=(
            classification_authority.authority_policy_sha256
        ),
        external_evidence_sha256=evidence_sha256,
        classified_at=classified_at(),
        **classification_extra,
    )
    durable = _DurablyClassifiedMeasurement(captured, classification)
    del captured

    opened_measurement: object | None = None
    if failure is None:
        try:
            opened_measurement = durable.open()
        except Exception as exc:
            if policy.is_v2 and not isinstance(
                exc,
                (subprocess.TimeoutExpired, OSError, RuntimeError),
            ):
                raise
            failure = _failure_evidence(
                "open", exc, qualify_timeout=policy.is_v2,
            )
    if policy.is_v2 and capture_executed and failure is None and (
        getattr(opened_measurement, "records", None) != reservation.records
        or getattr(opened_measurement, "threads", None) != reservation.threads
    ):
        raise FloorAttemptLauncherError(
            "v2 opened ScalePoint coordinates differ from durable identity"
        )
    repetition_evidence: tuple[Mapping[str, object], ...] = ()
    if failure is None:
        repetition_evidence = tuple(dict(item) for item in private_rep_sink)
    measurement_finished_monotonic = time.monotonic()
    duration_s = float(
        measurement_finished_monotonic - measurement_started_monotonic
    )
    terminal_finished_at = classified_at() if policy.is_v2 else ""
    opened = OpenedFloorAttempt(
        measurement=opened_measurement,
        failure=failure,
        probe_before=probe_before,
        probe_after=probe_after,
        launch_failures=launch_failures,
        pre_observation_failure_reason=reason,
        external_evidence_sha256=evidence_sha256,
        repetition_evidence=repetition_evidence,
        expected_use_perf=policy.expected_use_perf,
        reps_expected=policy.reps_expected,
        measurement_started_monotonic=measurement_started_monotonic,
        measurement_finished_monotonic=measurement_finished_monotonic,
        duration_s=duration_s,
        binary_sha256_at_measure=binary_sha256_at_measure,
        capture_keyword_arguments=capture_keyword_arguments,
        finished_at=terminal_finished_at,
    )
    opened_snapshot: _OpenedSourceSnapshot | None = None
    if policy.is_v2:
        assert policy.terminal_source_snapshot is not None
        try:
            opened_snapshot = _snapshot_opened_source(
                policy.terminal_source_snapshot, opened,
            )
            opened_source = _opened_source_document(opened_snapshot)
        except TerminalEvidenceError as exc:
            raise FloorAttemptLauncherError(
                "[s8b-launcher-terminal] opened facts cannot be snapshotted"
            ) from exc
        builder_opened = OpenedFloorAttempt(
            measurement=opened_measurement,
            failure=opened_source["failure"],
            probe_before=opened_source["probe_before"],
            probe_after=opened_source["probe_after"],
            launch_failures=tuple(opened_source["launch_failures"]),
            pre_observation_failure_reason=opened_source[
                "pre_observation_failure_reason"
            ],
            external_evidence_sha256=opened_source[
                "external_evidence_sha256"
            ],
            repetition_evidence=tuple(opened_source["repetition_evidence"]),
            expected_use_perf=policy.expected_use_perf,
            reps_expected=policy.reps_expected,
            measurement_started_monotonic=measurement_started_monotonic,
            measurement_finished_monotonic=measurement_finished_monotonic,
            duration_s=duration_s,
            binary_sha256_at_measure=binary_sha256_at_measure,
            capture_keyword_arguments=dict(capture_keyword_arguments),
            finished_at=terminal_finished_at,
        )
    else:
        builder_opened = opened
    terminal = terminal_builder(builder_opened)
    if type(terminal) is not FloorAttemptTerminal:
        raise FloorAttemptLauncherError(
            "terminal_builder returned an invalid type"
        )
    if failure is not None and terminal.terminal_status == "observed":
        raise FloorAttemptLauncherError(
            "[s8b-launcher-terminal] observed terminal contradicts a capture "
            "or open failure"
        )
    sealed_draft: SealedTerminalEvidenceDraft | None = None
    if policy.is_v2:
        assert opened_snapshot is not None
        try:
            terminal_snapshot = _snapshot_terminal_source(terminal)
        except TerminalEvidenceError as exc:
            raise FloorAttemptLauncherError(
                "[s8b-launcher-terminal] terminal facts cannot be snapshotted"
            ) from exc
        _assert_v2_terminal_launcher_facts(
            terminal_snapshot,
            duration_s=duration_s,
            finished_at=terminal_finished_at,
            binary_sha256_at_measure=binary_sha256_at_measure,
        )
        sealed_draft = seal_terminal_evidence(
            reservation, opened_snapshot, terminal_snapshot,
        )
        _terminal_source, _record, sealed_raw_output = (
            _terminal_source_document(terminal_snapshot)
        )
        output.seal(sealed_raw_output)
    else:
        output.seal(terminal.raw_output_bytes)
    observation = _begin_observation(
        durable.classification, dependencies=dependencies,
    )
    if sealed_draft is not None:
        if sealed_terminal_recorder is None:
            raise FloorAttemptLauncherError(
                "[s8b-launcher-v2-terminal] registry cannot issue sealed evidence"
            )
        sealed_terminal_recorder(observation, sealed_draft)
    else:
        registry.record_attempt_terminal(
            observation,
            terminal_status=terminal.terminal_status,
            report_sha256=terminal.report_sha256,
            observation_sha256=terminal.observation_sha256,
            primary_value=terminal.primary_value,
            finished_at=terminal.finished_at,
        )
    return FloorAttemptLaunchResult(opened=builder_opened, terminal=terminal)


def launch_floor_attempt(
    reservation: FloorAttemptReservation,
    registry_genesis: FloorAttemptRegistryGenesis,
    measurement: FloorMeasurementCapture,
    *,
    post_probe: FloorPostProbeCapability,
    classified_at: Callable[[], str],
    terminal_builder: Callable[[OpenedFloorAttempt], FloorAttemptTerminal],
) -> FloorAttemptLaunchResult:
    """Certified launcher surface with no caller-provided result callback."""
    _assert_owned_post_probe_capability(post_probe)
    launcher_origin_capability = (
        attempt_registry._new_launcher_origin_capability()
    )
    return _launch_floor_attempt(
        reservation,
        registry_genesis,
        measurement,
        post_probe_capability=post_probe,
        post_probe_reader=_post_probe_from_capability,
        classification_authority=_CLASSIFICATION_AUTHORITY,
        classified_at=classified_at,
        terminal_builder=terminal_builder,
        dependencies=_PRODUCTION_DEPENDENCIES,
        sealed_terminal_recorder=attempt_registry.record_sealed_attempt_terminal,
        launcher_origin_capability=launcher_origin_capability,
    )


def launch_probed_floor_attempt(
    reservation: FloorAttemptReservation,
    registry_genesis: FloorAttemptRegistryGenesis,
    measurement: FloorMeasurementCapture,
    *,
    pre_probe: FloorAttemptPreProbe,
    classified_at: Callable[[], str],
    terminal_builder: Callable[[OpenedFloorAttempt], FloorAttemptTerminal],
) -> FloorAttemptLaunchResult:
    """Certified launcher using one previously sealed fixed pre-probe."""
    probe_before, post_probe = _claim_floor_attempt_pre_probe(pre_probe)
    launcher_origin_capability = (
        attempt_registry._new_launcher_origin_capability()
    )
    return _launch_floor_attempt(
        reservation,
        registry_genesis,
        measurement,
        post_probe_capability=post_probe,
        post_probe_reader=_post_probe_from_capability,
        classification_authority=_CLASSIFICATION_AUTHORITY,
        classified_at=classified_at,
        terminal_builder=terminal_builder,
        dependencies=_PRODUCTION_DEPENDENCIES,
        sealed_terminal_recorder=attempt_registry.record_sealed_attempt_terminal,
        launcher_origin_capability=launcher_origin_capability,
        pre_probe_result=probe_before,
    )


def _launch_floor_attempt_for_test(
    reservation: FloorAttemptReservation,
    registry_genesis: FloorAttemptRegistryGenesis,
    measurement: FloorMeasurementCapture,
    *,
    post_probe: Callable[[], Mapping[str, object]],
    classified_at: Callable[[], str],
    terminal_builder: Callable[[OpenedFloorAttempt], FloorAttemptTerminal],
    registry: object,
    capture_measure_point: Callable[..., object],
    classification_authority: ClassificationAuthority = (
        _CLASSIFICATION_AUTHORITY
    ),
) -> FloorAttemptLaunchResult:
    """Test-only dependency injection, separate from the certified API."""
    if not callable(post_probe) or not callable(capture_measure_point):
        raise FloorAttemptLauncherError("test dependency is not callable")

    def record_sealed_for_test(
        observation: object,
        evidence: SealedTerminalEvidenceDraft,
    ) -> None:
        recorder = getattr(registry, "record_sealed_attempt_terminal", None)
        if not callable(recorder):
            raise FloorAttemptLauncherError(
                "[s8b-launcher-v2-terminal] fake registry cannot issue "
                "validated evidence"
            )
        recorder(observation, evidence)

    return _launch_floor_attempt(
        reservation,
        registry_genesis,
        measurement,
        post_probe_capability=_new_post_probe_capability(post_probe),
        post_probe_reader=_post_probe_for_test,
        classification_authority=classification_authority,
        classified_at=classified_at,
        terminal_builder=terminal_builder,
        dependencies=_LauncherDependencies(
            registry=registry,
            capture_measure_point=capture_measure_point,
        ),
        sealed_terminal_recorder=record_sealed_for_test,
        launcher_origin_capability=None,
    )
