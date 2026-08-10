# -*- coding: utf-8 -*-
"""tools/dev_wave_wait.py の canonical waiter 契約テスト。"""
from __future__ import annotations

import errno
import importlib.util
import json
import os
import signal
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


_ROOT = Path(__file__).resolve().parents[2]
_TOOL = _ROOT / "tools" / "dev_wave_wait.py"
_LEASE_HELPER = _ROOT / "tools" / "wave_land_window.py"
_SPEC = importlib.util.spec_from_file_location("dev_wave_wait_under_test", _TOOL)
assert _SPEC and _SPEC.loader
DW = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = DW
_SPEC.loader.exec_module(DW)

_SHA_A = "a" * 40
_SHA_B = "b" * 40
_SHA_C = "c" * 40
_WAVE = "wave-test"
_REPO = Path("/repo")
_LEASE = Path("/lease")
_MESSAGE = Path("/message.txt")
_VALIDATED_MESSAGE = Path("/validated-message.txt")
_COMMAND = ("harmless-command", "--flag")
_RELEASE_JSON = json.dumps({"state": "released"})


def _stat_text(pid: int, start_time: int) -> str:
    fields = ["S", *("0" for _ in range(18)), str(start_time), "0"]
    return f"{pid} (worker name) " + " ".join(fields)


class _FakeEffects:
    def __init__(self) -> None:
        self.events: list[tuple[object, ...]] = []
        self.run_queue: list[tuple[tuple[str, ...], bool, object]] = []
        self.kill_queue: list[object] = []
        self.is_file_queue: list[tuple[Path, object]] = []
        self.read_text_queue: list[tuple[Path, object]] = []
        self.monotonic_queue: list[float] = []
        self.env: dict[str, str] = {}
        self.temp_path = _VALIDATED_MESSAGE

    @property
    def effects(self) -> object:
        return DW._Effects(
            run=self.run,
            run_unbounded=self.run,
            sleep=self.sleep,
            kill=self.kill,
            is_file=self.is_file,
            read_text=self.read_text,
            getenv=self.getenv,
            monotonic=self.monotonic,
            write_temp=self.write_temp,
            unlink=self.unlink,
        )

    def expect_run(
        self,
        argv: tuple[str, ...],
        result: object = None,
        *,
        capture: bool = True,
    ) -> None:
        if result is None:
            result = DW._CommandResult(0)
        self.run_queue.append((argv, capture, result))

    def run(self, argv: object, cwd: Path, capture: bool) -> object:
        actual = tuple(argv)
        self.events.append(("run", actual, cwd, capture))
        assert self.run_queue, f"unexpected run: {actual}"
        expected, expected_capture, result = self.run_queue.pop(0)
        assert actual == expected
        assert capture is expected_capture
        if isinstance(result, BaseException):
            raise result
        return result

    def sleep(self, seconds: float) -> None:
        self.events.append(("sleep", seconds))

    def kill(self, pid: int, signum: int) -> None:
        self.events.append(("kill", pid, signum))
        result = self.kill_queue.pop(0)
        if isinstance(result, BaseException):
            raise result

    def is_file(self, path: Path) -> bool:
        self.events.append(("is_file", path))
        assert self.is_file_queue, f"unexpected is_file: {path}"
        expected, result = self.is_file_queue.pop(0)
        assert path == expected
        if isinstance(result, BaseException):
            raise result
        return bool(result)

    def read_text(self, path: Path) -> str:
        self.events.append(("read_text", path))
        assert self.read_text_queue, f"unexpected read_text: {path}"
        expected, result = self.read_text_queue.pop(0)
        assert path == expected
        if isinstance(result, BaseException):
            raise result
        return str(result)

    def getenv(self, name: str) -> str | None:
        self.events.append(("getenv", name))
        return self.env.get(name)

    def monotonic(self) -> float:
        self.events.append(("monotonic",))
        return self.monotonic_queue.pop(0) if self.monotonic_queue else 0.0

    def write_temp(self, content: bytes) -> Path:
        self.events.append(("write_temp", content))
        return self.temp_path

    def unlink(self, path: Path) -> None:
        self.events.append(("unlink", path))

    def assert_drained(
        self, expected_events: list[tuple[object, ...]] | None = None
    ) -> None:
        if expected_events is not None:
            assert self.events == expected_events
        assert self.run_queue == []
        assert self.kill_queue == []
        assert self.is_file_queue == []
        assert self.read_text_queue == []
        assert self.monotonic_queue == []


def _helper(action: str, sha: str | None = None) -> tuple[str, ...]:
    argv = (
        sys.executable,
        str(_REPO / "tools" / "wave_land_window.py"),
        action,
        "--lease-dir",
        str(_LEASE),
        "--wave",
        _WAVE,
    )
    return argv + (("--main-sha", sha) if sha is not None else ())


def _preflight(fake: _FakeEffects) -> None:
    fake.expect_run(
        ("git", "rev-parse", "--is-inside-work-tree"),
        DW._CommandResult(0, "true\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "--show-toplevel"),
        DW._CommandResult(0, str(_REPO) + "\n"),
    )
    fake.expect_run(
        ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
        DW._CommandResult(0, f"feature-{_WAVE}\n"),
    )
    fake.expect_run(
        ("git", "status", "--porcelain", "--untracked-files=no"),
        DW._CommandResult(0, ""),
    )


_PREFLIGHT_EVENTS = [
    ("run", ("git", "rev-parse", "--is-inside-work-tree"), _REPO, True),
    ("run", ("git", "rev-parse", "--show-toplevel"), _REPO, True),
    ("run", ("git", "symbolic-ref", "--quiet", "--short", "HEAD"), _REPO, True),
    ("run", ("git", "status", "--porcelain", "--untracked-files=no"), _REPO, True),
]


def _claim(fake: _FakeEffects, sha: str, payload: str) -> None:
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, sha + "\n"))
    fake.expect_run(_helper("claim", sha), DW._CommandResult(0, payload))


def _acquired(fake: _FakeEffects, sha: str = _SHA_A) -> None:
    _claim(fake, sha, json.dumps({"state": "acquired"}))


def _release(fake: _FakeEffects, result: object = None) -> None:
    fake.expect_run(
        _helper("release"),
        DW._CommandResult(0, _RELEASE_JSON) if result is None else result,
    )


def _abort_clean(fake: _FakeEffects, result: object = None) -> None:
    fake.expect_run(
        ("git", "merge", "--abort"),
        DW._CommandResult(0) if result is None else result,
    )
    fake.expect_run(
        ("git", "rev-parse", "-q", "--verify", "MERGE_HEAD"),
        DW._CommandResult(1),
    )
    fake.expect_run(
        ("git", "status", "--porcelain", "--untracked-files=no"),
        DW._CommandResult(0, ""),
    )


_ABORT_CLEAN_EVENTS = [
    ("run", ("git", "merge", "--abort"), _REPO, True),
    (
        "run",
        ("git", "rev-parse", "-q", "--verify", "MERGE_HEAD"),
        _REPO,
        True,
    ),
    (
        "run",
        ("git", "status", "--porcelain", "--untracked-files=no"),
        _REPO,
        True,
    ),
]


def _run_acceptance(
    fake: _FakeEffects,
    *,
    message: Path | None = None,
    max_wait: int = 7200,
    owned_paths: tuple[Path, ...] = (),
) -> object:
    return DW.run_acceptance(
        wave=_WAVE,
        lease_dir=_LEASE,
        merge_message_file=message,
        poll_seconds=30,
        max_wait_seconds=max_wait,
        command=_COMMAND,
        repo=_REPO,
        effects=fake.effects,
        owned_paths=owned_paths,
    )


