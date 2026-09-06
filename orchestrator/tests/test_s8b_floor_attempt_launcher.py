"""Ordering and ownership tests for the trusted 8b floor attempt launcher."""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import inspect
from pathlib import Path
import subprocess
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from orchestrator.calibrator import runner as calibrator_runner  # noqa: E402
from orchestrator.calibrator import perf_preflight  # noqa: E402
from orchestrator.campaign import attempt_registry_core  # noqa: E402
from orchestrator.campaign import s8b_attempt_profile  # noqa: E402
from orchestrator.campaign import s8b_attempt_registry  # noqa: E402
from orchestrator.campaign import s8b_floor_attempt_launcher as launcher  # noqa: E402
from orchestrator.campaign import s8b_holdout_admission  # noqa: E402


@dataclass(frozen=True)
class _Reserved:
    identity: str = "reserved"


@dataclass(frozen=True)
class _ClassifiedAttempt:
    reason: str | None


@dataclass(frozen=True)
class _ClassifiedFailure:
    reason: str


@dataclass(frozen=True)
class _Observation:
    raw_output: bytes


@dataclass(frozen=True)
class _Slot:
    freeze_holdout_key: str
    configuration_id: str
    repetition: int
    attempt_ordinal: int
    schedule_row_sha256: str


class _SlotCodec:
    @staticmethod
    def slot_id(slot: _Slot) -> tuple[str, str, int, int]:
        return (
            slot.freeze_holdout_key,
            slot.configuration_id,
            slot.repetition,
            slot.attempt_ordinal,
        )

    @staticmethod
    def to_json(slot: _Slot) -> dict[str, object]:
        return {
            "freeze_holdout_key": slot.freeze_holdout_key,
            "configuration_id": slot.configuration_id,
            "repetition": slot.repetition,
            "attempt_ordinal": slot.attempt_ordinal,
            "schedule_row_sha256": slot.schedule_row_sha256,
        }


class _Profile:
    slot_codec = _SlotCodec()


@dataclass(frozen=True)
class _Binding:
    protocol_sha256: str


class _CallableDict(dict[str, object]):
    def __call__(self) -> None:
        return None


_PROFILE = _Profile()
_PROTOCOL = {"reps": 3}
_BINDING = _Binding(launcher.canonical_protocol_sha256(_PROTOCOL))
_PLANNED_SLOT = _Slot(
    "holdout-a", "configuration-a", 7, 0, "7" * 64,
)
_RETRY_SLOT = _Slot(
    "holdout-a", "configuration-a", 7, 1, "8" * 64,
)


class _RecorderRegistry:
    """Event recorder fake with no adapter/core ordering gate."""

    class S8BAttemptRegistryError(RuntimeError):
        pass

    ClassifiedAttempt = _ClassifiedAttempt
    ClassifiedFailure = _ClassifiedFailure

    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.reader = None
        self.classification_kwargs: dict[str, object] = {}
        self.terminal_kwargs: dict[str, object] = {}
        self.reservation_kwargs: dict[str, object] = {}
        self.genesis_slots: tuple[object, ...] | None = None
        self.genesis_binding: object | None = None
        self.create_calls = 0
        self.read_calls = 0

    def create_attempt_registry(
        self, _repo_root: Path, **kwargs: object,
    ) -> Path:
        self.create_calls += 1
        if self.genesis_slots is not None:
            raise self.S8BAttemptRegistryError("create-only collision")
        self.genesis_slots = tuple(kwargs["slots"])
        self.genesis_binding = kwargs["binding"]
        return Path("registry.jsonl")

    def read_attempt_registry(
        self, _repo_root: Path, **kwargs: object,
    ) -> tuple[dict[str, object], ...]:
        self.read_calls += 1
        assert kwargs["binding"] is self.genesis_binding
        assert self.genesis_slots is not None
        return ({
            "event": "freeze",
            "slots": [
                kwargs["profile"].slot_codec.to_json(slot)
                for slot in self.genesis_slots
            ],
        },)

    def reserve_attempt_slot(self, _repo_root: Path, **kwargs: object) -> _Reserved:
        self.events.append("reserve")
        self.reservation_kwargs = dict(kwargs)
        self.reader = kwargs["deferred_output_reader"]
        return _Reserved()

    def classify_attempt(
        self, _reserved: _Reserved, **kwargs: object,
    ) -> _ClassifiedAttempt | _ClassifiedFailure:
        self.events.append("classify")
        self.classification_kwargs = dict(kwargs)
        reason = kwargs["pre_observation_failure_reason"]
        if reason is None:
            return _ClassifiedAttempt(None)
        return _ClassifiedFailure(str(reason))

    def begin_attempt_observation(
        self, _classified: _ClassifiedAttempt,
    ) -> _Observation:
        self.events.append("observe-success")
        assert callable(self.reader)
        return _Observation(self.reader())

    def begin_classified_failure_observation(
        self, _failure: _ClassifiedFailure,
    ) -> _Observation:
        self.events.append("observe-failure")
        assert callable(self.reader)
        return _Observation(self.reader())

    def record_attempt_terminal(
        self, observation: _Observation, **kwargs: object,
    ) -> None:
        self.events.append("terminal")
        self.terminal_kwargs = {
            **kwargs,
            "raw_output": observation.raw_output,
        }


