# -*- coding: utf-8 -*-
"""Trusted launch seam for one 8b floor measurement attempt.

The floor campaign supplies immutable reservation inputs, the complete closed
slot set, measurement arguments, a launcher-issued post-probe capability, and
a terminal builder.  It never receives the sealed measurement token.  This
module alone owns that token and connects the floor path to
:mod:`s8b_attempt_registry`.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from orchestrator.calibrator import runner as calibrator_runner

from . import s8b_attempt_registry as attempt_registry


POST_PROBE_COMPETING_REASON = "competing_process"
MEASUREMENT_LAUNCH_FAILURE_REASON = "launch_failure"
_PRE_OUTPUT_EVIDENCE_SCHEMA = "s8b-floor-pre-output-evidence/v1"

_POST_PROBE_ARGV = ("pgrep", "-af", r"ycsb_.*\.exe")
_POST_PROBE_TIMEOUT_S = 120.0
_POST_PROBE_CAPABILITY_SEAL = object()
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


@dataclass(frozen=True, slots=True)
class FloorAttemptReservation:
    """All durable identity inputs required before measurement capture."""

    repo_root: Path
    profile: object
    binding: object
    slot_id: tuple[str, str, int, int]
    run_start_receipt_sha256: str
    process_identity: Mapping[str, Any]
    started_at: str
    admission_claim_digest: str
    attempt_id: str
    campaign_run_id: str
    manifest_sha256: str
    run_relpath: str
    cell_id: str


@dataclass(frozen=True, slots=True)
class FloorAttemptRegistryGenesis:
    """The complete planned-plus-retry slot set fixed before observation."""

    slots: tuple[object, ...]


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
    """Launcher-issued capability for its fixed post-measurement probe."""

    _probe: Callable[[], Mapping[str, object]] = field(
        repr=False, compare=False
    )
    _seal: object = field(repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class ClassificationAuthority:
    """Pinned identity for the launcher's pre-output classification policy."""

    authority_id: str
    authority_policy_sha256: str


@dataclass(frozen=True, slots=True)
class OpenedFloorAttempt:
    """Post-classification data made available to the terminal builder."""

    measurement: object | None
    open_error: Exception | None
    post_probe: Mapping[str, object]
    launch_failures: tuple[object, ...]
    pre_observation_failure_reason: str | None
    external_evidence_sha256: str


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

    def __init__(self, captured: object, classification: object) -> None:
        self.__captured = captured
        self.__classification = classification

    @property
    def classification(self) -> object:
        return self.__classification

    def open(self) -> object:
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