class _RoutingAcceptanceEffects(_FakeEffects):
    def __init__(
        self,
        *,
        branch: str = f"feature-{_WAVE}",
        behind: list[int] | None = None,
        message: str = "merge\nAI-Agent: codex\n",
        head_shas: list[str] | None = None,
        changed_paths: str = "",
    ) -> None:
        super().__init__()
        self.branch = branch
        self.behind = list([0] if behind is None else behind)
        self.message = message
        self.head_shas = list([] if head_shas is None else head_shas)
        self.changed_paths = changed_paths
        self.claims = 0
        self.releases = 0
        self.submissions = 0

    def run(self, argv: object, cwd: Path, capture: bool) -> object:
        actual = tuple(argv)
        self.events.append(("run", actual, cwd, capture))
        if actual == ("git", "rev-parse", "--is-inside-work-tree"):
            return DW._CommandResult(0, "true\n")
        if actual == ("git", "rev-parse", "--show-toplevel"):
            return DW._CommandResult(0, str(_REPO) + "\n")
        if actual == ("git", "symbolic-ref", "--quiet", "--short", "HEAD"):
            return DW._CommandResult(0, self.branch + "\n")
        if actual == ("git", "status", "--porcelain", "--untracked-files=no"):
            return DW._CommandResult(0, "")
        if actual == ("git", "rev-parse", "main"):
            return DW._CommandResult(0, _SHA_A + "\n")
        if actual == _helper("claim", _SHA_A):
            self.claims += 1
            return DW._CommandResult(0, '{"state":"acquired"}')
        if actual == ("git", "rev-list", "--count", "HEAD..main"):
            assert self.behind
            return DW._CommandResult(0, f"{self.behind.pop(0)}\n")
        if actual == ("git", "diff", "--name-only", "HEAD...main"):
            return DW._CommandResult(0, self.changed_paths)
        if actual in {
            ("git", "merge", "--no-ff", "--no-commit", "main"),
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
        }:
            return DW._CommandResult(0)
        if actual == ("git", "rev-parse", "HEAD"):
            assert self.head_shas
            return DW._CommandResult(0, self.head_shas.pop(0) + "\n")
        if actual[:4] == ("git", "log", "-1", "--format=%B"):
            return DW._CommandResult(0, self.message)
        if actual == _COMMAND:
            self.submissions += 1
            return DW._CommandResult(0)
        if actual == _helper("release"):
            self.releases += 1
            return DW._CommandResult(0, _RELEASE_JSON)
        raise AssertionError(f"unexpected run: {actual}")

    def is_file(self, path: Path) -> bool:
        self.events.append(("is_file", path))
        return True

    def read_text(self, path: Path) -> str:
        self.events.append(("read_text", path))
        return self.message


def test_pid_probe_calls_kill_zero_for_exact_pid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pid = 4321
    subprocesses: list[tuple[object, ...]] = []
    events: list[tuple[object, ...]] = []

    def run(argv: object, cwd: Path, capture: bool) -> object:
        subprocesses.append((tuple(argv), cwd, capture))
        return DW._CommandResult(1)

    def direct_run(argv: object, **kwargs: object) -> object:
        subprocesses.append((tuple(argv), kwargs))
        return subprocess.CompletedProcess(argv, 1, "", "")

    monkeypatch.setattr(DW.subprocess, "run", direct_run)

    def read_text(path: Path) -> str:
        events.append(("read_text", path))
        return _stat_text(pid, 9)

    def kill(actual_pid: int, signum: int) -> None:
        events.append(("kill", actual_pid, signum))
        raise ProcessLookupError(errno.ESRCH, "gone")

    def is_file(path: Path) -> bool:
        events.append(("is_file", path))
        return True

    effects = DW._Effects(
        run=run, run_unbounded=run, sleep=lambda seconds: events.append(("sleep", seconds)),
        kill=kill, is_file=is_file, read_text=read_text,
        getenv=lambda name: None, monotonic=lambda: events.append(("monotonic",)) or 0.0,
        write_temp=lambda content: _VALIDATED_MESSAGE, unlink=lambda path: None,
    )

    outcome = DW.wait_for_producer(
        done_file=Path("done"),
        artifact_file=Path("artifact"),
        pid=pid,
        max_wait_seconds=None,
        effects=effects,
    )

    assert outcome.rc == 0
    assert subprocesses == []
    assert events == [
        ("monotonic",),
        ("read_text", Path(f"/proc/{pid}/stat")),
        ("kill", pid, 0),
        ("is_file", Path("done")),
        ("is_file", Path("artifact")),
    ]


def test_producer_waits_while_pid_alive_then_completes_after_death() -> None:
    fake = _FakeEffects()
    pid = 42
    stat_path = Path(f"/proc/{pid}/stat")
    fake.read_text_queue.extend(
        [(stat_path, _stat_text(pid, 11)), (stat_path, _stat_text(pid, 11))]
    )
    fake.kill_queue.extend([None, ProcessLookupError(errno.ESRCH, "gone")])
    fake.is_file_queue.extend([(Path("done"), True), (Path("artifact"), True)])

    outcome = DW.wait_for_producer(
        done_file=Path("done"),
        artifact_file=Path("artifact"),
        pid=pid,
        max_wait_seconds=None,
        effects=fake.effects,
    )

    assert outcome.rc == 0
    assert fake.events.count(("sleep", 5)) == 1
    fake.assert_drained()


@pytest.mark.parametrize("missing", ["done", "artifact"], ids=("done", "artifact"))
def test_producer_dead_without_required_file_fails_closed(missing: str) -> None:
    fake = _FakeEffects()
    pid = 55
    fake.read_text_queue.append((Path(f"/proc/{pid}/stat"), OSError("no proc")))
    fake.kill_queue.append(ProcessLookupError(errno.ESRCH, "gone"))
    for _ in range(7):
        fake.is_file_queue.append((Path("done"), missing != "done"))
        if missing != "done":
            fake.is_file_queue.append((Path("artifact"), False))

    outcome = DW.wait_for_producer(
        done_file=Path("done"),
        artifact_file=Path("artifact"),
        pid=pid,
        max_wait_seconds=None,
        effects=fake.effects,
    )

    assert outcome.rc == 70
    assert outcome.stage == "producer-files"
    file_events = [("is_file", Path("done"))]
    if missing == "artifact":
        file_events.append(("is_file", Path("artifact")))
    expected = [
        ("monotonic",),
        ("read_text", Path(f"/proc/{pid}/stat")),
        ("kill", pid, 0),
    ]
    for attempt in range(7):
        expected.extend(file_events)
        if attempt < 6:
            expected.append(("sleep", 5))
    fake.assert_drained(expected)


@pytest.mark.parametrize("source", ["direct", "pid-file"], ids=("direct", "pid-file"))
def test_producer_accepts_exactly_one_pid_source(source: str) -> None:
    fake = _FakeEffects()
    if source == "pid-file":
        fake.read_text_queue.append((Path("pid"), "123\n"))
    resolved = DW._resolve_pid(
        "123" if source == "direct" else None,
        Path("pid") if source == "pid-file" else None,
        fake.effects,
    )
    assert resolved == 123
    fake.assert_drained()