class _Token:
    def __init__(
        self,
        events: list[str],
        *,
        failures: tuple[object, ...] = (),
        open_error: Exception | None = None,
    ) -> None:
        self.events = events
        self.launch_failures = failures
        self.open_error = open_error
        self.opened = False
        self.throughputs = [101.0, 102.0, 103.0]
        self.notes: list[str] = []
        self.rep_observations = [{"source": "public measurement view"}]
        self._rep_sink: list[dict[str, object]] | None = None

    def open(self) -> object:
        self.events.append("open")
        self.opened = True
        assert self._rep_sink is not None
        self._rep_sink.extend(
            {
                "rep_index": rep, "returncode": 0,
                "counter_status": "available", "missing_perf_events": [],
                "perf_raw": {}, "throughput": throughput,
            }
            for rep, throughput in enumerate(self.throughputs)
        )
        if self.open_error is not None:
            raise self.open_error
        return self


def _reservation() -> launcher.FloorAttemptReservation:
    return launcher.FloorAttemptReservation(
        repo_root=Path("/tmp/launcher-recorder"),
        profile=_PROFILE,
        binding=_BINDING,
        slot_id=("holdout-a", "configuration-a", 7, 0),
        protocol=_PROTOCOL,
        mode="pilot",
        perf_preflight_receipt=None,
        consumption_marker=None,
        run_start_receipt_sha256="1" * 64,
        process_identity={
            "pid": 123,
            "starttime": "launcher-start",
            "execution_uuid": "launcher-execution",
        },
        started_at="2026-08-26T00:00:00+00:00",
        admission_claim_digest="2" * 64,
        attempt_id="holdout-a::configuration-a::attempt0",
        campaign_run_id="launcher-run",
        manifest_sha256="3" * 64,
        run_relpath="runs/launcher-run",
        cell_id="holdout-a::configuration-a",
    )


def _measurement() -> launcher.FloorMeasurementCapture:
    return launcher.FloorMeasurementCapture(
        binary="/tmp/ycsb_test.exe",
        records=1000,
        threads=4,
        clocks_per_us=2400,
        keyword_arguments={
            "extime": 3,
            "reps": 3,
            "use_perf": True,
        },
    )


def _genesis() -> launcher.FloorAttemptRegistryGenesis:
    return launcher.FloorAttemptRegistryGenesis(
        slots=(_PLANNED_SLOT, _RETRY_SLOT),
    )


def _probe(*, competing: bool = False) -> dict[str, object]:
    return {
        "rc": 0 if competing else 1,
        "stdout": "999 ycsb_other.exe\n" if competing else "",
        "stderr": "",
        "competing": competing,
    }


def _bind_sink(token: _Token, kwargs: dict[str, object]) -> None:
    assert "rep_observations" not in _measurement().keyword_arguments
    sink = kwargs["rep_observations"]
    assert type(sink) is list
    assert sink is not token.rep_observations
    token._rep_sink = sink


def _capture_token(token: _Token, *, record: bool = False):
    def capture(*_args: object, **kwargs: object) -> _Token:
        if record:  # Preserve event assertions in the older ordering nodes.
            token.events.append("capture")
        _bind_sink(token, kwargs)
        return token
    return capture


def _terminal(opened: launcher.OpenedFloorAttempt) -> launcher.FloorAttemptTerminal:
    reason = opened.pre_observation_failure_reason
    failed = reason is not None or opened.failure is not None
    return launcher.FloorAttemptTerminal(
        raw_output_bytes=b'{"event":"session"}\n',
        terminal_status="terminal-failure" if failed else "observed",
        report_sha256="4" * 64,
        observation_sha256=None if failed else "5" * 64,
        primary_value=None if failed else {"throughput": 102.0},
        finished_at="2026-08-26T00:00:02+00:00",
        campaign_record={"event": "session"},
    )


def _unavailable_receipt() -> dict[str, object]:
    return {
        "schema": perf_preflight.SCHEMA,
        "status": "unavailable",
        "available": False,
        "probe_argv": list(perf_preflight._BASE_PROBE_ARGV),
        "rc": 1,
        "parsed_events": [],
        "reason": "nonzero-rc",
        "stderr_sha256": "0" * 64,
        "candidates": [],
    }


def _available_receipt() -> dict[str, object]:
    receipt = _unavailable_receipt()
    receipt.update(
        status="available", available=True, rc=0,
        parsed_events=list(calibrator_runner.PERF_EVENTS), reason="available",
    )
    return receipt