def _post_probe(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise FloorAttemptLauncherError("post-probe result is not a mapping")
    result = dict(value)
    if type(result.get("competing")) is not bool:
        raise FloorAttemptLauncherError(
            "post-probe result requires an exact boolean competing field"
        )
    _canonical_json_bytes(result, label="post-probe result")
    return result


def _owned_post_probe() -> Mapping[str, object]:
    """Run the launcher's fixed post-measurement competition probe."""
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


def _external_evidence_sha256(
    *, post_probe: Mapping[str, object], launch_failures: tuple[object, ...],
) -> str:
    payload = {
        "schema_version": _PRE_OUTPUT_EVIDENCE_SCHEMA,
        "post_probe": dict(post_probe),
        "launch_failures": [
            _launch_failure_evidence(failure)
            for failure in launch_failures
        ],
    }
    return hashlib.sha256(
        _canonical_json_bytes(payload, label="pre-output evidence")
    ).hexdigest()


def _pre_observation_failure_reason(
    *, post_probe: Mapping[str, object], launch_failures: tuple[object, ...],
) -> str | None:
    if post_probe["competing"] is True:
        return POST_PROBE_COMPETING_REASON
    if launch_failures:
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
    return keyword_arguments


def _capture(
    request: FloorMeasurementCapture,
    *,
    dependencies: _LauncherDependencies,
) -> object:
    keyword_arguments = _checked_measurement_keyword_arguments(request)
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
) -> object:
    if type(request) is not FloorAttemptReservation:
        raise FloorAttemptLauncherError(
            "reservation request has an invalid type"
        )
    return dependencies.registry.reserve_attempt_slot(
        request.repo_root,
        profile=request.profile,
        binding=request.binding,
        slot_id=request.slot_id,
        run_start_receipt_sha256=request.run_start_receipt_sha256,
        process_identity=request.process_identity,
        started_at=request.started_at,
        admission_claim_digest=request.admission_claim_digest,
        attempt_id=request.attempt_id,
        campaign_run_id=request.campaign_run_id,
        manifest_sha256=request.manifest_sha256,
        run_relpath=request.run_relpath,
        cell_id=request.cell_id,
        deferred_output_reader=output.read,
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
) -> FloorAttemptLaunchResult:
    """Reserve, capture, seal classification, open, observe, and terminalize.

    ``capture_measure_point`` is invoked only inside this function.  Its token
    remains owned here, is wrapped in a private capability only after
    ``classify_attempt`` returns, and is never returned or passed to the
    campaign.  The post-probe reason precedence is competing process, launch
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
    # Reject unreviewed result surfaces before registry or process effects.
    _checked_measurement_keyword_arguments(measurement)

    output = _OwnedRawOutput()
    _ensure_registry_genesis(
        reservation, registry_genesis, dependencies=dependencies,
    )
    reserved = _reserve(
        reservation, output=output, dependencies=dependencies,
    )
    captured = _capture(measurement, dependencies=dependencies)
    probe_result = post_probe_reader(post_probe_capability)
    launch_failures = _captured_launch_failures(captured)
    reason = _pre_observation_failure_reason(
        post_probe=probe_result,
        launch_failures=launch_failures,
    )
    evidence_sha256 = _external_evidence_sha256(
        post_probe=probe_result,
        launch_failures=launch_failures,
    )
    registry = dependencies.registry
    classification = registry.classify_attempt(
        reserved,
        pre_observation_failure_reason=reason,
        authority_id=classification_authority.authority_id,
        authority_policy_sha256=(
            classification_authority.authority_policy_sha256
        ),
        external_evidence_sha256=evidence_sha256,
        classified_at=classified_at(),
    )
    durable = _DurablyClassifiedMeasurement(captured, classification)
    del captured

    opened_measurement: object | None = None
    open_error: Exception | None = None
    try:
        opened_measurement = durable.open()
    except Exception as exc:  # output-derived failures still terminalize
        open_error = exc
    opened = OpenedFloorAttempt(
        measurement=opened_measurement,
        open_error=open_error,
        post_probe=probe_result,
        launch_failures=launch_failures,
        pre_observation_failure_reason=reason,
        external_evidence_sha256=evidence_sha256,
    )
    terminal = terminal_builder(opened)
    if type(terminal) is not FloorAttemptTerminal:
        raise FloorAttemptLauncherError(
            "terminal_builder returned an invalid type"
        )
    output.seal(terminal.raw_output_bytes)
    observation = _begin_observation(
        durable.classification, dependencies=dependencies,
    )
    registry.record_attempt_terminal(
        observation,
        terminal_status=terminal.terminal_status,
        report_sha256=terminal.report_sha256,
        observation_sha256=terminal.observation_sha256,
        primary_value=terminal.primary_value,
        finished_at=terminal.finished_at,
    )
    return FloorAttemptLaunchResult(opened=opened, terminal=terminal)


def launch_floor_attempt(
    reservation: FloorAttemptReservation,
    registry_genesis: FloorAttemptRegistryGenesis,
    measurement: FloorMeasurementCapture,
    *,
    post_probe: FloorPostProbeCapability,
    classification_authority: ClassificationAuthority,
    classified_at: Callable[[], str],
    terminal_builder: Callable[[OpenedFloorAttempt], FloorAttemptTerminal],
) -> FloorAttemptLaunchResult:
    """Certified launcher surface with no caller-provided result callback."""
    _assert_owned_post_probe_capability(post_probe)
    return _launch_floor_attempt(
        reservation,
        registry_genesis,
        measurement,
        post_probe_capability=post_probe,
        post_probe_reader=_post_probe_from_capability,
        classification_authority=classification_authority,
        classified_at=classified_at,
        terminal_builder=terminal_builder,
        dependencies=_PRODUCTION_DEPENDENCIES,
    )


def _launch_floor_attempt_for_test(
    reservation: FloorAttemptReservation,
    registry_genesis: FloorAttemptRegistryGenesis,
    measurement: FloorMeasurementCapture,
    *,
    post_probe: Callable[[], Mapping[str, object]],
    classification_authority: ClassificationAuthority,
    classified_at: Callable[[], str],
    terminal_builder: Callable[[OpenedFloorAttempt], FloorAttemptTerminal],
    registry: object,
    capture_measure_point: Callable[..., object],
) -> FloorAttemptLaunchResult:
    """Test-only dependency injection, separate from the certified API."""
    if not callable(post_probe) or not callable(capture_measure_point):
        raise FloorAttemptLauncherError("test dependency is not callable")
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
    )