@pytest.mark.parametrize("source", ["neither", "both"], ids=("neither", "both"))
def test_producer_rejects_invalid_pid_source(source: str) -> None:
    fake = _FakeEffects()
    with pytest.raises(DW._StageFailure) as raised:
        DW._resolve_pid(
            "123" if source == "both" else None,
            Path("pid") if source == "both" else None,
            fake.effects,
        )
    assert raised.value.outcome.rc == 2
    fake.assert_drained([])


def test_producer_cli_surface_has_no_pattern_input(capsys: pytest.CaptureFixture[str]) -> None:
    parser = DW._producer_parser()
    expected_options = {
        "-h",
        "--help",
        "--done-file",
        "--artifact-file",
        "--pid",
        "--pid-file",
        "--max-wait-seconds",
    }
    actual_options = {
        option
        for action in parser._actions
        for option in action.option_strings
    }
    positional_actions = [action for action in parser._actions if not action.option_strings]
    assert actual_options == expected_options
    assert positional_actions == []

    base = ["producer", "--done-file", "d", "--artifact-file", "a", "--pid", "1"]
    for extra in (["--pattern", "X"], ["--match", "X"], ["unexpected"]):
        assert DW.main(base + extra) == 2
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Traceback" not in captured.err


def test_producer_start_time_change_is_original_process_death() -> None:
    fake = _FakeEffects()
    pid = 99
    stat_path = Path(f"/proc/{pid}/stat")
    fake.read_text_queue.extend(
        [(stat_path, _stat_text(pid, 1)), (stat_path, _stat_text(pid, 2))]
    )
    fake.kill_queue.append(None)
    fake.is_file_queue.extend([(Path("done"), True), (Path("artifact"), True)])
    outcome = DW.wait_for_producer(
        done_file=Path("done"), artifact_file=Path("artifact"), pid=pid,
        max_wait_seconds=None, effects=fake.effects,
    )
    assert outcome.rc == 0
    assert ("sleep", 5) not in fake.events
    fake.assert_drained()


def test_producer_zombie_is_dead_even_when_kill_zero_succeeds() -> None:
    fake = _FakeEffects()
    pid = 101
    stat_path = Path(f"/proc/{pid}/stat")
    fake.read_text_queue.extend(
        [(stat_path, _stat_text(pid, 7)), (stat_path, _stat_text(pid, 7).replace(" S ", " Z ", 1))]
    )
    fake.kill_queue.append(None)
    fake.is_file_queue.extend([(Path("done"), True), (Path("artifact"), True)])

    outcome = DW.wait_for_producer(
        done_file=Path("done"), artifact_file=Path("artifact"), pid=pid,
        max_wait_seconds=None, effects=fake.effects,
    )

    assert outcome.rc == 0
    assert ("sleep", 5) not in fake.events
    fake.assert_drained()


def test_producer_file_visibility_grace_is_bounded() -> None:
    fake = _FakeEffects()
    pid = 100
    fake.read_text_queue.append((Path(f"/proc/{pid}/stat"), OSError("no proc")))
    fake.kill_queue.append(ProcessLookupError(errno.ESRCH, "gone"))
    fake.is_file_queue.extend(
        [
            (Path("done"), False),
            (Path("done"), True),
            (Path("artifact"), False),
            (Path("done"), True),
            (Path("artifact"), True),
        ]
    )
    outcome = DW.wait_for_producer(
        done_file=Path("done"), artifact_file=Path("artifact"), pid=pid,
        max_wait_seconds=None, effects=fake.effects,
    )
    assert outcome.rc == 0
    assert fake.events.count(("sleep", 5)) == 2
    fake.assert_drained()


@pytest.mark.parametrize(
    "state", ["held", "queued", "stale-held", "unavailable"],
    ids=("held", "queued", "stale-held", "unavailable"),
)
def test_acceptance_non_acquired_state_never_runs_command(state: str) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _claim(fake, _SHA_A, json.dumps({"state": state}))
    if state in {"held", "queued"}:
        fake.monotonic_queue[:] = [0.0, 0.0]
    outcome = _run_acceptance(fake, max_wait=1)

    assert outcome.rc == 70
    expected = [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
    ]
    if state in {"held", "queued"}:
        expected.append(("monotonic",))
    assert fake.events == expected
    fake.assert_drained()


def test_acceptance_ignores_acquired_outside_top_level_state() -> None:
    payload = json.dumps(
        {"state": "held", "diagnostic": "acquired", "nested": {"state": "acquired"}}
    )

    class RoutingEffects(_FakeEffects):
        def __init__(self) -> None:
            super().__init__()
            self.submissions = 0

        def run(self, argv: object, cwd: Path, capture: bool) -> object:
            actual = tuple(argv)
            self.events.append(("run", actual, cwd, capture))
            if actual == ("git", "rev-parse", "--is-inside-work-tree"):
                return DW._CommandResult(0, "true\n")
            if actual == ("git", "rev-parse", "--show-toplevel"):
                return DW._CommandResult(0, str(_REPO) + "\n")
            if actual == ("git", "symbolic-ref", "--quiet", "--short", "HEAD"):
                return DW._CommandResult(0, f"feature-{_WAVE}\n")
            if actual == ("git", "status", "--porcelain", "--untracked-files=no"):
                return DW._CommandResult(0, "")
            if actual == ("git", "rev-parse", "main"):
                return DW._CommandResult(0, _SHA_A + "\n")
            if actual == _helper("claim", _SHA_A):
                return DW._CommandResult(0, payload)
            if actual == ("git", "rev-list", "--count", "HEAD..main"):
                return DW._CommandResult(0, "0\n")
            if actual == _COMMAND:
                self.submissions += 1
                return DW._CommandResult(0)
            if actual == _helper("release"):
                return DW._CommandResult(0, _RELEASE_JSON)
            raise AssertionError(f"unexpected run: {actual}")

    fake = RoutingEffects()
    _run_acceptance(fake, max_wait=1)

    assert fake.submissions == 0


def test_claim_once_uses_only_exact_top_level_state() -> None:
    fake = _FakeEffects()
    payload = json.dumps(
        {"state": "held", "diagnostic": "acquired", "nested": {"state": "acquired"}}
    )
    fake.expect_run(_helper("claim", _SHA_A), DW._CommandResult(0, payload))

    state = DW._claim_once(fake.effects, _REPO, _LEASE, _WAVE, _SHA_A)

    assert state == "held"
    assert fake.events == [("run", _helper("claim", _SHA_A), _REPO, True)]
    fake.assert_drained()


@pytest.mark.parametrize(
    ("case", "payload"),
    [
        ("malformed", "{"),
        ("duplicate-state", '{"state":"acquired","state":"held"}'),
        ("unknown-state", '{"state":"free"}'),
        ("non-string-state", '{"state":7}'),
        ("array", '["acquired"]'),
        ("scalar", '"acquired"'),
    ],
    ids=(
        "malformed", "duplicate-state", "unknown-state", "non-string-state",
        "array", "scalar",
    ),
)
def test_acceptance_rejects_claim_json(case: str, payload: str) -> None:
    del case
    fake = _FakeEffects()
    _preflight(fake)
    _claim(fake, _SHA_A, payload)
    _release(fake)
    outcome = _run_acceptance(fake)
    assert outcome.rc == 70
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