@pytest.mark.parametrize(
    ("competing", "failures", "expected_reason", "observe_event"),
    (
        pytest.param(
            True,
            (
                calibrator_runner.MeasurementLaunchFailure(
                    "OSError", 12, "launch failed",
                ),
            ),
            launcher.POST_PROBE_COMPETING_REASON,
            "observe-failure",
            id="post-probe-precedes-launch-failure",
        ),
        pytest.param(
            False,
            (
                calibrator_runner.MeasurementLaunchFailure(
                    "FileNotFoundError", 2, "binary unavailable",
                ),
            ),
            launcher.MEASUREMENT_LAUNCH_FAILURE_REASON,
            "observe-failure",
            id="launch-failure",
        ),
        pytest.param(
            False,
            (),
            None,
            "observe-success",
            id="no-pre-output-reason",
        ),
    ),
)
def test_mut_t1668_seal_order_and_reason_precedence_use_recorder_fake(
    monkeypatch: pytest.MonkeyPatch,
    competing: bool,
    failures: tuple[object, ...],
    expected_reason: str | None,
    observe_event: str,
) -> None:
    events: list[str] = []
    fake_registry = _RecorderRegistry(events)
    token = _Token(events, failures=failures)

    def capture(*args: object, **kwargs: object) -> _Token:
        events.append("capture")
        assert args == ("/tmp/ycsb_test.exe", 1000, 4, 2400)
        assert set(kwargs) == {"extime", "reps", "use_perf", "rep_observations"}
        assert kwargs["extime"] == 3
        assert kwargs["reps"] == 3
        assert kwargs["use_perf"] is True
        assert type(kwargs["rep_observations"]) is list
        assert "rep_observations" not in _measurement().keyword_arguments
        _bind_sink(token, kwargs)
        return token

    probe_calls = 0

    def post_probe() -> dict[str, object]:
        nonlocal probe_calls
        events.append("post-probe")
        probe_calls += 1
        return _probe(competing=competing if probe_calls == 2 else False)

    raw_output = b'{"event":"session","throughputs":[101,102,103]}\n'

    def terminal_builder(
        opened: launcher.OpenedFloorAttempt,
    ) -> launcher.FloorAttemptTerminal:
        events.append("build-terminal")
        assert token.opened is True
        assert opened.pre_observation_failure_reason == expected_reason
        assert opened.measurement is not None
        return launcher.FloorAttemptTerminal(
            raw_output_bytes=raw_output,
            terminal_status=(
                "observed" if expected_reason is None else "terminal-failure"
            ),
            report_sha256="4" * 64,
            observation_sha256=("5" * 64 if expected_reason is None else None),
            primary_value=(
                {"throughput": 102.0} if expected_reason is None else None
            ),
            finished_at="2026-08-26T00:00:02+00:00",
            campaign_record={"event": "session"},
        )

    result = launcher._launch_floor_attempt_for_test(
        _reservation(),
        _genesis(),
        _measurement(),
        post_probe=post_probe,
        classification_authority=launcher.ClassificationAuthority(
            authority_id="launcher-test-authority",
            authority_policy_sha256="6" * 64,
        ),
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=terminal_builder,
        registry=fake_registry,
        capture_measure_point=capture,
    )

    assert events == [
        "reserve",
        "post-probe",
        "capture",
        "post-probe",
        "classify",
        "open",
        "build-terminal",
        observe_event,
        "terminal",
    ]
    assert events.index("classify") < events.index("open")
    assert fake_registry.classification_kwargs[
        "pre_observation_failure_reason"
    ] == expected_reason
    evidence_sha256 = fake_registry.classification_kwargs[
        "external_evidence_sha256"
    ]
    assert isinstance(evidence_sha256, str) and len(evidence_sha256) == 64
    assert fake_registry.terminal_kwargs["raw_output"] == raw_output
    assert hashlib.sha256(
        fake_registry.terminal_kwargs["raw_output"]
    ).hexdigest() != hashlib.sha256(b"").hexdigest()
    assert result.opened.measurement is not None
    assert result.terminal.raw_output_bytes == raw_output
    assert not hasattr(result, "token")
    assert fake_registry.create_calls == 1
    assert fake_registry.read_calls == 1
    assert fake_registry.genesis_slots == (_PLANNED_SLOT, _RETRY_SLOT)


def test_open_error_still_observes_and_terminalizes_after_classification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    fake_registry = _RecorderRegistry(events)
    failure = calibrator_runner.MeasurementLaunchFailure(
        "FileNotFoundError", 2, "binary unavailable",
    )
    token = _Token(
        events,
        failures=(failure,),
        open_error=RuntimeError("all reps failed"),
    )
    capture = _capture_token(token, record=True)

    def terminal_builder(
        opened: launcher.OpenedFloorAttempt,
    ) -> launcher.FloorAttemptTerminal:
        events.append("build-terminal")
        assert opened.measurement is None
        assert opened.failure == {
            "stage": "open",
            "exception_type": "RuntimeError",
            "errno": None,
            "message": "all reps failed",
        }
        return launcher.FloorAttemptTerminal(
            raw_output_bytes=b'{"event":"session","excluded_reason":"launch_failure"}\n',
            terminal_status="terminal-failure",
            report_sha256=None,
            observation_sha256=None,
            primary_value=None,
            finished_at="2026-08-26T00:00:02+00:00",
            campaign_record={"event": "session"},
        )

    result = launcher._launch_floor_attempt_for_test(
        _reservation(),
        _genesis(),
        _measurement(),
        post_probe=lambda: (events.append("post-probe") or _probe()),
        classification_authority=launcher.ClassificationAuthority(
            authority_id="launcher-test-authority",
            authority_policy_sha256="6" * 64,
        ),
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=terminal_builder,
        registry=fake_registry,
        capture_measure_point=capture,
    )

    assert events == [
        "reserve",
        "post-probe",
        "capture",
        "post-probe",
        "classify",
        "open",
        "build-terminal",
        "observe-failure",
        "terminal",
    ]
    assert result.opened.failure is not None


