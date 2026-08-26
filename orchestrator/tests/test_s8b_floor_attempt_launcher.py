"""Ordering and ownership tests for the trusted 8b floor attempt launcher."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import subprocess
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from orchestrator.calibrator import runner as calibrator_runner  # noqa: E402
from orchestrator.campaign import attempt_registry_core  # noqa: E402
from orchestrator.campaign import s8b_attempt_profile  # noqa: E402
from orchestrator.campaign import s8b_attempt_registry  # noqa: E402
from orchestrator.campaign import s8b_floor_attempt_launcher as launcher  # noqa: E402


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


_PROFILE = _Profile()
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

    def open(self) -> object:
        self.events.append("open")
        self.opened = True
        if self.open_error is not None:
            raise self.open_error
        return {
            "throughputs": [101.0, 102.0, 103.0],
            "run_cmd": "perf stat ccbench",
        }


def _reservation() -> launcher.FloorAttemptReservation:
    return launcher.FloorAttemptReservation(
        repo_root=Path("/tmp/launcher-recorder"),
        profile=_PROFILE,
        binding=object(),
        slot_id=("holdout-a", "configuration-a", 7, 0),
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
        assert kwargs == {"extime": 3, "reps": 3, "use_perf": True}
        return token

    def post_probe() -> dict[str, object]:
        events.append("post-probe")
        return {
            "rc": 0 if competing else 1,
            "stdout": "999 ycsb_other.exe\n" if competing else "",
            "stderr": "",
            "competing": competing,
        }

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
    capture = lambda *args, **kwargs: (events.append("capture") or token)

    def terminal_builder(
        opened: launcher.OpenedFloorAttempt,
    ) -> launcher.FloorAttemptTerminal:
        events.append("build-terminal")
        assert opened.measurement is None
        assert isinstance(opened.open_error, RuntimeError)
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
        post_probe=lambda: (
            events.append("post-probe")
            or {"rc": 1, "stdout": "", "stderr": "", "competing": False}
        ),
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
        "capture",
        "post-probe",
        "classify",
        "open",
        "build-terminal",
        "observe-failure",
        "terminal",
    ]
    assert isinstance(result.opened.open_error, RuntimeError)


def test_empty_output_cannot_reach_observation_or_terminal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    fake_registry = _RecorderRegistry(events)
    token = _Token(events)
    capture = lambda *args, **kwargs: (events.append("capture") or token)

    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match="non-empty raw output bytes",
    ):
        launcher._launch_floor_attempt_for_test(
            _reservation(),
            _genesis(),
            _measurement(),
            post_probe=lambda: (
                events.append("post-probe")
                or {
                    "rc": 1,
                    "stdout": "",
                    "stderr": "",
                    "competing": False,
                }
            ),
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
    reservation = launcher.FloorAttemptReservation(
        repo_root=repo,
        profile=profile,
        binding=binding,
        slot_id=profile.slot_codec.slot_id(planned),
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
    launcher._ensure_registry_genesis(
        reservation,
        complete,
        dependencies=launcher._PRODUCTION_DEPENDENCIES,
    )
    rows = s8b_attempt_registry.read_attempt_registry(
        repo,
        profile=profile,
        binding=binding,
    )
    assert rows[0]["slots"] == [
        profile.slot_codec.to_json(planned),
        profile.slot_codec.to_json(retry),
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
            classification_authority=launcher.ClassificationAuthority(
                authority_id="launcher-test-authority",
                authority_policy_sha256="6" * 64,
            ),
            classified_at=lambda: "2026-08-26T00:00:01+00:00",
            terminal_builder=lambda _opened: pytest.fail(
                "terminal builder must not run"
            ),
        )
    assert effects == []


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", str(Path(__file__).resolve())]))