def test_held_and_queued_refresh_main_before_every_claim() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.monotonic_queue[:] = [0.0, 0.0, 30.0]
    _claim(fake, _SHA_A, '{"state":"held"}')
    _claim(fake, _SHA_B, '{"state":"queued"}')
    _claim(fake, _SHA_C, '{"state":"acquired"}')
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_C + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    outcome = _run_acceptance(fake)
    assert outcome.rc == 0
    claim_shas = [
        event[1][-1]
        for event in fake.events
        if event[0] == "run" and len(event[1]) > 2 and event[1][2] == "claim"
    ]
    assert claim_shas == [_SHA_A, _SHA_B, _SHA_C]
    assert fake.events.count(("sleep", 30)) == 2
    assert not any(event[0] == "run" and event[1] == _helper("release") for event in fake.events)
    fake.assert_drained()


def test_acquired_reloads_main_before_behind_check() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake, _SHA_A)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    outcome = _run_acceptance(fake)
    assert outcome.rc == 0
    rev_parse_outputs = [
        event for event in fake.events
        if event[0] == "run" and event[1] == ("git", "rev-parse", "main")
    ]
    assert len(rev_parse_outputs) == 2
    fake.assert_drained()


def test_merge_required_without_message_file_releases_before_submission() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "1\n"))
    _release(fake)
    outcome = _run_acceptance(fake)
    assert outcome.rc == 70
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


@pytest.mark.parametrize(
    ("owned_path", "changed_path"),
    [
        (Path("./docs/x.md"), "docs/x.md"),
        (Path("docs"), "docs/sub/x.md"),
    ],
    ids=("normalized-exact", "directory-child"),
)
def test_owned_path_overlap_blocks_before_merge_and_releases(
    owned_path: Path,
    changed_path: str,
) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.is_file_queue.append((_MESSAGE, True))
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "1\n"),
    )
    fake.expect_run(
        ("git", "diff", "--name-only", "HEAD...main"),
        DW._CommandResult(0, changed_path + "\n"),
    )
    _release(fake)

    outcome = _run_acceptance(
        fake,
        message=_MESSAGE,
        owned_paths=(owned_path,),
    )

    assert outcome.rc == 70
    assert outcome.stage == "owned-path-overlap"
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        (
            "run",
            ("git", "rev-list", "--count", "HEAD..main"),
            _REPO,
            True,
        ),
        (
            "run",
            ("git", "diff", "--name-only", "HEAD...main"),
            _REPO,
            True,
        ),
        ("run", _helper("release"), _REPO, True),
    ]
    assert not any(
        event[0] == "run" and event[1][:2] == ("git", "merge")
        for event in fake.events
    )
    assert not any(
        event[0] == "run" and event[1] == _COMMAND for event in fake.events
    )
    fake.assert_drained()


def test_owned_path_diff_nonzero_fails_closed_and_releases() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.is_file_queue.append((_MESSAGE, True))
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "1\n"),
    )
    fake.expect_run(
        ("git", "diff", "--name-only", "HEAD...main"),
        DW._CommandResult(9),
    )
    _release(fake)

    outcome = _run_acceptance(
        fake,
        message=_MESSAGE,
        owned_paths=(Path("docs/x.md"),),
    )

    assert outcome.rc == 70
    assert outcome.stage == "owned-path-diff"
    assert outcome.source_rc == 9
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        (
            "run",
            ("git", "rev-list", "--count", "HEAD..main"),
            _REPO,
            True,
        ),
        (
            "run",
            ("git", "diff", "--name-only", "HEAD...main"),
            _REPO,
            True,
        ),
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


def test_owned_path_prefix_is_not_overlap_and_reaches_submission() -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1, 0],
        head_shas=[_SHA_C, _SHA_C],
        changed_paths="docs/xy.md\n",
    )

    outcome = _run_acceptance(
        fake,
        message=_MESSAGE,
        owned_paths=(Path("docs/x.md"),),
    )

    assert outcome.rc == 0
    assert (fake.claims, fake.submissions, fake.releases) == (1, 1, 0)
    selected_calls = [
        event[1]
        for event in fake.events
        if event[0] == "run"
        and event[1]
        in {
            ("git", "diff", "--name-only", "HEAD...main"),
            ("git", "merge", "--no-ff", "--no-commit", "main"),
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
            _COMMAND,
        }
    ]
    assert selected_calls == [
        ("git", "diff", "--name-only", "HEAD...main"),
        ("git", "merge", "--no-ff", "--no-commit", "main"),
        ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
        ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
        _COMMAND,
    ]


def test_missing_owned_path_skips_diff_warns_and_reaches_submission(
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1, 0],
        head_shas=[_SHA_C, _SHA_C],
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 0
    assert (fake.claims, fake.submissions, fake.releases) == (1, 1, 0)
    assert not any(
        event[0] == "run"
        and event[1] == ("git", "diff", "--name-only", "HEAD...main")
        for event in fake.events
    )
    selected_calls = [
        event[1]
        for event in fake.events
        if event[0] == "run"
        and event[1]
        in {
            ("git", "merge", "--no-ff", "--no-commit", "main"),
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
            _COMMAND,
        }
    ]
    assert selected_calls == [
        ("git", "merge", "--no-ff", "--no-commit", "main"),
        ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
        ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
        _COMMAND,
    ]
    warning = (
        "acceptance: --owned-path 未指定のため所有実装面 overlap 判定を省略します"
    )
    assert capsys.readouterr().err.splitlines().count(warning) == 1


def test_missing_message_preflight_does_not_release_foreign_lease() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.is_file_queue.append((_MESSAGE, False))

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 2
    assert outcome.stage == "merge-message-preflight"
    assert fake.events == [*_PREFLIGHT_EVENTS, ("is_file", _MESSAGE)]
    fake.assert_drained()


def test_merge_sequence_and_postcheck_are_exact(capsys: pytest.CaptureFixture[str]) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.monotonic_queue[:] = [0.0, 100.0, 130.0]
    fake.is_file_queue.append((_MESSAGE, True))
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "2\n"))
    fake.is_file_queue.append((_MESSAGE, True))
    fake.read_text_queue.append((_MESSAGE, "merge\n\nAI-Agent: codex\n"))
    fake.expect_run(("git", "merge", "--no-ff", "--no-commit", "main"))
    fake.expect_run(("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)))
    fake.expect_run(("git", "commit", "-F", str(_VALIDATED_MESSAGE)))
    fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(0, _SHA_C + "\n"))
    fake.expect_run(
        ("git", "log", "-1", "--format=%B", _SHA_C),
        DW._CommandResult(0, "merge\n\nAI-Agent: codex\n"),
    )
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(0, _SHA_C + "\n"))
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 0
    git_mutations = [
        event[1]
        for event in fake.events
        if event[0] == "run" and event[1][:2] in {("git", "merge"), ("git", "commit")}
    ]
    assert git_mutations == [
        ("git", "merge", "--no-ff", "--no-commit", "main"),
        ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
        ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
    ]
    assert all("--ff-only" not in argv and "--no-edit" not in argv for argv in git_mutations)
    assert not any(event[0] == "run" and event[1] == _helper("release") for event in fake.events)
    captured = capsys.readouterr()
    assert "lease is held" in captured.out
    assert "TTL remaining at most 2370 seconds" in captured.out
    assert "exclusivity is lost after expiry" in captured.out
    assert "no fencing token" in captured.out
    assert "until land termination" not in captured.out
    assert "timeout=none" in captured.err
    assert ("unlink", _VALIDATED_MESSAGE) in fake.events
    fake.assert_drained()


