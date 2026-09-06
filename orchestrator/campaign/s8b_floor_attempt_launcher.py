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
from pathlib import Path
import subprocess
from typing import Any

from orchestrator.calibrator.perf_preflight import use_perf_from_receipt
from orchestrator.calibrator import runner as calibrator_runner

from . import s8b_attempt_registry as attempt_registry
from . import s8b_attempt_profile as profile8b
from .s8b_floor_contract import canonical_protocol_sha256


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
    """Launcher-issued capability for its fixed pre/post measurement probe."""

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
    failure: Mapping[str, object] | None
    probe_before: Mapping[str, object]
    probe_after: Mapping[str, object] | None
    launch_failures: tuple[object, ...]
    pre_observation_failure_reason: str | None
    external_evidence_sha256: str
    repetition_evidence: tuple[Mapping[str, object], ...]
    expected_use_perf: bool
    reps_expected: int


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


def _failure_evidence(stage: str, failure: BaseException) -> dict[str, object]:
    error_number = getattr(failure, "errno", None)
    if type(error_number) is not int:
        error_number = None
    return {
        "stage": stage,
        "exception_type": type(failure).__name__,
        "errno": error_number,
        "message": str(failure),
    }


def _external_evidence_sha256(
    *,
    probe_before: Mapping[str, object],
    probe_after: Mapping[str, object] | None,
    launch_failures: tuple[object, ...],
    capture_failure: Mapping[str, object] | None,
) -> str:
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
    return hashlib.sha256(
        _canonical_json_bytes(payload, label="pre-output evidence")
    ).hexdigest()


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
) -> _ReservationPolicy:
    """Validate policy before effects and retain the exact capture kwargs copy.

    A non-None marker is rejected by the preceding v2 gate, so marker content
    never reaches the nested-callable inspection below.
    """
    if type(reservation) is not FloorAttemptReservation:
        raise FloorAttemptLauncherError(
            "reservation request has an invalid type"
        )
    if (
        getattr(reservation.profile, "schema", None) is profile8b.S8B_V2_SCHEMA_PROFILE
        or reservation.consumption_marker is not None
    ):
        raise FloorAttemptLauncherError(
            "[s8b-launcher-v2-terminal] v2 attempts require the sealed "
            "terminal evidence API"
        )
    if (
        _contains_callable(reservation.protocol)
        or _contains_callable(reservation.perf_preflight_receipt)
    ):
        raise FloorAttemptLauncherError(
            "reservation policy contains a callable"
        )
    if not isinstance(reservation.protocol, Mapping):
        raise FloorAttemptLauncherError("reservation protocol is not a mapping")
    if type(reservation.mode) is not str or reservation.mode not in {"pilot", "official"}:
        raise FloorAttemptLauncherError(
            "reservation mode must be pilot or official"
        )
    if (
        reservation.perf_preflight_receipt is not None and
        not isinstance(reservation.perf_preflight_receipt, Mapping)
    ):
        raise FloorAttemptLauncherError(
            "perf preflight receipt is not a mapping"
        )
    try:
        bound_protocol_sha256 = reservation.binding.protocol_sha256
        actual_protocol_sha256 = canonical_protocol_sha256(reservation.protocol)
    except (AttributeError, TypeError, ValueError, RuntimeError) as exc:
        raise FloorAttemptLauncherError(
            "reservation protocol binding is invalid"
        ) from exc
    if actual_protocol_sha256 != bound_protocol_sha256:
        raise FloorAttemptLauncherError(
            "reservation protocol is not bound to binding.protocol_sha256"
        )
    reps_expected = reservation.protocol.get("reps")
    if type(reps_expected) is not int or reps_expected <= 0:
        raise FloorAttemptLauncherError(
            "reservation protocol.reps is not a positive exact integer"
        )
    try:
        expected_use_perf = use_perf_from_receipt(
            reservation.perf_preflight_receipt
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
        consumption_marker=request.consumption_marker,
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
    policy = _checked_reservation_policy(reservation, measurement)

    output = _OwnedRawOutput()
    _ensure_registry_genesis(
        reservation, registry_genesis, dependencies=dependencies,
    )
    reserved = _reserve(
        reservation, output=output, dependencies=dependencies,
    )
    probe_before = post_probe_reader(post_probe_capability)
    probe_after: Mapping[str, object] | None = None
    captured: object | None = None
    failure: Mapping[str, object] | None = None
    launch_failures: tuple[object, ...] = ()
    private_rep_sink: list[dict[str, object]] = []
    if probe_before["competing"] is not True:
        try:
            captured = _capture(
                measurement,
                keyword_arguments=policy.capture_keyword_arguments,
                rep_observations=private_rep_sink,
                dependencies=dependencies,
            )
        except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
            failure = _failure_evidence("capture", exc)
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
    evidence_sha256 = _external_evidence_sha256(
        probe_before=probe_before,
        probe_after=probe_after,
        launch_failures=launch_failures,
        capture_failure=failure,
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
    if failure is None:
        try:
            opened_measurement = durable.open()
        except Exception as exc:  # output-derived failures still terminalize
            failure = _failure_evidence("open", exc)
    repetition_evidence: tuple[Mapping[str, object], ...] = ()
    if failure is None:
        repetition_evidence = tuple(dict(item) for item in private_rep_sink)
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
    )
    terminal = terminal_builder(opened)
    if type(terminal) is not FloorAttemptTerminal:
        raise FloorAttemptLauncherError(
            "terminal_builder returned an invalid type"
        )
    if opened.failure is not None and terminal.terminal_status == "observed":
        raise FloorAttemptLauncherError(
            "[s8b-launcher-terminal] observed terminal contradicts a capture "
            "or open failure"
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
        classification_authority=_CLASSIFICATION_AUTHORITY,
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