def test_empty_output_cannot_reach_observation_or_terminal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    fake_registry = _RecorderRegistry(events)
    token = _Token(events)
    capture = _capture_token(token, record=True)

    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match="non-empty raw output bytes",
    ):
        launcher._launch_floor_attempt_for_test(
            _reservation(),
            _genesis(),
            _measurement(),
            post_probe=lambda: (events.append("post-probe") or _probe()),
            classification_authority=launcher.ClassificationAuthority(
                authority_id="launcher-test-authority",
                authority_policy_sha256="6" * 64,
            ),
            classified_at=lambda: "2026-08-26T00:00:01+00:00",
            terminal_builder=lambda opened: launcher.FloorAttemptTerminal(
                raw_output_bytes=b"",
                terminal_status="observed",
                report_sha256="4" * 64,
                observation_sha256="5" * 64,
                primary_value={"throughput": 102.0},
                finished_at="2026-08-26T00:00:02+00:00",
                campaign_record={"event": "session"},
            ),
            registry=fake_registry,
            capture_measure_point=capture,
        )

    assert "classify" in events and "open" in events
    assert "observe-success" not in events
    assert "terminal" not in events


def test_existing_genesis_replays_all_rows_and_rejects_a_different_slot_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del monkeypatch
    events: list[str] = []
    fake_registry = _RecorderRegistry(events)
    reservation = _reservation()
    fake_registry.genesis_slots = (_PLANNED_SLOT,)
    fake_registry.genesis_binding = reservation.binding

    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match="complete slot set",
    ):
        launcher._launch_floor_attempt_for_test(
            reservation,
            _genesis(),
            _measurement(),
            post_probe=_probe,
            classification_authority=launcher.ClassificationAuthority(
                authority_id="launcher-test-authority",
                authority_policy_sha256="6" * 64,
            ),
            classified_at=lambda: "2026-08-26T00:00:01+00:00",
            terminal_builder=lambda _opened: pytest.fail(
                "terminal builder must not run"
            ),
            registry=fake_registry,
            capture_measure_point=lambda *_args, **_kwargs: pytest.fail(
                "capture must not run"
            ),
        )

    assert fake_registry.create_calls == 1
    assert fake_registry.read_calls == 1
    assert events == []