_STAGES = (
    "preclaim-rev-parse",
    "claim",
    "postclaim-rev-parse",
    "behind-count",
    "merge",
    "commit-dry-run",
    "commit",
    "commit-rev-parse",
    "commit-message-postcheck",
    "postcheck",
    "commit-head-postcheck",
)


@pytest.mark.parametrize("stage", _STAGES, ids=_STAGES)
def test_nonzero_stage_blocks_submission_and_releases(stage: str) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    if stage == "preclaim-rev-parse":
        fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(9))
    else:
        fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_A + "\n"))
        fake.expect_run(
            _helper("claim", _SHA_A),
            DW._CommandResult(9) if stage == "claim" else DW._CommandResult(0, '{"state":"acquired"}'),
        )
    if stage not in {"preclaim-rev-parse", "claim"}:
        fake.expect_run(
            ("git", "rev-parse", "main"),
            DW._CommandResult(9) if stage == "postclaim-rev-parse" else DW._CommandResult(0, _SHA_B + "\n"),
        )
    if stage not in {"preclaim-rev-parse", "claim", "postclaim-rev-parse"}:
        fake.expect_run(
            ("git", "rev-list", "--count", "HEAD..main"),
            DW._CommandResult(9) if stage == "behind-count" else DW._CommandResult(0, "1\n"),
        )
    merge_stages = {
        "merge", "commit-dry-run", "commit", "commit-rev-parse",
        "commit-message-postcheck", "postcheck", "commit-head-postcheck",
    }
    if stage in merge_stages:
        fake.is_file_queue.extend([(_MESSAGE, True), (_MESSAGE, True)])
        fake.read_text_queue.append((_MESSAGE, "merge\nAI-Agent: codex\n"))
        fake.expect_run(
            ("git", "merge", "--no-ff", "--no-commit", "main"),
            DW._CommandResult(9) if stage == "merge" else DW._CommandResult(0),
        )
    if stage in {
        "commit-dry-run", "commit", "commit-rev-parse",
        "commit-message-postcheck", "postcheck", "commit-head-postcheck",
    }:
        fake.expect_run(
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            DW._CommandResult(9) if stage == "commit-dry-run" else DW._CommandResult(0),
        )
    if stage in {
        "commit", "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck",
    }:
        fake.expect_run(
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
            DW._CommandResult(9) if stage == "commit" else DW._CommandResult(0),
        )
    if stage in {
        "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck",
    }:
        fake.expect_run(
            ("git", "rev-parse", "HEAD"),
            DW._CommandResult(9) if stage == "commit-rev-parse"
            else DW._CommandResult(0, _SHA_C + "\n"),
        )
    if stage in {"commit-message-postcheck", "postcheck", "commit-head-postcheck"}:
        fake.expect_run(
            ("git", "log", "-1", "--format=%B", _SHA_C),
            DW._CommandResult(9) if stage == "commit-message-postcheck"
            else DW._CommandResult(0, "merge\nAI-Agent: codex\n"),
        )
    if stage in {"postcheck", "commit-head-postcheck"}:
        fake.expect_run(
            ("git", "rev-list", "--count", "HEAD..main"),
            DW._CommandResult(9) if stage == "postcheck"
            else DW._CommandResult(0, "0\n"),
        )
    if stage == "commit-head-postcheck":
        fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(9))
    if stage in {"merge", "commit-dry-run", "commit"}:
        _abort_clean(fake)
    if stage != "preclaim-rev-parse":
        _release(fake)

    outcome = _run_acceptance(fake, message=_MESSAGE if stage in merge_stages else None)

    assert outcome.rc == 70
    expected = [*_PREFLIGHT_EVENTS]
    if stage in merge_stages:
        expected.append(("is_file", _MESSAGE))
    expected.extend(
        [
            ("monotonic",),
            ("run", ("git", "rev-parse", "main"), _REPO, True),
        ]
    )
    if stage != "preclaim-rev-parse":
        expected.extend(
            [
                ("monotonic",),
                ("run", _helper("claim", _SHA_A), _REPO, True),
            ]
        )
    if stage not in {"preclaim-rev-parse", "claim"}:
        expected.append(("run", ("git", "rev-parse", "main"), _REPO, True))
    if stage not in {"preclaim-rev-parse", "claim", "postclaim-rev-parse"}:
        expected.append(
            ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True)
        )
    if stage in merge_stages:
        expected.extend(
            [
                ("is_file", _MESSAGE),
                ("read_text", _MESSAGE),
                ("write_temp", b"merge\nAI-Agent: codex\n"),
                ("run", ("git", "merge", "--no-ff", "--no-commit", "main"), _REPO, True),
            ]
        )
    if stage in {
        "commit-dry-run", "commit", "commit-rev-parse",
        "commit-message-postcheck", "postcheck", "commit-head-postcheck",
    }:
        expected.append(
            ("run", ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)), _REPO, True)
        )
    if stage in {
        "commit", "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck",
    }:
        expected.append(
            ("run", ("git", "commit", "-F", str(_VALIDATED_MESSAGE)), _REPO, True)
        )
    if stage in {
        "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck",
    }:
        expected.append(("run", ("git", "rev-parse", "HEAD"), _REPO, True))
    if stage in {"commit-message-postcheck", "postcheck", "commit-head-postcheck"}:
        expected.append(
            ("run", ("git", "log", "-1", "--format=%B", _SHA_C), _REPO, True)
        )
    if stage in {"postcheck", "commit-head-postcheck"}:
        expected.append(
            ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True)
        )
    if stage == "commit-head-postcheck":
        expected.append(("run", ("git", "rev-parse", "HEAD"), _REPO, True))
    if stage in merge_stages:
        expected.append(("unlink", _VALIDATED_MESSAGE))
    if stage in {"merge", "commit-dry-run", "commit"}:
        expected.extend(_ABORT_CLEAN_EVENTS)
    if stage != "preclaim-rev-parse":
        expected.append(("run", _helper("release"), _REPO, True))
    assert fake.events == expected
    fake.assert_drained()


def test_merge_failure_aborts_before_release() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.is_file_queue.extend([(_MESSAGE, True), (_MESSAGE, True)])
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "1\n"))
    fake.read_text_queue.append((_MESSAGE, "merge\nAI-Agent: codex\n"))
    fake.expect_run(("git", "merge", "--no-ff", "--no-commit", "main"), DW._CommandResult(1))
    _abort_clean(fake)
    _release(fake)
    outcome = _run_acceptance(fake, message=_MESSAGE)
    assert outcome.rc == 70
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("is_file", _MESSAGE),
        ("read_text", _MESSAGE),
        ("write_temp", b"merge\nAI-Agent: codex\n"),
        ("run", ("git", "merge", "--no-ff", "--no-commit", "main"), _REPO, True),
        ("unlink", _VALIDATED_MESSAGE),
        *_ABORT_CLEAN_EVENTS,
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


def test_acceptance_command_red_is_propagated_after_release() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(_COMMAND, DW._CommandResult(23), capture=False)
    _release(fake)
    outcome = _run_acceptance(fake)
    assert outcome.rc == 23
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", _COMMAND, _REPO, False),
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


