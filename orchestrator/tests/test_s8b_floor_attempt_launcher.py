"""Ordering and ownership tests for the trusted 8b floor attempt launcher."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
import hashlib
import inspect
import json
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
from orchestrator.campaign import s8b_floor_stats  # noqa: E402
from orchestrator.campaign import s8b_holdout_admission  # noqa: E402
from orchestrator.campaign import s8b_terminal_evidence  # noqa: E402
from orchestrator.tests import test_s8b_attempt_registry as registry_cases  # noqa: E402
from orchestrator.tests import test_s8b_holdout_admission as admission_cases  # noqa: E402


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
        self.sealed_draft: object | None = None

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

    def record_sealed_attempt_terminal(
        self, observation: _Observation, evidence: object,
    ) -> None:
        self.events.append("sealed-draft")
        self.sealed_draft = evidence
        assert observation.raw_output
        assert type(evidence) is s8b_terminal_evidence.SealedTerminalEvidenceDraft
        raise launcher.FloorAttemptLauncherError(
            "[s8b-launcher-v2-terminal] fake registry cannot issue "
            "validated evidence"
        )


class _AcceptOnlyRecorderRegistry(_RecorderRegistry):
    """Recorder whose terminal sink adds no rejection after the leaf gates."""

    def record_sealed_attempt_terminal(
        self, observation: _Observation, evidence: object,
    ) -> None:
        self.events.append("sealed-draft")
        self.sealed_draft = evidence
        assert observation.raw_output
        assert type(evidence) is s8b_terminal_evidence.SealedTerminalEvidenceDraft


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
                "execution_failure": False,
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
        schedule_row_sha256=_PLANNED_SLOT.schedule_row_sha256,
        records=1000,
        threads=4,
        workload={"kind": "launcher-test"},
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
        schedule_row_sha256=planned.schedule_row_sha256,
        records=1000,
        threads=4,
        workload={"kind": "launcher-test"},
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
                "execution_failure": False, "missing_perf_events": [],
                "perf_raw": {}, "throughput": 101.0,
            },
            {
                "rep_index": 1, "returncode": 0, "counter_status": "available",
                "execution_failure": False, "missing_perf_events": [],
                "perf_raw": {}, "throughput": 102.0,
            },
            {
                "rep_index": 2, "returncode": 0, "counter_status": "available",
                "execution_failure": False, "missing_perf_events": [],
                "perf_raw": {}, "throughput": 103.0,
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


def test_v2_profile_reaches_draft_but_fake_cannot_issue_capability(
    tmp_path: Path,
) -> None:
    class _V2Profile:
        schema = s8b_attempt_profile.S8B_V2_SCHEMA_PROFILE
        slot_codec = s8b_attempt_profile.S8B_V2_SLOT_CODEC

    class _V2Token(_Token):
        def open(self) -> object:
            self.events.append("open")
            self.opened = True
            assert self._rep_sink is not None
            self._rep_sink.extend(
                {
                    "rep_index": rep,
                    "returncode": 0,
                    "execution_failure": False,
                    "counter_status": "not_required",
                    "missing_perf_events": [],
                    "perf_raw": {
                        event: None for event in calibrator_runner.PERF_EVENTS
                    },
                    "throughput": throughput,
                }
                for rep, throughput in enumerate(self.throughputs)
            )
            return self

    events: list[str] = []
    registry = _RecorderRegistry(events)
    protocol = {"reps": 3, "session_cv_max": "0.10"}
    workload = {"kind": "launcher-v2-test"}
    binary = tmp_path / "ycsb-v2.exe"
    binary.write_bytes(b"v2-binary")
    slot = s8b_attempt_profile.S8BV2AttemptSlot(
        freeze_holdout_key="holdout-a",
        configuration_id="configuration-a",
        repetition=7,
        measurement_ordinal=0,
        attempt_ordinal=0,
        schedule_row_sha256="7" * 64,
    )
    reservation = replace(
        _reservation(),
        profile=_V2Profile(),
        binding=s8b_attempt_profile.S8BAttemptBinding(
            freeze_sha256="a" * 64,
            protocol_sha256=launcher.canonical_protocol_sha256(protocol),
            schedule_sha256="b" * 64,
        ),
        slot_id=s8b_attempt_profile.S8B_V2_SLOT_CODEC.slot_id(slot),
        protocol=protocol,
        perf_preflight_receipt=_unavailable_receipt(),
        consumption_marker=object(),
        schedule_row_sha256=slot.schedule_row_sha256,
        workload=workload,
    )
    genesis = launcher.FloorAttemptRegistryGenesis(slots=(slot,))
    measurement = replace(
        _measurement(),
        binary=str(binary),
        keyword_arguments={
            **_measurement().keyword_arguments,
            "use_perf": False,
            "workload": workload,
        },
    )
    token = _V2Token(events)
    token.records = reservation.records
    token.threads = reservation.threads

    def build(
        opened: launcher.OpenedFloorAttempt,
    ) -> launcher.FloorAttemptTerminal:
        assessment = s8b_floor_stats.assess_session(
            [101.0, 102.0, 103.0], reps=3, session_cv_max="0.10",
        )
        record = {
            "attempt_id": reservation.attempt_id,
            "binary_sha256_at_measure": opened.binary_sha256_at_measure,
            "cell_id": reservation.cell_id,
            "configuration_id": "configuration-a",
            "duration_s": opened.duration_s,
            "event": "session",
            "excluded_reason": None,
            "exclusion_class": None,
            "exec_failures": 0,
            "holdout_id": "holdout-a",
            "kind": "planned",
            "notes": [],
            "probe_after": dict(opened.probe_after or {}),
            "probe_before": dict(opened.probe_before),
            "records": reservation.records,
            "rep_integrity_failures": 0,
            "rep_observations": [
                dict(item) for item in opened.repetition_evidence
            ],
            "reps_expected": 3,
            "retry": False,
            "retry_ordinal": None,
            "round": 8,
            "run_cmd": "v2 command",
            "seq": 7,
            "session_cv": assessment.cv,
            "session_median": 102.0,
            "threads": reservation.threads,
            "throughputs": [101.0, 102.0, 103.0],
            "trigger": None,
            "valid": True,
            "workload": workload,
        }
        raw = (
            json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False)
            + "\n"
        ).encode("utf-8")
        observations_digest = hashlib.sha256(
            attempt_registry_core.canonical_json_bytes(
                record["rep_observations"]
            )
        ).hexdigest()
        return launcher.FloorAttemptTerminal(
            raw_output_bytes=raw,
            terminal_status="observed",
            report_sha256=hashlib.sha256(raw).hexdigest(),
            observation_sha256=observations_digest,
            primary_value=102.0,
            finished_at=opened.finished_at,
            campaign_record=record,
        )

    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match=r"^\[s8b-launcher-v2-terminal\] fake registry cannot issue",
    ):
        launcher._launch_floor_attempt_for_test(
            reservation,
            genesis,
            measurement,
            post_probe=_probe,
            classified_at=lambda: "2026-08-26T00:00:01+00:00",
            terminal_builder=build,
            registry=registry,
            capture_measure_point=_capture_token(token),
        )
    assert type(registry.sealed_draft) is (
        s8b_terminal_evidence.SealedTerminalEvidenceDraft
    )
    assert registry.sealed_draft.document["attempt_binding"].keys() == {
        "admission_claim_digest",
        "attempt_id",
        "campaign_run_id",
        "freeze_sha256",
        "manifest_sha256",
        "protocol_sha256",
        "run_relpath",
        "schedule_row_sha256",
        "schedule_sha256",
    }
    assert events[-2:] == ["observe-success", "sealed-draft"]


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


def _v2_policy_case(
    tmp_path: Path,
) -> tuple[
    launcher.FloorAttemptReservation,
    launcher.FloorMeasurementCapture,
    s8b_attempt_profile.S8BV2AttemptSlot,
]:
    class _V2PolicyProfile:
        schema = s8b_attempt_profile.S8B_V2_SCHEMA_PROFILE
        slot_codec = s8b_attempt_profile.S8B_V2_SLOT_CODEC

    protocol = {"reps": 3, "session_cv_max": "0.10"}
    workload = {"kind": "v2-policy"}
    slot = s8b_attempt_profile.S8BV2AttemptSlot(
        freeze_holdout_key="holdout-a",
        configuration_id="configuration-a",
        repetition=7,
        measurement_ordinal=0,
        attempt_ordinal=0,
        schedule_row_sha256="7" * 64,
    )
    binary = tmp_path / "v2-policy.exe"
    binary.write_bytes(b"v2-policy-binary")
    reservation = replace(
        _reservation(),
        profile=_V2PolicyProfile(),
        binding=s8b_attempt_profile.S8BAttemptBinding(
            freeze_sha256="a" * 64,
            protocol_sha256=launcher.canonical_protocol_sha256(protocol),
            schedule_sha256="b" * 64,
        ),
        slot_id=s8b_attempt_profile.S8B_V2_SLOT_CODEC.slot_id(slot),
        protocol=protocol,
        perf_preflight_receipt=_unavailable_receipt(),
        consumption_marker=object(),
        schedule_row_sha256=slot.schedule_row_sha256,
        records=1000,
        threads=4,
        workload=workload,
    )
    measurement = replace(
        _measurement(),
        binary=str(binary),
        keyword_arguments={
            **_measurement().keyword_arguments,
            "use_perf": False,
            "workload": workload,
        },
    )
    return reservation, measurement, slot


class _OpenedV2Token(_Token):
    def open(self) -> object:
        self.events.append("open")
        self.opened = True
        assert self._rep_sink is not None
        self._rep_sink.extend(
            {
                "rep_index": rep,
                "returncode": 0,
                "execution_failure": False,
                "counter_status": "not_required",
                "missing_perf_events": [],
                "perf_raw": {
                    event: None for event in calibrator_runner.PERF_EVENTS
                },
                "throughput": throughput,
            }
            for rep, throughput in enumerate(self.throughputs)
        )
        if self.open_error is not None:
            raise self.open_error
        if not hasattr(self, "records"):
            self.records = 1000
        if not hasattr(self, "threads"):
            self.threads = 4
        return self


def _v2_terminal_from_opened(
    reservation: launcher.FloorAttemptReservation,
    opened: launcher.OpenedFloorAttempt,
    *,
    session_cv_max: str,
) -> launcher.FloorAttemptTerminal:
    measurement_ordinal = reservation.slot_id[3]
    is_retry = measurement_ordinal != 0
    values = [] if opened.measurement is None else list(
        opened.measurement.throughputs
    )
    assessment = s8b_floor_stats.assess_session(
        values,
        reps=opened.reps_expected,
        session_cv_max=session_cv_max,
    )
    competing = opened.probe_before["competing"] is True or (
        opened.probe_after is not None
        and opened.probe_after["competing"] is True
    )
    if competing:
        excluded_reason = exclusion_class = "competing_process"
    elif opened.failure is not None or opened.launch_failures:
        excluded_reason = exclusion_class = "launch_failure"
    else:
        excluded_reason = assessment.required_reason
        exclusion_class = assessment.required_reason
    observed = excluded_reason is None
    observations = [dict(item) for item in opened.repetition_evidence]
    record = {
        "attempt_id": reservation.attempt_id,
        "binary_sha256_at_measure": opened.binary_sha256_at_measure,
        "cell_id": reservation.cell_id,
        "configuration_id": reservation.slot_id[1],
        "duration_s": opened.duration_s,
        "event": "session",
        "excluded_reason": excluded_reason,
        "exclusion_class": exclusion_class,
        "exec_failures": (
            opened.reps_expected if opened.failure is not None else 0
        ),
        "holdout_id": reservation.slot_id[0],
        "kind": "retry" if is_retry else "planned",
        "notes": [],
        "probe_after": (
            None if opened.probe_after is None else dict(opened.probe_after)
        ),
        "probe_before": dict(opened.probe_before),
        "records": reservation.records,
        "rep_integrity_failures": (
            None if opened.measurement is None else 0
        ),
        "rep_observations": observations,
        "reps_expected": opened.reps_expected,
        "retry": is_retry,
        "retry_ordinal": measurement_ordinal if is_retry else None,
        "round": 8,
        "run_cmd": "v2 command",
        "seq": 7,
        "session_cv": assessment.cv,
        "session_median": (
            float(assessment.median) if observed else None
        ),
        "threads": reservation.threads,
        "throughputs": values,
        "trigger": "launcher-retry-test" if is_retry else None,
        "valid": observed,
        "workload": dict(reservation.workload),
    }
    raw = s8b_attempt_profile.serialize_session_line(record)
    return launcher.FloorAttemptTerminal(
        raw_output_bytes=raw,
        terminal_status="observed" if observed else "retryable-failure",
        report_sha256=hashlib.sha256(raw).hexdigest(),
        observation_sha256=(
            hashlib.sha256(
                attempt_registry_core.canonical_json_bytes(observations)
            ).hexdigest()
            if observed
            else None
        ),
        primary_value=(
            float(assessment.median) if observed else None
        ),
        finished_at=opened.finished_at,
        campaign_record=record,
    )


def _v2_fake_launch_case(
    tmp_path: Path,
    *,
    throughputs: tuple[float, float, float] = (100.0, 101.0, 102.0),
    measurement_ordinal: int = 0,
    attempt_ordinal: int = 0,
) -> tuple[
    launcher.FloorAttemptReservation,
    launcher.FloorMeasurementCapture,
    launcher.FloorAttemptRegistryGenesis,
    _OpenedV2Token,
    _RecorderRegistry,
]:
    reservation, measurement, slot = _v2_policy_case(tmp_path)
    slot = replace(
        slot,
        measurement_ordinal=measurement_ordinal,
        attempt_ordinal=attempt_ordinal,
    )
    reservation = replace(
        reservation,
        slot_id=s8b_attempt_profile.S8B_V2_SLOT_CODEC.slot_id(slot),
    )
    token = _OpenedV2Token([])
    token.throughputs = list(throughputs)
    token.records = reservation.records
    token.threads = reservation.threads
    registry = _RecorderRegistry([])
    return (
        reservation,
        measurement,
        launcher.FloorAttemptRegistryGenesis(slots=(slot,)),
        token,
        registry,
    )


def _terminal_with_retry_ordinal(
    terminal: launcher.FloorAttemptTerminal,
    retry_ordinal: int | None,
) -> launcher.FloorAttemptTerminal:
    assert isinstance(terminal.campaign_record, Mapping)
    record = {**terminal.campaign_record, "retry_ordinal": retry_ordinal}
    raw = s8b_attempt_profile.serialize_session_line(record)
    return replace(
        terminal,
        raw_output_bytes=raw,
        report_sha256=hashlib.sha256(raw).hexdigest(),
        campaign_record=record,
    )


def test_planned_terminal_rejects_nonnull_retry_ordinal(
    tmp_path: Path,
) -> None:
    reservation, measurement, genesis, token, _registry = (
        _v2_fake_launch_case(tmp_path)
    )
    registry = _AcceptOnlyRecorderRegistry([])

    def build(
        opened: launcher.OpenedFloorAttempt,
    ) -> launcher.FloorAttemptTerminal:
        terminal = _v2_terminal_from_opened(
            reservation, opened, session_cv_max="0.10",
        )
        assert terminal.campaign_record["retry_ordinal"] is None
        return _terminal_with_retry_ordinal(
            terminal, reservation.slot_id[4],
        )

    with pytest.raises(
        s8b_terminal_evidence.TerminalEvidenceError,
        match="campaign_record.retry_ordinal differs from durable identity",
    ):
        launcher._launch_floor_attempt_for_test(
            reservation,
            genesis,
            measurement,
            post_probe=_probe,
            classified_at=lambda: "2026-09-08T00:00:01+00:00",
            terminal_builder=build,
            registry=registry,
            capture_measure_point=_capture_token(token),
        )
    assert registry.sealed_draft is None


def test_retry_terminal_rejects_recovery_ordinal_substitution(
    tmp_path: Path,
) -> None:
    reservation, measurement, genesis, token, _registry = (
        _v2_fake_launch_case(
            tmp_path,
            measurement_ordinal=2,
            attempt_ordinal=1,
        )
    )
    registry = _AcceptOnlyRecorderRegistry([])
    assert reservation.slot_id[3] == 2
    assert reservation.slot_id[4] == 1

    def build(
        opened: launcher.OpenedFloorAttempt,
    ) -> launcher.FloorAttemptTerminal:
        terminal = _v2_terminal_from_opened(
            reservation, opened, session_cv_max="0.10",
        )
        assert terminal.campaign_record["retry_ordinal"] == 2
        return _terminal_with_retry_ordinal(
            terminal, reservation.slot_id[4],
        )

    with pytest.raises(
        s8b_terminal_evidence.TerminalEvidenceError,
        match="campaign_record.retry_ordinal differs from durable identity",
    ):
        launcher._launch_floor_attempt_for_test(
            reservation,
            genesis,
            measurement,
            post_probe=_probe,
            classified_at=lambda: "2026-09-08T00:00:01+00:00",
            terminal_builder=build,
            registry=registry,
            capture_measure_point=_capture_token(token),
        )
    assert registry.sealed_draft is None


def _real_v2_launch_case(
    tmp_path: Path,
) -> tuple[
    launcher.FloorAttemptReservation,
    launcher.FloorMeasurementCapture,
    launcher.FloorAttemptRegistryGenesis,
    _OpenedV2Token,
]:
    original_documents = admission_cases._fixture_documents

    def full_protocol_documents(master_seed: str = "seed-a") -> tuple[dict, dict]:
        protocol, freeze = original_documents(master_seed)
        return ({**protocol, "session_cv_max": "0.10"}, freeze)

    admission_cases._fixture_documents = full_protocol_documents
    try:
        case, profile, binding, slot = (
            registry_cases._v2_registry_capability_case(tmp_path)
        )
    finally:
        admission_cases._fixture_documents = original_documents
    claim = s8b_holdout_admission._read_canonical_document(
        case["claim_path"]
    )
    protocol_path = (
        case["repo_root"] / "output/s8b-freeze/floor_protocol.json"
    )
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    binary = tmp_path / "certified-v2.exe"
    binary.write_bytes(b"certified-v2-binary")
    reservation = launcher.FloorAttemptReservation(
        repo_root=case["repo_root"],
        profile=profile,
        binding=binding,
        slot_id=profile.slot_codec.slot_id(slot),
        protocol=protocol,
        mode=str(claim["mode"]),
        perf_preflight_receipt=_unavailable_receipt(),
        consumption_marker=case["capability"],
        run_start_receipt_sha256="4" * 64,
        process_identity={
            "pid": 1234,
            "starttime": "launcher-real-start",
            "execution_uuid": "launcher-real-execution",
        },
        started_at="2026-09-08T00:00:00+00:00",
        admission_claim_digest=case["marker"][
            "measurement_generation_claim_digest"
        ],
        attempt_id=case["marker"]["attempt_id"],
        campaign_run_id=case["marker"]["campaign_run_id"],
        manifest_sha256=case["marker"]["manifest_sha256"],
        run_relpath=case["marker"]["run_relpath"],
        cell_id=case["marker"]["cell_id"],
        schedule_row_sha256=slot.schedule_row_sha256,
        records=int(claim["records"]),
        threads=int(claim["threads"]),
        workload=dict(claim["workload"]),
    )
    measurement = launcher.FloorMeasurementCapture(
        binary=str(binary),
        records=reservation.records,
        threads=reservation.threads,
        clocks_per_us=2400,
        keyword_arguments={
            "reps": int(protocol["reps"]),
            "use_perf": False,
            "workload": dict(reservation.workload),
        },
    )
    token = _OpenedV2Token([])
    token.throughputs = [100.0] * int(protocol["reps"])
    token.records = reservation.records
    token.threads = reservation.threads
    return (
        reservation,
        measurement,
        launcher.FloorAttemptRegistryGenesis(slots=(slot,)),
        token,
    )


def test_v2_policy_accepts_exact_schema_marker_and_durable_coordinates(
    tmp_path: Path,
) -> None:
    reservation, measurement, _slot = _v2_policy_case(tmp_path)
    policy = launcher._checked_reservation_policy(reservation, measurement)
    assert policy.is_v2 is True
    assert policy.expected_use_perf is False
    assert policy.reps_expected == 3
    assert policy.capture_keyword_arguments == measurement.keyword_arguments
    assert "rep_observations" not in policy.capture_keyword_arguments


@pytest.mark.parametrize(
    "reservation_mutation",
    (
        {"consumption_marker": None},
        {"profile": _PROFILE, "consumption_marker": object()},
    ),
    ids=("v2-without-marker", "v1-with-marker"),
)
def test_schema_and_consumption_marker_must_be_biconditional_before_effects(
    tmp_path: Path,
    reservation_mutation: dict[str, object],
) -> None:
    reservation, measurement, _slot = _v2_policy_case(tmp_path)
    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match=r"^\[s8b-launcher-v2-policy\]",
    ):
        launcher._checked_reservation_policy(
            replace(reservation, **reservation_mutation), measurement,
        )


@pytest.mark.parametrize(
    ("reservation_mutation", "measurement_mutation", "message"),
    (
        ({"slot_id": ("too", "short")}, {}, "durable identity"),
        ({"schedule_row_sha256": "A" * 64}, {}, "durable identity"),
        ({"records": 0}, {}, "durable identity"),
        ({"threads": True}, {}, "durable identity"),
        ({"workload": _CallableDict()}, {}, "durable identity"),
        ({}, {"records": 999}, "capture coordinates"),
        ({}, {"threads": 999}, "capture coordinates"),
        (
            {},
            {"keyword_arguments": {
                "extime": 3,
                "reps": 3,
                "use_perf": False,
                "workload": {"kind": "different"},
            }},
            "capture coordinates",
        ),
    ),
    ids=(
        "slot-id",
        "schedule-row",
        "records-type",
        "threads-type",
        "workload-callable",
        "capture-records",
        "capture-threads",
        "capture-workload",
    ),
)
def test_v2_policy_rejects_each_local_durable_identity_mismatch(
    tmp_path: Path,
    reservation_mutation: dict[str, object],
    measurement_mutation: dict[str, object],
    message: str,
) -> None:
    reservation, measurement, _slot = _v2_policy_case(tmp_path)
    with pytest.raises(launcher.FloorAttemptLauncherError, match=message):
        launcher._checked_reservation_policy(
            replace(reservation, **reservation_mutation),
            replace(measurement, **measurement_mutation),
        )


def test_v2_genesis_rechecks_schedule_row_before_registry_create(
    tmp_path: Path,
) -> None:
    reservation, _measurement_value, slot = _v2_policy_case(tmp_path)
    fake = _RecorderRegistry([])
    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match="schedule row differs from closed genesis",
    ):
        launcher._ensure_registry_genesis(
            replace(reservation, schedule_row_sha256="f" * 64),
            launcher.FloorAttemptRegistryGenesis(slots=(slot,)),
            dependencies=launcher._LauncherDependencies(
                registry=fake,
                capture_measure_point=pytest.fail,
            ),
        )
    assert fake.create_calls == fake.read_calls == 0


def test_v2_protocol_snapshot_precedes_builder_mutation(
    tmp_path: Path,
) -> None:
    reservation, measurement, genesis, token, registry = (
        _v2_fake_launch_case(
            tmp_path,
            throughputs=(1.0, 100.0, 200.0),
        )
    )
    registry = _AcceptOnlyRecorderRegistry([])

    def build(
        opened: launcher.OpenedFloorAttempt,
    ) -> launcher.FloorAttemptTerminal:
        assert isinstance(reservation.protocol, dict)
        reservation.protocol["session_cv_max"] = "1.0"
        return _v2_terminal_from_opened(
            reservation, opened, session_cv_max="1.0",
        )

    with pytest.raises(
        s8b_terminal_evidence.TerminalEvidenceError,
        match="terminal.terminal_status differs from E1",
    ):
        try:
            launcher._launch_floor_attempt_for_test(
                reservation,
                genesis,
                measurement,
                post_probe=_probe,
                classified_at=lambda: "2026-09-08T00:00:01+00:00",
                terminal_builder=build,
                registry=registry,
                capture_measure_point=_capture_token(token),
            )
        finally:
            assert registry.sealed_draft is None


def test_v2_perf_receipt_snapshot_precedes_builder_mutation(
    tmp_path: Path,
) -> None:
    reservation, measurement, genesis, token, registry = (
        _v2_fake_launch_case(tmp_path)
    )
    original_receipt = dict(reservation.perf_preflight_receipt or {})

    def build(
        opened: launcher.OpenedFloorAttempt,
    ) -> launcher.FloorAttemptTerminal:
        assert isinstance(reservation.perf_preflight_receipt, dict)
        reservation.perf_preflight_receipt["reason"] = "builder-forged"
        return _v2_terminal_from_opened(
            reservation, opened, session_cv_max="0.10",
        )

    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match="fake registry cannot issue validated evidence",
    ):
        launcher._launch_floor_attempt_for_test(
            reservation,
            genesis,
            measurement,
            post_probe=_probe,
            classified_at=lambda: "2026-09-08T00:00:01+00:00",
            terminal_builder=build,
            registry=registry,
            capture_measure_point=_capture_token(token),
        )
    assert isinstance(
        registry.sealed_draft,
        s8b_terminal_evidence.SealedTerminalEvidenceDraft,
    )
    assert registry.sealed_draft.document[
        "perf_preflight_receipt_sha256"
    ] == hashlib.sha256(
        attempt_registry_core.canonical_json_bytes(original_receipt)
    ).hexdigest()


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("probe", "campaign_record.probe_before differs"),
        ("repetition", "terminal.observation_sha256 differs"),
    ),
)
def test_v2_builder_receives_detached_sources_not_private_snapshot(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    reservation, measurement, genesis, token, registry = (
        _v2_fake_launch_case(tmp_path)
    )
    registry = _AcceptOnlyRecorderRegistry([])

    def build(
        opened: launcher.OpenedFloorAttempt,
    ) -> launcher.FloorAttemptTerminal:
        if mutation == "probe":
            opened.probe_before["stderr"] = "builder-forged"
        else:
            perf_raw = opened.repetition_evidence[0]["perf_raw"]
            assert isinstance(perf_raw, dict)
            perf_raw[next(iter(perf_raw))] = 999
        return _v2_terminal_from_opened(
            reservation, opened, session_cv_max="0.10",
        )

    with pytest.raises(
        s8b_terminal_evidence.TerminalEvidenceError,
        match=message,
    ):
        try:
            launcher._launch_floor_attempt_for_test(
                reservation,
                genesis,
                measurement,
                post_probe=_probe,
                classified_at=lambda: "2026-09-08T00:00:01+00:00",
                terminal_builder=build,
                registry=registry,
                capture_measure_point=_capture_token(token),
            )
        finally:
            assert registry.sealed_draft is None
    assert token._rep_sink is not None
    assert token._rep_sink[0]["throughput"] == 100.0


def test_v2_campaign_record_snapshot_is_shared_by_launcher_and_sealer(
    tmp_path: Path,
) -> None:
    reservation, measurement, genesis, token, registry = (
        _v2_fake_launch_case(tmp_path)
    )
    registry = _AcceptOnlyRecorderRegistry([])

    class SplitRecord(Mapping[str, object]):
        def __init__(
            self,
            snapshot_values: dict[str, object],
            launcher_values: dict[str, object],
        ) -> None:
            self.snapshot_values = snapshot_values
            self.launcher_values = launcher_values

        def __iter__(self):
            return iter(self.snapshot_values)

        def __len__(self) -> int:
            return len(self.snapshot_values)

        def __getitem__(self, key: str) -> object:
            return self.snapshot_values[key]

        def get(self, key: str, default: object = None) -> object:
            return self.launcher_values.get(key, default)

    def build(
        opened: launcher.OpenedFloorAttempt,
    ) -> launcher.FloorAttemptTerminal:
        terminal = _v2_terminal_from_opened(
            reservation, opened, session_cv_max="0.10",
        )
        snapshot_values = dict(terminal.campaign_record)
        snapshot_values["duration_s"] = 99.0
        raw = s8b_attempt_profile.serialize_session_line(snapshot_values)
        return replace(
            terminal,
            raw_output_bytes=raw,
            report_sha256=hashlib.sha256(raw).hexdigest(),
            campaign_record=SplitRecord(
                snapshot_values,
                {
                    "duration_s": opened.duration_s,
                    "binary_sha256_at_measure": (
                        opened.binary_sha256_at_measure
                    ),
                },
            ),
        )

    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match="launcher fact: duration_s",
    ):
        try:
            launcher._launch_floor_attempt_for_test(
                reservation,
                genesis,
                measurement,
                post_probe=_probe,
                classified_at=lambda: "2026-09-08T00:00:01+00:00",
                terminal_builder=build,
                registry=registry,
                capture_measure_point=_capture_token(token),
            )
        finally:
            assert registry.sealed_draft is None


def test_test_seam_forwarding_registry_lacks_launcher_origin_capability(
    tmp_path: Path,
) -> None:
    reservation, measurement, genesis, token = _real_v2_launch_case(
        tmp_path
    )

    class ForwardEveryRegistryMethod:
        def __getattr__(self, name: str) -> object:
            return getattr(s8b_attempt_registry, name)

    forwarding_registry = ForwardEveryRegistryMethod()
    with pytest.raises(
        s8b_attempt_registry.S8BAttemptRegistryError,
        match="sealed terminal requires a certified launcher origin",
    ):
        launcher._launch_floor_attempt_for_test(
            reservation,
            genesis,
            measurement,
            post_probe=_probe,
            classified_at=lambda: "2026-09-08T00:00:01+00:00",
            terminal_builder=lambda opened: _v2_terminal_from_opened(
                reservation, opened, session_cv_max="0.10",
            ),
            registry=forwarding_registry,
            capture_measure_point=_capture_token(token),
        )
    rows = s8b_attempt_registry.read_attempt_registry(
        reservation.repo_root,
        profile=reservation.profile,
        binding=reservation.binding,
    )
    assert rows[-1]["event"] == "observation-start"
    evidence_dir = (
        s8b_holdout_admission.shared_admission_root(reservation.repo_root)
        / "floor-attempt-registry-receipts/terminal-evidence"
    )
    assert not evidence_dir.exists()


def test_certified_pre_probe_competing_branch_publishes_sealed_terminal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reservation, measurement, genesis, _token = _real_v2_launch_case(
        tmp_path
    )
    monkeypatch.setattr(
        launcher,
        "_owned_post_probe",
        lambda: _probe(competing=True),
    )
    monkeypatch.setattr(
        launcher,
        "_PRODUCTION_DEPENDENCIES",
        launcher._LauncherDependencies(
            registry=s8b_attempt_registry,
            capture_measure_point=lambda *_args, **_kwargs: pytest.fail(
                "pre-probe competing branch must not capture"
            ),
        ),
    )
    result = launcher.launch_floor_attempt(
        reservation,
        genesis,
        measurement,
        post_probe=launcher.floor_post_probe_capability(),
        classified_at=lambda: "2026-09-08T00:00:01+00:00",
        terminal_builder=lambda opened: _v2_terminal_from_opened(
            reservation, opened, session_cv_max="0.10",
        ),
    )
    assert result.opened.measurement is None
    assert result.opened.probe_after is None
    rows = s8b_attempt_registry.read_attempt_registry(
        reservation.repo_root,
        profile=reservation.profile,
        binding=reservation.binding,
    )
    assert rows[-1]["terminal_status"] == "retryable-failure"
    assert rows[-1]["failure_reason"] == "competing_process"
    assert rows[-1]["measurement_retry_reason"] == (
        "measurement_environment_conflict"
    )
    evidence_path = s8b_attempt_registry._terminal_evidence_path(
        s8b_holdout_admission.shared_admission_root(reservation.repo_root),
        rows[-1]["terminal_evidence_sha256"],
    )
    assert evidence_path.is_file()


def test_timeout_exception_name_is_qualified_only_for_v2_evidence() -> None:
    failure = subprocess.TimeoutExpired(["measure"], timeout=1.0)
    legacy = launcher._failure_evidence("capture", failure)
    sealed = launcher._failure_evidence(
        "capture", failure, qualify_timeout=True,
    )
    assert legacy["exception_type"] == "TimeoutExpired"
    assert sealed["exception_type"] == "subprocess.TimeoutExpired"
    assert legacy["stage"] == sealed["stage"] == "capture"


@pytest.mark.parametrize(
    ("failure", "legacy_name", "sealed_name"),
    (
        (FileNotFoundError(2, "missing"), "FileNotFoundError", "OSError"),
        (PermissionError(13, "denied"), "PermissionError", "OSError"),
        (
            type("CaptureRuntimeSubclass", (RuntimeError,), {})("failed"),
            "CaptureRuntimeSubclass",
            "RuntimeError",
        ),
    ),
)
def test_v2_exception_names_normalize_to_captured_base_categories(
    failure: BaseException,
    legacy_name: str,
    sealed_name: str,
) -> None:
    assert launcher._failure_evidence(
        "capture", failure,
    )["exception_type"] == legacy_name
    assert launcher._failure_evidence(
        "capture", failure, qualify_timeout=True,
    )["exception_type"] == sealed_name


@pytest.mark.parametrize(
    ("failure", "sealed_name"),
    (
        (FileNotFoundError(2, "missing"), "OSError"),
        (PermissionError(13, "denied"), "OSError"),
        (
            type("IssuedRuntimeSubclass", (RuntimeError,), {})("failed"),
            "RuntimeError",
        ),
    ),
)
def test_v2_capture_subclasses_reach_a_sealed_draft(
    tmp_path: Path,
    failure: BaseException,
    sealed_name: str,
) -> None:
    reservation, measurement, genesis, _token, registry = (
        _v2_fake_launch_case(tmp_path)
    )

    def fail_capture(*_args: object, **_kwargs: object) -> object:
        raise failure

    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match="fake registry cannot issue validated evidence",
    ):
        launcher._launch_floor_attempt_for_test(
            reservation,
            genesis,
            measurement,
            post_probe=_probe,
            classified_at=lambda: "2026-09-08T00:00:01+00:00",
            terminal_builder=lambda opened: _v2_terminal_from_opened(
                reservation, opened, session_cv_max="0.10",
            ),
            registry=registry,
            capture_measure_point=fail_capture,
        )
    assert isinstance(
        registry.sealed_draft,
        s8b_terminal_evidence.SealedTerminalEvidenceDraft,
    )
    assert registry.sealed_draft.document["failure"] == {
        "stage": "capture",
        "exception_type": sealed_name,
        "errno": getattr(failure, "errno", None),
    }


def test_v2_open_exception_outside_captured_set_is_not_terminalized(
    tmp_path: Path,
) -> None:
    reservation, measurement, genesis, token, registry = (
        _v2_fake_launch_case(tmp_path)
    )
    token.open_error = ValueError("outside v2 captured set")
    with pytest.raises(ValueError, match="outside v2 captured set"):
        launcher._launch_floor_attempt_for_test(
            reservation,
            genesis,
            measurement,
            post_probe=_probe,
            classified_at=lambda: "2026-09-08T00:00:01+00:00",
            terminal_builder=lambda _opened: pytest.fail(
                "out-of-domain open error must not terminalize"
            ),
            registry=registry,
            capture_measure_point=_capture_token(token),
        )
    assert "sealed-draft" not in registry.events


def test_v2_terminal_builder_can_only_echo_launcher_duration_binary_and_clock(
) -> None:
    terminal = launcher.FloorAttemptTerminal(
        raw_output_bytes=b"{}\n",
        terminal_status="observed",
        report_sha256="1" * 64,
        observation_sha256="2" * 64,
        primary_value=1.0,
        finished_at="2026-09-08T00:00:02+00:00",
        campaign_record={
            "duration_s": 1.25,
            "binary_sha256_at_measure": "3" * 64,
        },
    )
    launcher._assert_v2_terminal_launcher_facts(
        terminal,
        duration_s=1.25,
        finished_at="2026-09-08T00:00:02+00:00",
        binary_sha256_at_measure="3" * 64,
    )
    mutations = (
        (
            replace(
                terminal,
                campaign_record={
                    **terminal.campaign_record,
                    "duration_s": 9.0,
                },
            ),
            "duration_s",
        ),
        (
            replace(
                terminal,
                campaign_record={
                    **terminal.campaign_record,
                    "binary_sha256_at_measure": "4" * 64,
                },
            ),
            "binary_sha256_at_measure",
        ),
        (
            replace(
                terminal,
                finished_at="2099-01-01T00:00:00+00:00",
            ),
            "finished_at",
        ),
    )
    for mutated, message in mutations:
        with pytest.raises(launcher.FloorAttemptLauncherError, match=message):
            launcher._assert_v2_terminal_launcher_facts(
                mutated,
                duration_s=1.25,
                finished_at="2026-09-08T00:00:02+00:00",
                binary_sha256_at_measure="3" * 64,
            )


def test_binary_digest_reader_is_no_follow_and_hashes_exact_bytes(
    tmp_path: Path,
) -> None:
    binary = tmp_path / "binary.exe"
    binary.write_bytes(b"binary-at-measurement")
    expected = hashlib.sha256(b"binary-at-measurement").hexdigest()
    assert launcher._binary_sha256_at_measure(str(binary)) == expected

    alias = tmp_path / "binary-alias.exe"
    alias.symlink_to(binary.name)
    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match="no-follow regular file",
    ):
        launcher._binary_sha256_at_measure(str(alias))

    directory = tmp_path / "binary-directory"
    directory.mkdir()
    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match="no-follow regular file",
    ):
        launcher._binary_sha256_at_measure(str(directory))


def test_certified_wrapper_fixes_the_sealed_adapter_and_exposes_no_registry(
) -> None:
    parameters = inspect.signature(launcher.launch_floor_attempt).parameters
    assert "registry" not in parameters
    assert "sealed_terminal_recorder" not in parameters
    source = inspect.getsource(launcher.launch_floor_attempt)
    assert (
        "sealed_terminal_recorder="
        "attempt_registry.record_sealed_attempt_terminal"
    ) in source


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


def test_probe_floor_attempt_preconditions_runs_owned_probe_once_and_seals_only_competing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def counted_probe() -> dict[str, object]:
        nonlocal calls
        calls += 1
        return _probe(competing=True)

    monkeypatch.setattr(launcher, "_owned_post_probe", counted_probe)
    pre_probe = launcher.probe_floor_attempt_preconditions(
        post_probe=launcher.floor_post_probe_capability(),
    )

    assert calls == 1
    assert type(pre_probe) is launcher.FloorAttemptPreProbe
    assert pre_probe.competing is True
    assert not hasattr(pre_probe, "probe_before")
    assert not hasattr(pre_probe, "raw_probe")
    assert not hasattr(pre_probe, "post_probe")
    assert not hasattr(pre_probe, "capability")


def test_pre_probe_raw_snapshot_is_immutable_and_does_not_consume_seal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_probe = {
        "rc": 0,
        "stdout": "measured competitor output",
        "stderr": "measured probe stderr",
        "competing": True,
    }
    events: list[str] = []
    registry = _RecorderRegistry(events)
    monkeypatch.setattr(launcher, "_owned_post_probe", lambda: raw_probe)
    monkeypatch.setattr(
        launcher,
        "_PRODUCTION_DEPENDENCIES",
        launcher._LauncherDependencies(
            registry=registry,
            capture_measure_point=lambda *_args, **_kwargs: pytest.fail(
                "competing pre-probe must not capture"
            ),
        ),
    )
    pre_probe = launcher.probe_floor_attempt_preconditions(
        post_probe=launcher.floor_post_probe_capability(),
    )

    snapshot = launcher.read_floor_attempt_pre_probe(pre_probe)

    assert dict(snapshot) == raw_probe
    with pytest.raises(TypeError):
        snapshot["stdout"] = "forged"  # type: ignore[index]
    launched = launcher.launch_probed_floor_attempt(
        _reservation(),
        _genesis(),
        _measurement(),
        pre_probe=pre_probe,
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=_terminal,
    )
    assert launched.opened.probe_before == raw_probe


def test_probe_floor_attempt_preconditions_rejects_unissued_capability_without_probe(
) -> None:
    effects: list[str] = []
    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match="launcher-issued fixed capability",
    ):
        launcher.probe_floor_attempt_preconditions(
            post_probe=lambda: effects.append("probe"),  # type: ignore[arg-type]
        )
    assert effects == []


def test_launch_probed_floor_attempt_rejects_reused_pre_probe_before_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    registry = _RecorderRegistry(events)
    monkeypatch.setattr(
        launcher, "_owned_post_probe", lambda: _probe(competing=True),
    )
    monkeypatch.setattr(
        launcher,
        "_PRODUCTION_DEPENDENCIES",
        launcher._LauncherDependencies(
            registry=registry,
            capture_measure_point=lambda *_args, **_kwargs: pytest.fail(
                "competing pre-probe must not capture"
            ),
        ),
    )
    pre_probe = launcher.probe_floor_attempt_preconditions(
        post_probe=launcher.floor_post_probe_capability(),
    )
    launcher.launch_probed_floor_attempt(
        _reservation(),
        _genesis(),
        _measurement(),
        pre_probe=pre_probe,
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=_terminal,
    )
    effects_after_first_launch = list(events)

    with pytest.raises(
        launcher.FloorAttemptLauncherError,
        match="one-shot and was already used",
    ):
        launcher.launch_probed_floor_attempt(
            _reservation(),
            _genesis(),
            _measurement(),
            pre_probe=pre_probe,
            classified_at=lambda: "2026-08-26T00:00:01+00:00",
            terminal_builder=_terminal,
        )
    assert events == effects_after_first_launch


@pytest.mark.parametrize(
    "unissued_pre_probe",
    (
        pytest.param(launcher.FloorAttemptPreProbe(), id="caller-constructed"),
        pytest.param(
            type(
                "FloorAttemptPreProbe",
                (),
                {"competing": False},
            )(),
            id="spoofed-type",
        ),
    ),
)
def test_launch_probed_floor_attempt_rejects_unissued_or_spoofed_pre_probe(
    monkeypatch: pytest.MonkeyPatch,
    unissued_pre_probe: object,
) -> None:
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
        match="launcher-issued sealed pre-probe",
    ):
        launcher.launch_probed_floor_attempt(
            _reservation(),
            _genesis(),
            _measurement(),
            pre_probe=unissued_pre_probe,  # type: ignore[arg-type]
            classified_at=lambda: "2026-08-26T00:00:01+00:00",
            terminal_builder=_terminal,
        )


def test_launch_probed_floor_attempt_rejects_a_different_capability_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def first_owned_probe() -> dict[str, object]:
        return _probe()

    def replacement_owned_probe() -> dict[str, object]:
        return _probe()

    monkeypatch.setattr(launcher, "_owned_post_probe", first_owned_probe)
    pre_probe = launcher.probe_floor_attempt_preconditions(
        post_probe=launcher.floor_post_probe_capability(),
    )
    monkeypatch.setattr(launcher, "_owned_post_probe", replacement_owned_probe)
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
        launcher.launch_probed_floor_attempt(
            _reservation(),
            _genesis(),
            _measurement(),
            pre_probe=pre_probe,
            classified_at=lambda: "2026-08-26T00:00:01+00:00",
            terminal_builder=_terminal,
        )


def test_launch_probed_floor_attempt_does_not_repeat_pre_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def counted_probe() -> dict[str, object]:
        nonlocal calls
        calls += 1
        return _probe()

    events: list[str] = []
    registry = _RecorderRegistry(events)
    token = _Token(events)
    monkeypatch.setattr(launcher, "_owned_post_probe", counted_probe)
    monkeypatch.setattr(
        launcher,
        "_PRODUCTION_DEPENDENCIES",
        launcher._LauncherDependencies(
            registry=registry,
            capture_measure_point=_capture_token(token, record=True),
        ),
    )
    pre_probe = launcher.probe_floor_attempt_preconditions(
        post_probe=launcher.floor_post_probe_capability(),
    )
    assert calls == 1

    result = launcher.launch_probed_floor_attempt(
        _reservation(),
        _genesis(),
        _measurement(),
        pre_probe=pre_probe,
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=_terminal,
    )

    assert calls == 2
    assert result.opened.probe_before == _probe()
    assert result.opened.probe_after == _probe()
    assert events.count("capture") == 1


def test_launch_probed_clean_matches_existing_terminal_and_classification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing_root = tmp_path / "existing"
    probed_root = tmp_path / "probed"
    existing_root.mkdir()
    probed_root.mkdir()
    existing_case = _real_v2_launch_case(existing_root)
    probed_case = _real_v2_launch_case(probed_root)
    (
        existing_reservation,
        existing_measurement,
        existing_genesis,
        existing_token,
    ) = existing_case
    (
        probed_reservation,
        probed_measurement,
        probed_genesis,
        probed_token,
    ) = probed_case
    monotonic_values = iter((10.0, 12.0, 10.0, 12.0))
    monkeypatch.setattr(launcher.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(launcher, "_owned_post_probe", _probe)

    monkeypatch.setattr(
        launcher,
        "_PRODUCTION_DEPENDENCIES",
        launcher._LauncherDependencies(
            s8b_attempt_registry, _capture_token(existing_token),
        ),
    )
    existing = launcher.launch_floor_attempt(
        existing_reservation,
        existing_genesis,
        existing_measurement,
        post_probe=launcher.floor_post_probe_capability(),
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=lambda opened: _v2_terminal_from_opened(
            existing_reservation, opened, session_cv_max="0.10",
        ),
    )

    monkeypatch.setattr(
        launcher,
        "_PRODUCTION_DEPENDENCIES",
        launcher._LauncherDependencies(
            s8b_attempt_registry, _capture_token(probed_token),
        ),
    )
    pre_probe = launcher.probe_floor_attempt_preconditions(
        post_probe=launcher.floor_post_probe_capability(),
    )
    probed = launcher.launch_probed_floor_attempt(
        probed_reservation,
        probed_genesis,
        probed_measurement,
        pre_probe=pre_probe,
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=lambda opened: _v2_terminal_from_opened(
            probed_reservation, opened, session_cv_max="0.10",
        ),
    )

    assert probed.terminal == existing.terminal
    assert replace(probed.opened, measurement=None) == replace(
        existing.opened, measurement=None,
    )
    existing_rows = s8b_attempt_registry.read_attempt_registry(
        existing_reservation.repo_root,
        profile=existing_reservation.profile,
        binding=existing_reservation.binding,
    )
    probed_rows = s8b_attempt_registry.read_attempt_registry(
        probed_reservation.repo_root,
        profile=probed_reservation.profile,
        binding=probed_reservation.binding,
    )
    assert probed_rows == existing_rows
    assert probed_rows[-1]["terminal_status"] == "observed"
    assert probed_rows[-1]["terminal_evidence_sha256"]


def test_launch_probed_competing_skips_capture_and_matches_existing_terminal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing_root = tmp_path / "existing"
    probed_root = tmp_path / "probed"
    existing_root.mkdir()
    probed_root.mkdir()
    (
        existing_reservation,
        existing_measurement,
        existing_genesis,
        _existing_token,
    ) = _real_v2_launch_case(existing_root)
    (
        probed_reservation,
        probed_measurement,
        probed_genesis,
        _probed_token,
    ) = _real_v2_launch_case(probed_root)
    monotonic_values = iter((10.0, 12.0, 10.0, 12.0))
    monkeypatch.setattr(launcher.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(
        launcher, "_owned_post_probe", lambda: _probe(competing=True),
    )

    monkeypatch.setattr(
        launcher,
        "_PRODUCTION_DEPENDENCIES",
        launcher._LauncherDependencies(
            s8b_attempt_registry,
            lambda *_args, **_kwargs: pytest.fail(
                "competing pre-probe must not capture"
            ),
        ),
    )
    existing = launcher.launch_floor_attempt(
        existing_reservation,
        existing_genesis,
        existing_measurement,
        post_probe=launcher.floor_post_probe_capability(),
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=lambda opened: _v2_terminal_from_opened(
            existing_reservation, opened, session_cv_max="0.10",
        ),
    )

    monkeypatch.setattr(
        launcher,
        "_PRODUCTION_DEPENDENCIES",
        launcher._LauncherDependencies(
            s8b_attempt_registry,
            lambda *_args, **_kwargs: pytest.fail(
                "competing pre-probe must not capture"
            ),
        ),
    )
    pre_probe = launcher.probe_floor_attempt_preconditions(
        post_probe=launcher.floor_post_probe_capability(),
    )
    probed = launcher.launch_probed_floor_attempt(
        probed_reservation,
        probed_genesis,
        probed_measurement,
        pre_probe=pre_probe,
        classified_at=lambda: "2026-08-26T00:00:01+00:00",
        terminal_builder=lambda opened: _v2_terminal_from_opened(
            probed_reservation, opened, session_cv_max="0.10",
        ),
    )

    assert probed.terminal == existing.terminal
    assert replace(probed.opened, measurement=None) == replace(
        existing.opened, measurement=None,
    )
    assert probed.opened.measurement is None
    assert probed.opened.probe_before["competing"] is True
    assert probed.opened.probe_after is None
    existing_rows = s8b_attempt_registry.read_attempt_registry(
        existing_reservation.repo_root,
        profile=existing_reservation.profile,
        binding=existing_reservation.binding,
    )
    probed_rows = s8b_attempt_registry.read_attempt_registry(
        probed_reservation.repo_root,
        profile=probed_reservation.profile,
        binding=probed_reservation.binding,
    )
    assert probed_rows == existing_rows
    assert probed_rows[-1]["terminal_status"] == "retryable-failure"
    assert probed_rows[-1]["failure_reason"] == "competing_process"
    assert probed_rows[-1]["measurement_retry_reason"] == (
        "measurement_environment_conflict"
    )


def test_probed_certified_wrapper_fixes_sealed_adapter_and_public_signatures(
) -> None:
    probe_parameters = inspect.signature(
        launcher.probe_floor_attempt_preconditions
    ).parameters
    assert tuple(probe_parameters) == ("post_probe",)
    assert probe_parameters["post_probe"].kind is inspect.Parameter.KEYWORD_ONLY

    launch_parameters = inspect.signature(
        launcher.launch_probed_floor_attempt
    ).parameters
    assert tuple(launch_parameters) == (
        "reservation",
        "registry_genesis",
        "measurement",
        "pre_probe",
        "classified_at",
        "terminal_builder",
    )
    assert launch_parameters["pre_probe"].kind is inspect.Parameter.KEYWORD_ONLY
    assert "registry" not in launch_parameters
    assert "sealed_terminal_recorder" not in launch_parameters
    source = inspect.getsource(launcher.launch_probed_floor_attempt)
    assert (
        "sealed_terminal_recorder="
        "attempt_registry.record_sealed_attempt_terminal"
    ) in source


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", str(Path(__file__).resolve())]))