def test_real_adapter_creates_and_exactly_reuses_complete_genesis(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    subprocess.run(
        ["git", "init", "-q", str(repo)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    profile = s8b_attempt_profile.make_s8b_domain_profile(
        max_consumptions_per_budget_key=4,
        recovery_authority_id="launcher-test-recovery-authority",
        recovery_authority_policy_sha256="9" * 64,
    )
    binding = s8b_attempt_profile.S8BAttemptBinding(
        freeze_sha256="a" * 64,
        protocol_sha256="b" * 64,
        schedule_sha256="c" * 64,
    )

    def slot(ordinal: int) -> s8b_attempt_profile.S8BAttemptSlot:
        identity = {
            "freeze_holdout_key": "holdout-a",
            "configuration_id": "configuration-a",
            "repetition": 7,
            "attempt_ordinal": ordinal,
        }
        return s8b_attempt_profile.S8BAttemptSlot(
            **identity,
            schedule_row_sha256=hashlib.sha256(
                attempt_registry_core.canonical_json_bytes(identity)
            ).hexdigest(),
        )

    planned, retry = slot(0), slot(1)
    protocol = {"reps": 3}
    reservation = launcher.FloorAttemptReservation(
        repo_root=repo,
        profile=profile,
        binding=s8b_attempt_profile.S8BAttemptBinding(
            freeze_sha256=binding.freeze_sha256,
            protocol_sha256=launcher.canonical_protocol_sha256(protocol),
            schedule_sha256=binding.schedule_sha256,
        ),
        slot_id=profile.slot_codec.slot_id(planned),
        protocol=protocol,
        mode="pilot",
        perf_preflight_receipt=None,
        consumption_marker=None,
        run_start_receipt_sha256="d" * 64,
        process_identity={
            "pid": 123,
            "starttime": "launcher-start",
            "execution_uuid": "launcher-execution",
        },
        started_at="2026-08-26T00:00:00+00:00",
        admission_claim_digest="e" * 64,
        attempt_id="holdout-a::configuration-a::attempt0",
        campaign_run_id="launcher-run",
        manifest_sha256="f" * 64,
        run_relpath="runs/launcher-run",
        cell_id="holdout-a::configuration-a",
    )
    complete = launcher.FloorAttemptRegistryGenesis(
        slots=(planned, retry),
    )

    launcher._ensure_registry_genesis(
        reservation,
        complete,
        dependencies=launcher._PRODUCTION_DEPENDENCIES,
    )
    consumed = s8b_holdout_admission.shared_admission_root(repo) / "consumed"
    consumed.mkdir(parents=True, exist_ok=True)
    marker_digest = hashlib.sha256(reservation.attempt_id.encode()).hexdigest()
    marker = {
        "schema_version": "s8b-holdout-attempt-consumption/v1", "event": "consume",
        "claim_digest": reservation.admission_claim_digest, "attempt_id": reservation.attempt_id,
        "campaign_run_id": reservation.campaign_run_id, "manifest_sha256": reservation.manifest_sha256,
        "run_relpath": reservation.run_relpath, "cell_id": reservation.cell_id,
        "freeze_holdout_key": planned.freeze_holdout_key, "configuration_id": planned.configuration_id,
        "observation_role": s8b_holdout_admission.OBSERVATION_ROLE_FLOOR_CAMPAIGN,
    }
    marker_name = f"{reservation.admission_claim_digest}-{marker_digest}.json"
    (consumed / marker_name).write_bytes(attempt_registry_core.canonical_json_bytes(marker) + b"\n")
    token = _Token([])
    launcher._launch_floor_attempt_for_test(
        reservation, complete, _measurement(), post_probe=_probe,
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=_terminal, registry=s8b_attempt_registry,
        capture_measure_point=_capture_token(token),
    )
    rows = s8b_attempt_registry.read_attempt_registry(
        repo,
        profile=profile,
        binding=reservation.binding,
    )
    assert rows[0]["slots"] == [
        profile.slot_codec.to_json(planned),
        profile.slot_codec.to_json(retry),
    ]
    assert [row["event"] for row in rows] == [
        "freeze", "start", "pre-observation-seal", "classification",
        "observation-start", "terminal",
    ]

    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match="complete slot set",
    ):
        launcher._ensure_registry_genesis(
            reservation,
            launcher.FloorAttemptRegistryGenesis(slots=(planned,)),
            dependencies=launcher._PRODUCTION_DEPENDENCIES,
        )


@pytest.mark.parametrize(
    "keyword_arguments",
    (
        {"subprocess_runner": lambda *_args, **_kwargs: None},
        {"extime": 3, "workload": {"leak": lambda: 1}},
        {"rep_returncodes": []},
        {"rep_observations": []},
    ),
)
def test_certified_measurement_keywords_reject_result_leak_surfaces(
    keyword_arguments: dict[str, object],
) -> None:
    events: list[str] = []
    fake_registry = _RecorderRegistry(events)
    request = launcher.FloorMeasurementCapture(
        binary="/tmp/ycsb_test.exe",
        records=1000,
        threads=4,
        clocks_per_us=2400,
        keyword_arguments=keyword_arguments,
    )

    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match="allowlist|contain a callable",
    ):
        launcher._launch_floor_attempt_for_test(
            _reservation(),
            _genesis(),
            request,
            post_probe=lambda: {"competing": False},
            classification_authority=launcher.ClassificationAuthority(
                authority_id="launcher-test-authority",
                authority_policy_sha256="6" * 64,
            ),
            classified_at=lambda: "2026-08-26T00:00:01+00:00",
            terminal_builder=lambda _opened: pytest.fail(
                "terminal builder must not run"
            ),
            registry=fake_registry,
            capture_measure_point=lambda *_args, **_kwargs: pytest.fail(
                "capture dependency must not run"
            ),
        )

    assert events == []


def test_pre_probe_competition_terminalizes_without_capture() -> None:
    events: list[str] = []
    registry = _RecorderRegistry(events)
    probe_calls = 0

    def probe() -> dict[str, object]:
        nonlocal probe_calls
        probe_calls += 1
        events.append("probe")
        return _probe(competing=True)

    def build(opened: launcher.OpenedFloorAttempt) -> launcher.FloorAttemptTerminal:
        events.append("build-terminal")
        assert opened.measurement is None
        assert opened.failure is None
        assert opened.probe_after is None
        assert opened.launch_failures == ()
        assert opened.repetition_evidence == ()
        return _terminal(opened)

    result = launcher._launch_floor_attempt_for_test(
        _reservation(), _genesis(), _measurement(),
        post_probe=probe,
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=build,
        registry=registry,
        capture_measure_point=lambda *_args, **_kwargs: pytest.fail(
            "capture must not run"
        ),
    )

    assert probe_calls == 1
    assert events == [
        "reserve", "probe", "classify", "build-terminal",
        "observe-failure", "terminal",
    ]
    assert result.opened.pre_observation_failure_reason == (
        launcher.POST_PROBE_COMPETING_REASON
    )


def test_private_rep_sink_snapshot_occurs_after_token_open() -> None:
    events: list[str] = []
    token = _Token(events)

    def capture(*_args: object, **kwargs: object) -> _Token:
        assert token.opened is False and token._rep_sink is None
        _bind_sink(token, kwargs)
        assert token._rep_sink == []
        return token

    def build(opened: launcher.OpenedFloorAttempt) -> launcher.FloorAttemptTerminal:
        assert token.opened is True and opened.measurement is token
        assert opened.repetition_evidence == (
            {
                "rep_index": 0, "returncode": 0, "counter_status": "available",
                "missing_perf_events": [], "perf_raw": {}, "throughput": 101.0,
            },
            {
                "rep_index": 1, "returncode": 0, "counter_status": "available",
                "missing_perf_events": [], "perf_raw": {}, "throughput": 102.0,
            },
            {
                "rep_index": 2, "returncode": 0, "counter_status": "available",
                "missing_perf_events": [], "perf_raw": {}, "throughput": 103.0,
            },
        )
        assert token.rep_observations == [{"source": "public measurement view"}]
        assert (opened.expected_use_perf, opened.reps_expected) == (True, 3)
        return _terminal(opened)

    result = launcher._launch_floor_attempt_for_test(
        _reservation(), _genesis(), _measurement(), post_probe=_probe,
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=build, registry=_RecorderRegistry(events),
        capture_measure_point=capture,
    )
    assert result.opened.repetition_evidence is not token.rep_observations


def test_capture_uses_checked_kwargs_snapshot_after_source_mapping_mutates() -> None:
    extra_env = {"MODE": "checked"}
    numactl = ["numactl", "--cpunodebind=0"]
    source = {
        "extime": 3, "reps": 3, "use_perf": True,
        "extra_env": extra_env, "numactl": numactl,
    }
    measurement = replace(_measurement(), keyword_arguments=source)
    token = _Token([])
    probe_calls = 0

    def probe() -> dict[str, object]:
        nonlocal probe_calls
        if probe_calls == 0:
            source.update(reps=99, use_perf=False)
            extra_env["MODE"] = "mutated"
            numactl[1] = "--cpunodebind=1"
        probe_calls += 1
        return _probe()

    def capture(*_args: object, **kwargs: object) -> _Token:
        assert (kwargs["reps"], kwargs["use_perf"]) == (3, True)
        assert kwargs["extra_env"] == {"MODE": "checked"}
        assert kwargs["extra_env"] is not extra_env
        assert kwargs["numactl"] == ("numactl", "--cpunodebind=0")
        _bind_sink(token, kwargs)
        return token

    launcher._launch_floor_attempt_for_test(
        _reservation(), _genesis(), measurement, post_probe=probe,
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=_terminal, registry=_RecorderRegistry([]),
        capture_measure_point=capture,
    )
    assert source == {
        "extime": 3, "reps": 99, "use_perf": False,
        "extra_env": {"MODE": "mutated"},
        "numactl": ["numactl", "--cpunodebind=1"],
    }


def test_v2_profile_is_rejected_before_any_registry_side_effect() -> None:
    class _V2Profile(_Profile):
        schema = s8b_attempt_profile.S8B_V2_SCHEMA_PROFILE

    events: list[str] = []
    registry = _RecorderRegistry(events)
    reservations = (
        replace(_reservation(), profile=_V2Profile()),
        replace(_reservation(), consumption_marker=object()),
    )
    for reservation in reservations:
        with pytest.raises(
            launcher.FloorAttemptLauncherError,
            match=r"^\[s8b-launcher-v2-terminal\]",
        ):
            launcher._launch_floor_attempt_for_test(
                reservation, _genesis(), _measurement(), post_probe=pytest.fail,
                classified_at=lambda: "2026-08-26T00:00:01+00:00",
                terminal_builder=pytest.fail, registry=registry,
                capture_measure_point=pytest.fail,
            )
    assert registry.create_calls == registry.read_calls == 0
    assert events == []


def test_certified_api_owns_classification_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert "classification_authority" not in inspect.signature(
        launcher.launch_floor_attempt
    ).parameters
    events: list[str] = []
    registry = _RecorderRegistry(events)
    token = _Token(events)

    monkeypatch.setattr(
        launcher, "_PRODUCTION_DEPENDENCIES",
        launcher._LauncherDependencies(registry, _capture_token(token)),
    )
    monkeypatch.setattr(launcher, "_owned_post_probe", _probe)
    launcher.launch_floor_attempt(
        _reservation(), _genesis(), _measurement(),
        post_probe=launcher.floor_post_probe_capability(),
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=_terminal,
    )
    authority = launcher._CLASSIFICATION_AUTHORITY
    assert authority.authority_id == (
        "s8b-floor-attempt-launcher/pre-output-classification/v1"
    )
    assert launcher._CLASSIFICATION_POLICY == {
        "schema": "s8b-floor-pre-output-classification/v1",
        "precedence": ["competing_process", "launch_failure"],
        "probe_argv": ["pgrep", "-af", r"ycsb_.*\.exe"],
        "probe_timeout_s": 120.0,
    }
    assert registry.classification_kwargs["authority_id"] == authority.authority_id
    assert registry.classification_kwargs["authority_policy_sha256"] == (
        hashlib.sha256(
            launcher._canonical_json_bytes(
                launcher._CLASSIFICATION_POLICY, label="classification policy",
            )
        ).hexdigest()
    )


def test_reservation_rejects_protocol_not_bound_to_binding() -> None:
    policy = launcher._checked_reservation_policy(_reservation(), _measurement())
    assert policy.capture_keyword_arguments == _measurement().keyword_arguments
    reservation = replace(
        _reservation(), protocol={"reps": 3, "session_cv_max": "0.10"},
    )
    with pytest.raises(
        launcher.FloorAttemptLauncherError, match="not bound",
    ):
        launcher._checked_reservation_policy(reservation, _measurement())


def test_use_perf_must_be_derived_from_receipt() -> None:
    policy = launcher._checked_reservation_policy(_reservation(), _measurement())
    assert policy.expected_use_perf is True
    reservation = replace(
        _reservation(), perf_preflight_receipt=_unavailable_receipt(),
    )
    with pytest.raises(
        launcher.FloorAttemptLauncherError, match="use_perf differs",
    ):
        launcher._checked_reservation_policy(reservation, _measurement())


@pytest.mark.parametrize(("reservation", "message"), (
    (replace(_reservation(), mode="draft"), "mode"),
    (replace(_reservation(), mode="official", perf_preflight_receipt=_available_receipt()), "official"),
    (
        replace(_reservation(), protocol=_CallableDict(_PROTOCOL)),
        r"^reservation policy contains a callable$",
    ),
    (
        replace(
            _reservation(),
            perf_preflight_receipt=_CallableDict(_available_receipt()),
        ),
        r"^reservation policy contains a callable$",
    ),
))
def test_reservation_policy_rejects_each_untrusted_selector(
    reservation: launcher.FloorAttemptReservation, message: str,
) -> None:
    policy = launcher._checked_reservation_policy(_reservation(), _measurement())
    assert policy.reps_expected == 3
    with pytest.raises(launcher.FloorAttemptLauncherError, match=message):
        launcher._checked_reservation_policy(reservation, _measurement())


def test_reserve_forwards_consumption_marker_to_adapter() -> None:
    registry = _RecorderRegistry([])
    marker = object()
    launcher._reserve(
        replace(_reservation(), consumption_marker=marker),
        output=launcher._OwnedRawOutput(),
        dependencies=launcher._LauncherDependencies(registry, pytest.fail),
    )
    assert registry.reservation_kwargs["consumption_marker"] is marker


def test_pre_probe_competition_classifies_as_competing() -> None:
    launch_failure = calibrator_runner.MeasurementLaunchFailure("OSError", 5, "failed")
    competing = launcher.POST_PROBE_COMPETING_REASON
    launch = launcher.MEASUREMENT_LAUNCH_FAILURE_REASON
    cases = (
        (_probe(competing=True), _probe(), (), None, competing),
        (_probe(), _probe(competing=True), (), None, competing),
        (_probe(), _probe(), (launch_failure,), None, launch),
        (_probe(), _probe(), (), {"stage": "capture"}, launch),
        (_probe(), _probe(), (), None, None),
    )
    for before, after, failures, failure, expected in cases:
        assert launcher._pre_observation_failure_reason(
            probe_before=before, probe_after=after,
            launch_failures=failures, failure=failure,
        ) == expected


def test_external_evidence_digest_binds_both_probes() -> None:
    before = _probe()
    launch_failure = calibrator_runner.MeasurementLaunchFailure("OSError", 5, "launch failed")
    capture_failure = {
        "stage": "capture", "exception_type": "OSError",
        "errno": 5, "message": "capture failed",
    }
    payload = {
        "schema_version": "s8b-floor-pre-output-evidence/v2",
        "probe_before": before, "probe_after": None,
        "launch_failures": [{
            "exception_type": "OSError", "errno": 5, "message": "launch failed",
        }],
        "capture_failure": capture_failure,
    }
    common = {"launch_failures": (launch_failure,), "capture_failure": capture_failure}
    digest = launcher._external_evidence_sha256(
        probe_before=before, probe_after=None, **common,
    )
    expected = attempt_registry_core.canonical_json_bytes(payload)
    assert digest == hashlib.sha256(expected).hexdigest()
    changed_before = {**before, "stdout": "different pre-probe output"}
    changed_capture = {**capture_failure, "message": "different"}
    changed_before_digest = launcher._external_evidence_sha256(
        probe_before=changed_before, probe_after=None, **common)
    after_digest = launcher._external_evidence_sha256(
        probe_before=before, probe_after=_probe(), **common)
    changed_capture_digest = launcher._external_evidence_sha256(
        probe_before=before, probe_after=None, launch_failures=(launch_failure,),
        capture_failure=changed_capture)
    assert len({digest, changed_before_digest, after_digest, changed_capture_digest}) == 4


def test_probe_result_requires_exact_keys() -> None:
    assert launcher._post_probe(_probe()) == _probe()
    invalid_results = (
        ({**_probe(), "unexpected": "value"}, "exact four-key"),
        ({key: value for key, value in _probe().items() if key != "rc"},
         "exact four-key"),
        ({**_probe(), "rc": True}, "exact field types"),
        ({**_probe(), "stdout": 1}, "exact field types"),
    )
    for result, message in invalid_results:
        with pytest.raises(launcher.FloorAttemptLauncherError, match=message):
            launcher._post_probe(result)


def test_capture_exception_terminalizes_with_stage_capture() -> None:
    events: list[str] = []
    registry = _RecorderRegistry(events)

    def capture(*_args: object, **kwargs: object) -> object:
        assert type(kwargs["rep_observations"]) is list
        events.append("capture")
        raise OSError(5, "capture failed")

    def build(opened: launcher.OpenedFloorAttempt) -> launcher.FloorAttemptTerminal:
        events.append("build-terminal")
        assert opened.failure == {
            "stage": "capture",
            "exception_type": "OSError",
            "errno": 5,
            "message": "[Errno 5] capture failed",
        }
        assert opened.measurement is None
        assert opened.repetition_evidence == ()
        return _terminal(opened)

    result = launcher._launch_floor_attempt_for_test(
        _reservation(), _genesis(), _measurement(),
        post_probe=lambda: (events.append("probe") or _probe()),
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=build, registry=registry,
        capture_measure_point=capture,
    )
    assert events == [
        "reserve", "probe", "capture", "probe", "classify",
        "build-terminal", "observe-failure", "terminal",
    ]
    assert result.opened.pre_observation_failure_reason == (
        launcher.MEASUREMENT_LAUNCH_FAILURE_REASON
    )


def test_reservation_rejects_reps_not_equal_to_protocol() -> None:
    policy = launcher._checked_reservation_policy(_reservation(), _measurement())
    assert policy.reps_expected == 3
    measurement = replace(
        _measurement(),
        keyword_arguments={"extime": 3, "reps": 2, "use_perf": True},
    )
    with pytest.raises(
        launcher.FloorAttemptLauncherError, match="reps differs",
    ):
        launcher._checked_reservation_policy(_reservation(), measurement)


def test_open_failure_yields_empty_repetition_evidence() -> None:
    events: list[str] = []
    registry = _RecorderRegistry(events)
    token = _Token(events, open_error=RuntimeError("open failed"))

    result = launcher._launch_floor_attempt_for_test(
        _reservation(), _genesis(), _measurement(), post_probe=_probe,
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=_terminal, registry=registry,
        capture_measure_point=_capture_token(token),
    )
    assert token._rep_sink
    assert result.opened.failure is not None
    assert result.opened.failure["stage"] == "open"
    assert result.opened.repetition_evidence == ()
    assert result.terminal.terminal_status == "terminal-failure"


def test_open_failure_cannot_be_reported_as_observed() -> None:
    events: list[str] = []
    token = _Token(events, open_error=RuntimeError("open failed"))
    registry = _RecorderRegistry(events)

    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match=r"^\[s8b-launcher-terminal\] observed terminal contradicts",
    ):
        launcher._launch_floor_attempt_for_test(
            _reservation(), _genesis(), _measurement(), post_probe=_probe,
            classified_at=lambda: "2026-08-26T00:00:01+00:00",
            terminal_builder=lambda opened: replace(
                _terminal(opened), terminal_status="observed",
                observation_sha256="5" * 64,
                primary_value={"throughput": 102.0},
            ),
            registry=registry,
            capture_measure_point=_capture_token(token),
        )
    assert not {"terminal", "observe-success", "observe-failure"}.intersection(events)
    assert callable(registry.reader)
    with pytest.raises(
        launcher.FloorAttemptLauncherError, match="cannot be read before",
    ):
        registry.reader()


def test_certified_api_rejects_a_caller_callable_post_probe_without_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    effects = []
    monkeypatch.setattr(
        launcher,
        "_PRODUCTION_DEPENDENCIES",
        launcher._LauncherDependencies(
            registry=pytest.fail,
            capture_measure_point=pytest.fail,
        ),
    )
    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match="launcher-issued fixed capability",
    ):
        launcher.launch_floor_attempt(
            _reservation(),
            _genesis(),
            _measurement(),
            post_probe=lambda: effects.append("probe"),  # type: ignore[arg-type]
            classified_at=lambda: "2026-08-26T00:00:01+00:00",
            terminal_builder=lambda _opened: pytest.fail(
                "terminal builder must not run"
            ),
        )
    assert effects == []


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", str(Path(__file__).resolve())]))