@pytest.mark.parametrize("kind", ["subprocess-error", "keyboard-interrupt"])
def test_abnormal_path_without_ownership_does_not_release(kind: str) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    if kind == "subprocess-error":
        fake.expect_run(("git", "rev-parse", "main"), OSError("boom"))
    else:
        fake.monotonic_queue[:] = [0.0, 0.0]
        _claim(fake, _SHA_A, '{"state":"held"}')
        original_sleep = fake.sleep

        def interrupting_sleep(seconds: float) -> None:
            original_sleep(seconds)
            raise KeyboardInterrupt

        effects = fake.effects
        effects = DW._Effects(
            run=effects.run, run_unbounded=effects.run_unbounded,
            sleep=interrupting_sleep, kill=effects.kill,
            is_file=effects.is_file, read_text=effects.read_text,
            getenv=effects.getenv, monotonic=effects.monotonic,
            write_temp=effects.write_temp, unlink=effects.unlink,
        )
    if kind == "subprocess-error":
        outcome = _run_acceptance(fake)
    else:
        outcome = DW.run_acceptance(
            wave=_WAVE, lease_dir=_LEASE, merge_message_file=None,
            poll_seconds=30, max_wait_seconds=7200, command=_COMMAND,
            repo=_REPO, effects=effects,
        )
    assert outcome.rc == (130 if kind == "keyboard-interrupt" else 70)
    expected = [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
    ]
    if kind == "keyboard-interrupt":
        expected.extend(
            [
                ("monotonic",),
                ("run", _helper("claim", _SHA_A), _REPO, True),
                ("monotonic",),
                ("sleep", 30),
            ]
        )
    assert fake.events == expected
    fake.assert_drained()


def test_release_failure_overrides_primary_result() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(_COMMAND, DW._CommandResult(5), capture=False)
    _release(fake, DW._CommandResult(0, '{"state":"unavailable"}'))
    outcome = _run_acceptance(fake)
    assert outcome.rc == 74
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", _COMMAND, _REPO, False),
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


@pytest.mark.parametrize(
    "release_result",
    [DW._CommandResult(9, ""), DW._CommandResult(0, "not-json")],
    ids=("nonzero", "malformed-json"),
)
def test_release_subprocess_failures_are_cleanup_failures(release_result: object) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(_COMMAND, DW._CommandResult(5), capture=False)
    _release(fake, release_result)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 74
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", _COMMAND, _REPO, False),
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


def test_merge_abort_nonzero_is_cleanup_failure() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.is_file_queue.extend([(_MESSAGE, True), (_MESSAGE, True)])
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "1\n"))
    fake.read_text_queue.append((_MESSAGE, "merge\nAI-Agent: codex\n"))
    fake.expect_run(("git", "merge", "--no-ff", "--no-commit", "main"), DW._CommandResult(1))
    _abort_clean(fake, DW._CommandResult(8))
    _release(fake)

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 74
    assert outcome.stage == "merge-abort"
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("is_file", _MESSAGE),
        ("read_text", _MESSAGE),
        ("write_temp", b"merge\nAI-Agent: codex\n"),
        ("run", ("git", "merge", "--no-ff", "--no-commit", "main"), _REPO, True),
        ("unlink", _VALIDATED_MESSAGE),
        *_ABORT_CLEAN_EVENTS,
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


@pytest.mark.parametrize("dirty", ["merge-head", "tracked"], ids=("merge-head", "tracked"))
def test_merge_abort_requires_clean_repository_postcondition(dirty: str) -> None:
    fake = _FakeEffects()
    fake.expect_run(("git", "merge", "--abort"))
    fake.expect_run(
        ("git", "rev-parse", "-q", "--verify", "MERGE_HEAD"),
        DW._CommandResult(0, _SHA_A + "\n")
        if dirty == "merge-head" else DW._CommandResult(1),
    )
    fake.expect_run(
        ("git", "status", "--porcelain", "--untracked-files=no"),
        DW._CommandResult(0, " M tracked.py\n" if dirty == "tracked" else ""),
    )

    outcome = DW._abort_pending_merge(fake.effects, _REPO)

    assert outcome.rc == 74
    assert outcome.stage == (
        "merge-abort-state" if dirty == "merge-head" else "merge-abort-clean"
    )
    fake.assert_drained(_ABORT_CLEAN_EVENTS)


def test_default_run_sanitizes_git_and_bounds_only_stages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    popen_calls: list[tuple[list[str], dict[str, object]]] = []
    run_calls: list[tuple[list[str], dict[str, object]]] = []
    group_kills: list[tuple[int, int]] = []

    class Process:
        def __init__(self, argv: list[str], *, times_out: bool = False) -> None:
            self.argv = argv
            self.pid = 4321
            self.returncode = 0
            self.times_out = times_out
            self.communicate_calls: list[object] = []

        def communicate(self, timeout: object = None) -> tuple[str, str]:
            self.communicate_calls.append(timeout)
            if self.times_out and len(self.communicate_calls) == 1:
                raise subprocess.TimeoutExpired(self.argv, timeout)
            self.returncode = -signal.SIGKILL if self.times_out else 0
            return "", ""

        def kill(self) -> None:
            self.returncode = -signal.SIGKILL

        def wait(self, timeout: object = None) -> int:
            del timeout
            return self.returncode

    processes: list[Process] = []

    def recording_popen(argv: list[str], **kwargs: object) -> Process:
        popen_calls.append((argv, kwargs))
        process = Process(argv, times_out=len(popen_calls) == 3)
        processes.append(process)
        return process

    def recording_run(
        argv: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        run_calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, "", "")

    for key in DW._GIT_ENV_KEYS:
        monkeypatch.setenv(key, f"bad-{key}")
    monkeypatch.setattr(DW.subprocess, "Popen", recording_popen)
    monkeypatch.setattr(DW.subprocess, "run", recording_run)
    monkeypatch.setattr(
        DW.os, "killpg", lambda pid, signum: group_kills.append((pid, signum))
    )

    DW._default_run(("git", "status"), _REPO, True)
    DW._default_run(_helper("release"), _REPO, True)
    DW._default_run_unbounded(("git", "status"), _REPO, False)
    with pytest.raises(subprocess.TimeoutExpired):
        DW._default_run(("git", "merge", "main"), _REPO, True)

    git_kwargs = popen_calls[0][1]
    assert git_kwargs["start_new_session"] is True
    assert all(key not in git_kwargs["env"] for key in DW._GIT_ENV_KEYS)
    assert popen_calls[1][1]["start_new_session"] is True
    assert len(run_calls) == 1
    assert "start_new_session" not in run_calls[0][1]
    assert all(key not in run_calls[0][1]["env"] for key in DW._GIT_ENV_KEYS)
    assert len(popen_calls) == 3
    assert processes[2].communicate_calls == [300, 5]
    assert group_kills == [(4321, signal.SIGKILL)]


@pytest.mark.parametrize(
    "case", ["missing-delimiter", "empty-command", "poll-29", "poll-121", "default-30"],
)
def test_acceptance_cli_contract(case: str) -> None:
    base = ["acceptance", "--wave", _WAVE, "--lease-dir", str(_LEASE)]
    if case == "missing-delimiter":
        argv = base + ["harmless"]
    elif case == "empty-command":
        argv = base + ["--"]
    elif case == "poll-29":
        argv = base + ["--poll-seconds", "29", "--", "harmless"]
    elif case == "poll-121":
        argv = base + ["--poll-seconds", "121", "--", "harmless"]
    else:
        command, args, child = DW._parse_cli(base + ["--", "harmless"])
        assert command == "acceptance"
        assert args.poll_seconds == 30
        assert args.max_wait_seconds == 7200
        assert args.owned_path == []
        assert child == ["harmless"]
        return
    with pytest.raises(DW._StageFailure) as raised:
        DW._parse_cli(argv)
    assert raised.value.outcome.rc == 2


def test_acceptance_owned_path_is_repeatable() -> None:
    command, args, child = DW._parse_cli(
        [
            "acceptance",
            "--wave",
            _WAVE,
            "--lease-dir",
            str(_LEASE),
            "--owned-path",
            "./docs/x.md",
            "--owned-path",
            "tools",
            "--",
            "harmless",
        ]
    )

    assert command == "acceptance"
    assert args.owned_path == [Path("docs/x.md"), Path("tools")]
    assert child == ["harmless"]


@pytest.mark.parametrize(
    ("top_level", "branch", "status", "failed_stage"),
    [
        ("/other", f"feature-{_WAVE}", "", "preflight-toplevel"),
        (str(_REPO), "wrong-branch", "", "preflight-branch"),
        (str(_REPO), f"feature-{_WAVE}", " M tracked.py\n", "preflight-clean"),
    ],
)
def test_identity_preflight_rejects_before_claim(
    top_level: str, branch: str, status: str, failed_stage: str,
) -> None:
    fake = _FakeEffects()
    fake.expect_run(("git", "rev-parse", "--is-inside-work-tree"), DW._CommandResult(0, "true\n"))
    fake.expect_run(("git", "rev-parse", "--show-toplevel"), DW._CommandResult(0, top_level + "\n"))
    if failed_stage != "preflight-toplevel":
        fake.expect_run(("git", "symbolic-ref", "--quiet", "--short", "HEAD"), DW._CommandResult(0, branch + "\n"))
    if failed_stage == "preflight-clean":
        fake.expect_run(("git", "status", "--porcelain", "--untracked-files=no"), DW._CommandResult(0, status))
    outcome = _run_acceptance(fake)
    assert outcome.rc == 2
    assert outcome.stage == failed_stage
    expected = [
        ("run", ("git", "rev-parse", "--is-inside-work-tree"), _REPO, True),
        ("run", ("git", "rev-parse", "--show-toplevel"), _REPO, True),
    ]
    if failed_stage != "preflight-toplevel":
        expected.append(
            ("run", ("git", "symbolic-ref", "--quiet", "--short", "HEAD"), _REPO, True)
        )
    if failed_stage == "preflight-clean":
        expected.append(
            ("run", ("git", "status", "--porcelain", "--untracked-files=no"), _REPO, True)
        )
    assert fake.events == expected
    fake.assert_drained()


def test_wrong_branch_fixture_reaches_submission_only_if_branch_gate_is_removed() -> None:
    fake = _RoutingAcceptanceEffects(branch="wrong-branch", behind=[0])

    outcome = _run_acceptance(fake)

    assert outcome.rc == 2
    assert outcome.stage == "preflight-branch"
    assert (fake.claims, fake.submissions, fake.releases) == (0, 0, 0)


def test_positive_postmerge_behind_count_blocks_only_submission() -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1, 1],
        head_shas=[_SHA_C],
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "postcheck"
    assert (fake.claims, fake.submissions, fake.releases) == (1, 0, 1)


def test_created_commit_identity_change_blocks_submission() -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1, 0],
        head_shas=[_SHA_C, _SHA_B],
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "commit-head-postcheck"
    assert (fake.claims, fake.submissions, fake.releases) == (1, 0, 1)


def test_merge_message_requires_nonempty_ai_agent_trailer() -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1, 0],
        message="merge without trailer\n",
        head_shas=[_SHA_C, _SHA_C],
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "merge-message"
    assert (fake.claims, fake.submissions, fake.releases) == (1, 0, 1)


def test_committed_message_without_ai_agent_never_runs_acceptance() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.is_file_queue.extend([(_MESSAGE, True), (_MESSAGE, True)])
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "1\n"))
    fake.read_text_queue.append((_MESSAGE, "merge\nAI-Agent: codex\n"))
    fake.expect_run(("git", "merge", "--no-ff", "--no-commit", "main"))
    fake.expect_run(("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)))
    fake.expect_run(("git", "commit", "-F", str(_VALIDATED_MESSAGE)))
    fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(0, _SHA_C + "\n"))
    fake.expect_run(
        ("git", "log", "-1", "--format=%B", _SHA_C),
        DW._CommandResult(0, "merge without trailer\n"),
    )
    _release(fake)

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "commit-message-postcheck"
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("is_file", _MESSAGE),
        ("read_text", _MESSAGE),
        ("write_temp", b"merge\nAI-Agent: codex\n"),
        ("run", ("git", "merge", "--no-ff", "--no-commit", "main"), _REPO, True),
        ("run", ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)), _REPO, True),
        ("run", ("git", "commit", "-F", str(_VALIDATED_MESSAGE)), _REPO, True),
        ("run", ("git", "rev-parse", "HEAD"), _REPO, True),
        ("run", ("git", "log", "-1", "--format=%B", _SHA_C), _REPO, True),
        ("unlink", _VALIDATED_MESSAGE),
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


def test_signal_path_releases_and_normalizes_rc() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_A + "\n"))
    fake.expect_run(_helper("claim", _SHA_A), DW._SignalReceived(15))
    _release(fake)
    outcome = _run_acceptance(fake)
    assert outcome.rc == 143
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


def test_cleanup_consumes_ownership_before_release_and_is_idempotent() -> None:
    fake = _FakeEffects()
    _release(fake)
    lifecycle = DW._AcceptanceLifecycle(ownership=DW._LeaseOwnership.ACQUIRED)

    first = DW._cleanup_lifecycle(lifecycle, fake.effects, _REPO, _LEASE, _WAVE)
    second = DW._cleanup_lifecycle(lifecycle, fake.effects, _REPO, _LEASE, _WAVE)

    assert first is None
    assert second is None
    assert lifecycle.ownership is DW._LeaseOwnership.NONE
    fake.assert_drained([("run", _helper("release"), _REPO, True)])


def test_signal_after_core_success_uses_restored_real_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    restored_handler_calls: list[int] = []
    restore_calls = 0
    real_restore = DW._restore_signal_handlers

    def inject_signal_then_restore(previous: dict[int, object]) -> None:
        nonlocal restore_calls
        restore_calls += 1
        if restore_calls == 1:
            os.kill(os.getpid(), signal.SIGTERM)
        real_restore(previous)

    monkeypatch.setattr(DW, "_restore_signal_handlers", inject_signal_then_restore)
    original = signal.getsignal(signal.SIGTERM)
    signal.signal(
        signal.SIGTERM,
        lambda signum, frame: restored_handler_calls.append(signum),
    )
    try:
        rc = DW.main(
            [
                "acceptance", "--wave", _WAVE, "--lease-dir", str(_LEASE),
                "--", *_COMMAND,
            ],
            effects=fake.effects,
            repo=_REPO,
        )
        os.kill(os.getpid(), signal.SIGTERM)
    finally:
        signal.signal(signal.SIGTERM, original)

    assert rc == 143
    assert restore_calls == 2
    assert restored_handler_calls == [signal.SIGTERM]
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", _COMMAND, _REPO, False),
        ("monotonic",),
    ]
    fake.assert_drained()


def test_public_main_failure_restores_handler_without_release() -> None:
    fake = _FakeEffects()
    fake.expect_run(
        ("git", "rev-parse", "--is-inside-work-tree"),
        DW._CommandResult(0, "true\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "--show-toplevel"),
        DW._CommandResult(0, str(_REPO) + "\n"),
    )
    fake.expect_run(
        ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
        DW._CommandResult(0, "wrong-branch\n"),
    )
    restored_handler_calls: list[int] = []
    original = signal.getsignal(signal.SIGTERM)
    signal.signal(
        signal.SIGTERM,
        lambda signum, frame: restored_handler_calls.append(signum),
    )
    try:
        rc = DW.main(
            [
                "acceptance", "--wave", _WAVE, "--lease-dir", str(_LEASE),
                "--", *_COMMAND,
            ],
            effects=fake.effects,
            repo=_REPO,
        )
        os.kill(os.getpid(), signal.SIGTERM)
    finally:
        signal.signal(signal.SIGTERM, original)

    assert rc == 2
    assert restored_handler_calls == [signal.SIGTERM]
    fake.assert_drained(
        [
            ("run", ("git", "rev-parse", "--is-inside-work-tree"), _REPO, True),
            ("run", ("git", "rev-parse", "--show-toplevel"), _REPO, True),
            (
                "run",
                ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
                _REPO,
                True,
            ),
        ]
    )


def test_second_signal_is_deferred_until_cleanup_completes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    _release(fake)
    previous_mask = {signal.SIGUSR1}

    def signal_mask(how: int, signals: object) -> set[signal.Signals]:
        if how == signal.SIG_BLOCK:
            fake.events.append(("mask", how, tuple(signals)))
            return previous_mask
        fake.events.append(("mask", how, signals))
        raise DW._SignalReceived(signal.SIGINT)

    monkeypatch.setattr(DW.signal, "pthread_sigmask", signal_mask)

    outcome = DW._cleanup_after_claim(
        fake.effects, _REPO, _LEASE, _WAVE, merge_pending=False,
    )

    assert outcome is None
    assert fake.events == [
        ("mask", signal.SIG_BLOCK, DW._HANDLED_SIGNALS),
        ("run", _helper("release"), _REPO, True),
        ("mask", signal.SIG_SETMASK, previous_mask),
    ]
    fake.assert_drained()


def test_default_wiring_with_real_git_and_lease_helper(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    lease = tmp_path / "lease"
    repo.mkdir()
    lease.mkdir()
    tools = repo / "tools"
    tools.mkdir()
    shutil.copy2(_LEASE_HELPER, tools / "wave_land_window.py")

    git_env = {
        **{key: value for key, value in os.environ.items() if key not in DW._GIT_ENV_KEYS},
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True,
            env=git_env,
        )

    git("init", "-b", "main")
    tracked = repo / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    git("add", "tracked.txt")
    git("commit", "-m", "base")
    git("checkout", "-b", "worktree-integration")
    git("checkout", "main")
    tracked.write_text("main advanced\n", encoding="utf-8")
    git("add", "tracked.txt")
    git("commit", "-m", "advance main")
    git("checkout", "worktree-integration")
    message = tmp_path / "merge-message.txt"
    message.write_text("merge main\n\nAI-Agent: codex\n", encoding="utf-8")

    child = (
        "import pathlib,sys; "
        "expected=pathlib.Path(sys.argv[1]); "
        "assert pathlib.Path.cwd()==expected; "
        "print('CHILD-STDOUT-SENTINEL'); "
        "print('CHILD-STDERR-SENTINEL', file=sys.stderr)"
    )
    waiter_env = {**git_env, "IZANAGI_WAVE_LEASE_DIR": str(lease)}

    result = subprocess.run(
        [
            sys.executable,
            str(_TOOL),
            "acceptance",
            "--wave",
            "integration",
            "--merge-message-file",
            str(message),
            "--",
            sys.executable,
            "-c",
            child,
            str(repo.resolve()),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=waiter_env,
    )

    assert result.returncode == 0, result.stderr
    assert "lease is held" in result.stdout
    assert "CHILD-STDOUT-SENTINEL" in result.stdout
    assert "CHILD-STDERR-SENTINEL" in result.stderr
    assert "AI-Agent: codex" in git("log", "-1", "--format=%B", "HEAD").stdout
    assert git("rev-list", "--count", "HEAD..main").stdout.strip() == "0"
    assert (lease / "acceptance.lease").is_file()
    released = subprocess.run(
        [
            sys.executable,
            str(tools / "wave_land_window.py"),
            "release",
            "--lease-dir",
            str(lease),
            "--wave",
            "integration",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert released.returncode == 0
    assert json.loads(released.stdout)["state"] == "released"


def test_public_main_real_signal_releases_lease(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    lease = tmp_path / "lease"
    repo.mkdir()
    lease.mkdir()
    (repo / "tools").mkdir()
    shutil.copy2(_LEASE_HELPER, repo / "tools" / "wave_land_window.py")
    git_env = {
        **{key: value for key, value in os.environ.items() if key not in DW._GIT_ENV_KEYS},
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }

    def git(*args: str) -> None:
        subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True,
            env=git_env,
        )

    git("init", "-b", "main")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    git("add", "tracked.txt")
    git("commit", "-m", "base")
    git("checkout", "-b", "worktree-signal")
    signal_child = (
        "import os,signal; "
        "os.kill(os.getppid(), signal.SIGTERM)"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(_TOOL),
            "acceptance",
            "--wave",
            "signal",
            "--",
            sys.executable,
            "-c",
            signal_child,
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env={**git_env, "IZANAGI_WAVE_LEASE_DIR": str(lease)},
    )

    assert result.returncode == 143, result.stderr
    assert not (lease / "acceptance.lease").exists()


def test_public_main_real_signal_after_success_uses_restored_handler(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo-success"
    lease = tmp_path / "lease-success"
    repo.mkdir()
    lease.mkdir()
    (repo / "tools").mkdir()
    shutil.copy2(_LEASE_HELPER, repo / "tools" / "wave_land_window.py")
    git_env = {
        **{key: value for key, value in os.environ.items() if key not in DW._GIT_ENV_KEYS},
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }

    def git(*args: str) -> None:
        subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True,
            env=git_env,
        )

    git("init", "-b", "main")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    git("add", "tracked.txt")
    git("commit", "-m", "base")
    git("checkout", "-b", "worktree-signal-success")
    runner = tmp_path / "success-boundary.py"
    runner.write_text(
        "import importlib.util, os, signal, sys\n"
        "from pathlib import Path\n"
        "spec=importlib.util.spec_from_file_location('waiter', sys.argv[1])\n"
        "module=importlib.util.module_from_spec(spec)\n"
        "sys.modules[spec.name]=module\n"
        "spec.loader.exec_module(module)\n"
        "received=[]\n"
        "signal.signal(signal.SIGTERM, lambda n, f: received.append(n))\n"
        "rc=module.main(['acceptance','--wave','signal-success','--',"
        "sys.executable,'-c','raise SystemExit(0)'], repo=Path(sys.argv[2]))\n"
        "os.kill(os.getpid(), signal.SIGTERM)\n"
        "print(f'RESTORED={received} RC={rc}')\n"
        "raise SystemExit(rc)\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(runner), str(_TOOL), str(repo)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env={**git_env, "IZANAGI_WAVE_LEASE_DIR": str(lease)},
    )

    assert result.returncode == 0, result.stderr
    assert f"RESTORED=[{signal.SIGTERM}] RC=0" in result.stdout
    assert (lease / "acceptance.lease").is_file()
