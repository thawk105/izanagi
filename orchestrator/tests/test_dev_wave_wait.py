# -*- coding: utf-8 -*-
"""tools/dev_wave_wait.py の canonical waiter 契約テスト。"""
from __future__ import annotations

import errno
import hashlib
import importlib.util
import itertools
import json
import os
import select
import signal
import shutil
import subprocess
import sys
import textwrap
import threading
import time
import tracemalloc
from collections.abc import Iterator
from pathlib import Path

import pytest


_ROOT = Path(__file__).resolve().parents[2]
_TOOL = _ROOT / "tools" / "dev_wave_wait.py"
_LAUNCHER = _ROOT / "tools" / "acceptance_launcher.py"
_LEASE_HELPER = _ROOT / "tools" / "wave_land_window.py"
_LANDER = _ROOT / "tools" / "dev_wave_land.py"
_DISPATCHER = _ROOT / "tools" / "pegasus" / "dispatch_compute.py"
_SPEC = importlib.util.spec_from_file_location("dev_wave_wait_under_test", _TOOL)
assert _SPEC and _SPEC.loader
DW = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = DW
_SPEC.loader.exec_module(DW)
_LAUNCHER_SPEC = importlib.util.spec_from_file_location(
    "acceptance_launcher_for_waiter_test", _LAUNCHER,
)
assert _LAUNCHER_SPEC and _LAUNCHER_SPEC.loader
LA = importlib.util.module_from_spec(_LAUNCHER_SPEC)
sys.modules[_LAUNCHER_SPEC.name] = LA
_LAUNCHER_SPEC.loader.exec_module(LA)
_LEASE_SPEC = importlib.util.spec_from_file_location(
    "wave_land_window_under_test", _LEASE_HELPER,
)
assert _LEASE_SPEC and _LEASE_SPEC.loader
WL = importlib.util.module_from_spec(_LEASE_SPEC)
sys.modules[_LEASE_SPEC.name] = WL
_LEASE_SPEC.loader.exec_module(WL)
_LAND_SPEC = importlib.util.spec_from_file_location(
    "dev_wave_land_under_test_for_waiter", _LANDER,
)
assert _LAND_SPEC and _LAND_SPEC.loader
LAND = importlib.util.module_from_spec(_LAND_SPEC)
sys.modules[_LAND_SPEC.name] = LAND
_LAND_SPEC.loader.exec_module(LAND)
_DISPATCH_SPEC = importlib.util.spec_from_file_location(
    "pegasus_dispatch_compute_under_test", _DISPATCHER,
)
assert _DISPATCH_SPEC and _DISPATCH_SPEC.loader
DC = importlib.util.module_from_spec(_DISPATCH_SPEC)
sys.modules[_DISPATCH_SPEC.name] = DC
_DISPATCH_SPEC.loader.exec_module(DC)

_SHA_A = "a" * 40
_SHA_B = "b" * 40
_SHA_C = "c" * 40
_WAVE = "wave-test"
_REPO = Path("/repo")
_LEASE = Path("/lease")
_MESSAGE = Path("/message.txt")
_VALIDATED_MESSAGE = Path("/validated-message.txt")
_RECEIPT = Path("/receipts/acceptance.json")
_RECEIPT_TEMP = Path("/receipts/.dev-wave-acceptance-receipt-test.tmp")
_LOG = Path("/receipts/acceptance.log")
_COMMAND = ("harmless-command", "--flag")
_RELAYED_LOADGROUP_MARKER = (
    b'| IZANAGI_EFFECTIVE_SCHEDULER_V1 {"effective_scheduler":"loadgroup"}'
)
_HOLDER = hashlib.sha256(_WAVE.encode("utf-8")).hexdigest()[:12]
_WAITER_BLOB = "d" * 40
_WAITER_BYTES_SHA256 = hashlib.sha256(b"same waiter source").hexdigest()
_LAUNCHER_BLOB = "2" * 40
_LAUNCHER_SOURCE = b"# acceptance launcher source\n"
_SELF_REPORTED_MERGE_MESSAGE = (
    b"merge main\n\n"
    b"AI-Agent: product=claude; model=not-exposed; "
    b"reasoning=not-exposed; role=integrator"
)
_RELEASE_JSON = json.dumps({"state": "released"})
_LEGACY_STATUS_ARGV = ("git", "status", "--porcelain", "--untracked-files=no")
_STATUS_ARGV = (
    "git", "status", "--porcelain", "--untracked-files=all",
    "--ignore-submodules=none",
)
_INDEX_FLAGS_ARGV = ("git", "ls-files", "-v", "-z")
_SUBMODULE_INDEX_FLAGS_ARGV = (
    "git", "submodule", "foreach", "--recursive", "--quiet",
    "git ls-files -v -z",
)
_DIFF_ARGV = ("git", "diff", "--binary", "--no-ext-diff", "HEAD", "--")
_SUBMODULE_STATUS_ARGV = ("git", "submodule", "status", "--recursive")
_SUBMODULE_READY_ARGV = _SUBMODULE_STATUS_ARGV
_REAL_PTHREAD_SIGMASK = signal.pthread_sigmask
_SIGNAL_WATCHDOG_SECONDS = 5.0


@pytest.fixture(autouse=True)
def _handled_signals_are_unblocked() -> Iterator[None]:
    entry_mask = set(_REAL_PTHREAD_SIGMASK(signal.SIG_BLOCK, ()))
    entry_blocked = entry_mask.intersection(DW._HANDLED_SIGNALS)
    if entry_blocked:
        try:
            pytest.fail(f"handled signals blocked at test entry: {entry_blocked!r}")
        finally:
            _REAL_PTHREAD_SIGMASK(signal.SIG_UNBLOCK, DW._HANDLED_SIGNALS)

    try:
        yield
    finally:
        exit_mask = set(_REAL_PTHREAD_SIGMASK(signal.SIG_BLOCK, ()))
        exit_blocked = exit_mask.intersection(DW._HANDLED_SIGNALS)
        try:
            assert not exit_blocked, (
                f"handled signals leaked by test: {exit_blocked!r}"
            )
        finally:
            if exit_mask != entry_mask:
                _REAL_PTHREAD_SIGMASK(signal.SIG_SETMASK, entry_mask)


def _await_python_handler(event: threading.Event) -> None:
    assert event.wait(_SIGNAL_WATCHDOG_SECONDS), "Python signal handler did not run"


def _await_wakeup_token(read_fd: int, signum: int) -> None:
    readable, _, _ = select.select(
        [read_fd], [], [], _SIGNAL_WATCHDOG_SECONDS
    )
    assert readable == [read_fd], "C signal handler did not publish a wakeup token"
    assert os.read(read_fd, 1) == bytes((signum & 0xFF,))


class _InterruptAfterHandledSigblock:
    def __init__(self, signum: int = signal.SIGTERM) -> None:
        self.signum = signum
        self.injected = False

    def __call__(self, how: int, signals: object) -> set[signal.Signals]:
        result = _REAL_PTHREAD_SIGMASK(how, signals)
        if (
            not self.injected
            and how == signal.SIG_BLOCK
            and frozenset(signals) == frozenset(DW._HANDLED_SIGNALS)
        ):
            self.injected = True
            raise DW._SignalReceived(self.signum)
        return result


def _scheduler_marker(value: object = "serial", *, relay: bool = False) -> bytes:
    payload = json.dumps(
        {"effective_scheduler": value},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    prefix = b"| " if relay else b""
    return prefix + DW._EFFECTIVE_SCHEDULER_PREFIX + payload + b"\n"


def _dispatch_outcome_marker(
    *,
    child_started: bool = False,
    child_rc: int | None = None,
    reason: str = "queue-wait-timeout",
    relay: bool = False,
) -> bytes:
    payload = json.dumps(
        {
            "child_rc": child_rc,
            "child_started": child_started,
            "kind": "infra",
            "reason": reason,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    prefix = b"| " if relay else b""
    return prefix + DW._DISPATCH_OUTCOME_PREFIX + payload + b"\n"


def test_dispatch_attestation_protocol_matches_producer_exactly() -> None:
    assert DW._DISPATCH_OUTCOME_PREFIX == DC._DISPATCH_OUTCOME_PREFIX.encode(
        "ascii"
    )
    assert DW._DISPATCH_INFRA_REASONS == DC._DISPATCH_INFRA_REASONS


def _provenance_argv(
    repo: Path = _REPO,
    message: Path = _VALIDATED_MESSAGE,
) -> tuple[str, ...]:
    return (
        sys.executable,
        str(repo / "tools" / "check_ai_provenance.py"),
        "--message-file",
        str(message),
    )


def _history_provenance_argv(repo: Path = _REPO) -> tuple[str, ...]:
    return (
        sys.executable,
        str(repo / "tools" / "check_ai_provenance.py"),
    )


def _stat_text(pid: int, start_time: int) -> str:
    fields = ["S", *("0" for _ in range(18)), str(start_time), "0"]
    return f"{pid} (worker name) " + " ".join(fields)


class _FakeLauncherSession:
    def __init__(
        self,
        fake: "_FakeEffects",
        argv: tuple[str, ...],
        source: bytes,
    ) -> None:
        self.fake = fake
        self.source = source
        raw_options = argv[5:]
        assert len(raw_options) % 2 == 0
        self.options = dict(zip(raw_options[::2], raw_options[1::2]))
        self.child_rc: int | None = None
        self.log_sha256: str | None = None

    def read_outcome(self) -> bytes:
        if self.fake.launcher_returncode_before_outcome is not None:
            raise OSError("launcher exited before outcome")
        log_file = Path(self.options["--log-file"])
        if self.fake.launcher_outcome_without_runner:
            self.fake.byte_files[log_file] = self.fake.logged_bytes
            self.fake.existing_paths.add(log_file)
            self.child_rc = 0
        else:
            child = self.fake.run_logged(_COMMAND, _REPO, log_file)
            self.child_rc = DW._normalize_child_rc(child.returncode)
        self.log_sha256 = hashlib.sha256(self.fake.logged_bytes).hexdigest()
        return LA._canonical_json_bytes(
            {
                "child_rc": self.child_rc,
                "log_sha256": self.log_sha256,
                "runner_executed_sha256": hashlib.sha256(
                    b"runner source"
                ).hexdigest(),
            }
        )

    def send_completion(self, payload: bytes) -> None:
        assert self.child_rc is not None and self.log_sha256 is not None
        if not self.fake.launcher_generate_receipt:
            return
        completion = json.loads(payload)
        config = LA._Config(
            repo_root=Path(self.options["--repo-root"]),
            wave=self.options["--wave"],
            lease_holder=self.options["--lease-holder"],
            tested_main=self.options["--tested-main"],
            tested_tip=self.options["--tested-tip"],
            launcher_source_revision=self.options[
                "--launcher-source-revision"
            ],
            launcher_blob_sha=self.options["--launcher-blob-sha"],
            launcher_executed_sha256=hashlib.sha256(self.source).hexdigest(),
            waiter_executed_sha256=self.options[
                "--waiter-executed-sha256"
            ],
            waiter_blob_sha=self.options.get("--waiter-blob-sha"),
            receipt_file=Path(self.options["--receipt-file"]),
            log_file=Path(self.options["--log-file"]),
            outcome_fd=10,
            completion_fd=11,
            pre_fingerprint=json.loads(
                self.options["--pre-fingerprint-json"]
            ),
            env_projection=json.loads(
                self.options["--env-projection-json"]
            ),
        )
        try:
            self.fake.receipt_content = LA._receipt_bytes(
                config,
                ("python3", "tools/run_tests.py"),
                self.child_rc,
                hashlib.sha256(b"runner source").hexdigest(),
                self.log_sha256,
                completion,
            )
        except LA.LauncherFailure:
            self.fake.launcher_returncode = 1

    def wait(self) -> object:
        return DW._CommandResult(self.fake.launcher_returncode)

    def abort(self) -> None:
        pass


class _FakeEffects:
    def __init__(self) -> None:
        self.events: list[tuple[object, ...]] = []
        self.run_queue: list[tuple[tuple[str, ...], bool, object]] = []
        self.run_with_input_queue: list[
            tuple[tuple[str, ...], bool, bytes, object]
        ] = []
        self.kill_queue: list[object] = []
        self.is_file_queue: list[tuple[Path, object]] = []
        self.read_text_queue: list[tuple[Path, object]] = []
        self.stat_mtime_queue: list[tuple[Path, object]] = []
        self.monotonic_queue: list[float] = []
        self.clock = 0.0
        self.env: dict[str, str] = {}
        self.temp_path = _VALIDATED_MESSAGE
        self.existing_paths: set[Path] = set()
        self.directories: set[Path] = {_RECEIPT.parent}
        self.symlinks: set[Path] = set()
        self.receipt_temp_result: object = _RECEIPT_TEMP
        self.receipt_temp_payload: bytes | None = None
        self.rename_result: object = None
        self.receipt_content: bytes | None = None
        self.receipt_published = False
        self.last_claim_main_sha: str | None = None
        self.final_claim_age_seconds = 0
        self.logged_bytes = _scheduler_marker()
        self.byte_files: dict[Path, bytes] = {}
        self.running_waiter_bytes_result: object = _WAITER_BYTES_SHA256
        self.tip_waiter_bytes_result: object = _WAITER_BYTES_SHA256
        self.launcher_binding = DW._LauncherBinding(
            _LAUNCHER_SOURCE,
            _LAUNCHER_BLOB,
            "tested-main",
        )
        self.launcher_returncode = 0
        self.launcher_returncode_before_outcome: int | None = None
        self.launcher_outcome_without_runner = False
        self.launcher_generate_receipt = True
        self.launcher_argv: tuple[str, ...] | None = None

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
            path_exists=self.path_exists,
            is_dir=self.is_dir,
            resolve_path=self.resolve_path,
            write_receipt_temp=self.write_receipt_temp,
            rename=self.rename,
            run_logged=self.run_logged,
            is_symlink=self.is_symlink,
            inspect_acceptance_log=self.inspect_acceptance_log,
            running_waiter_bytes_sha256=self.running_waiter_bytes_sha256,
            tip_waiter_bytes_sha256=self.tip_waiter_bytes_sha256,
            run_trusted_blob_git=self.run_with_input,
            launcher_source=self.launcher_source,
            launch_launcher=self.launch_launcher,
            inspect_no_verdict_log=self.inspect_no_verdict_log,
            archive_log=self.archive_log,
            acceptance_monotonic=lambda: self.clock,
            stat_mtime_ns=self.stat_mtime_ns,
        )

    def expect_run(
        self,
        argv: tuple[str, ...],
        result: object = None,
        *,
        capture: bool = True,
        unchanged_postrun: bool = True,
    ) -> None:
        if result is None:
            result = DW._CommandResult(0)
        if len(argv) >= 5 and argv[2] == "claim" and argv[-2] == "--main-sha":
            self.last_claim_main_sha = argv[-1]
        if (
            argv == _COMMAND
            and not isinstance(result, BaseException)
        ):
            assert self.last_claim_main_sha is not None
            confirmed_main_sha = self.last_claim_main_sha
            self.run_queue.append((argv, capture, result))
            if not unchanged_postrun:
                return
            postrun = [
                    (_STATUS_ARGV, True, DW._CommandResult(0, "")),
                    (_INDEX_FLAGS_ARGV, True, DW._CommandResult(0, "")),
                    (_SUBMODULE_INDEX_FLAGS_ARGV, True, DW._CommandResult(0, "")),
                    (
                        ("git", "rev-parse", "HEAD"),
                        True,
                        DW._CommandResult(0, _SHA_A + "\n"),
                    ),
                    (_DIFF_ARGV, True, DW._CommandResult(0, "")),
                    (_SUBMODULE_STATUS_ARGV, True, DW._CommandResult(0, "")),
            ]
            scheduler: str | None = None
            if result.returncode == 0:
                try:
                    _digest, payloads = DW._scan_acceptance_log_chunks(
                        [self.logged_bytes]
                    )
                    scheduler = DW._scheduler_from_marker_payloads(payloads)
                except DW._StageFailure:
                    pass
                else:
                    postrun.append(
                        (
                            (
                                "git",
                                "rev-parse",
                                f"{_SHA_A}:tools/dev_wave_wait.py",
                            ),
                            True,
                            DW._CommandResult(0, _WAITER_BLOB + "\n"),
                        )
                    )
            waiter_values = self.running_waiter_bytes_result
            postlaunch_waiter_matches = not (
                isinstance(waiter_values, list)
                and len(waiter_values) >= 3
                and waiter_values[1] != waiter_values[2]
            )
            if (
                result.returncode == 0
                and scheduler in LA._EFFECTIVE_SCHEDULERS
                and postlaunch_waiter_matches
            ):
                postrun.extend(
                    [
                    (
                        ("git", "rev-parse", "main"),
                        True,
                        DW._CommandResult(0, confirmed_main_sha + "\n"),
                    ),
                    (
                        _helper("claim", confirmed_main_sha),
                        True,
                        DW._CommandResult(
                            0,
                            _held_self_payload(
                                main_sha=confirmed_main_sha,
                                age_seconds=self.final_claim_age_seconds,
                            ),
                        ),
                    ),
                    ]
                )
            self.run_queue.extend(postrun)
        else:
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

    def expect_run_with_input(
        self,
        argv: tuple[str, ...],
        content: bytes,
        result: object = None,
        *,
        capture: bool = True,
    ) -> None:
        if result is None:
            result = DW._BinaryCommandResult(0)
        self.run_with_input_queue.append((argv, capture, content, result))

    def run_with_input(
        self,
        argv: object,
        cwd: Path,
        capture: bool,
        content: bytes,
    ) -> object:
        actual = tuple(argv)
        self.events.append(("run_with_input", actual, cwd, capture, content))
        assert self.run_with_input_queue, f"unexpected run_with_input: {actual}"
        expected, expected_capture, expected_content, result = (
            self.run_with_input_queue.pop(0)
        )
        assert actual == expected
        assert capture is expected_capture
        assert content == expected_content
        if isinstance(result, BaseException):
            raise result
        return result

    def run_logged(self, argv: object, cwd: Path, log_file: Path) -> object:
        result = self.run(argv, cwd, False)
        self.byte_files[log_file] = self.logged_bytes
        self.existing_paths.add(log_file)
        return result

    def launcher_source(
        self, repo: Path, tested_main: str, tested_tip: str
    ) -> object:
        assert repo == _REPO
        assert isinstance(tested_main, str)
        assert isinstance(tested_tip, str)
        if self.launcher_binding.waiter_blob_sha is not None:
            argv = (
                "git",
                "rev-parse",
                f"{tested_tip}:tools/dev_wave_wait.py",
            )
            if self.run_queue and self.run_queue[0][0] == argv:
                self.run(argv, repo, True)
            else:
                self.events.append(("run", argv, repo, True))
        return self.launcher_binding

    def launch_launcher(
        self, argv: object, cwd: Path, source: bytes
    ) -> object:
        actual = tuple(argv)
        assert cwd == _REPO
        self.launcher_argv = actual
        return _FakeLauncherSession(self, actual, source)

    def inspect_acceptance_log(self, path: Path) -> tuple[str, str]:
        assert path in self.byte_files, f"unexpected acceptance log: {path}"
        digest, payloads = DW._scan_acceptance_log_chunks([self.byte_files[path]])
        return digest, DW._scheduler_from_marker_payloads(payloads)

    def inspect_no_verdict_log(self, path: Path) -> object:
        assert path in self.byte_files, f"unexpected acceptance log: {path}"
        return DW._scan_no_verdict_log_chunks([self.byte_files[path]])

    def running_waiter_bytes_sha256(self) -> object:
        self.events.append(("running_waiter_bytes_sha256",))
        if isinstance(self.running_waiter_bytes_result, list):
            return self.running_waiter_bytes_result.pop(0)
        if isinstance(self.running_waiter_bytes_result, BaseException):
            raise self.running_waiter_bytes_result
        return self.running_waiter_bytes_result

    def tip_waiter_bytes_sha256(self, repo: Path, tip_sha: str) -> object:
        self.events.append(("tip_waiter_bytes_sha256", repo, tip_sha))
        if isinstance(self.tip_waiter_bytes_result, BaseException):
            raise self.tip_waiter_bytes_result
        return self.tip_waiter_bytes_result

    def sleep(self, seconds: float) -> None:
        self.events.append(("sleep", seconds))
        self.clock += seconds

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

    def stat_mtime_ns(self, path: Path) -> int:
        self.events.append(("stat_mtime_ns", path))
        assert self.stat_mtime_queue, f"unexpected stat_mtime_ns: {path}"
        expected, result = self.stat_mtime_queue.pop(0)
        assert path == expected
        if isinstance(result, BaseException):
            raise result
        return int(result)

    def getenv(self, name: str) -> str | None:
        return self.env.get(name)

    def monotonic(self) -> float:
        self.events.append(("monotonic",))
        return (
            self.monotonic_queue.pop(0)
            if self.monotonic_queue
            else self.clock
        )

    def write_temp(self, content: bytes) -> Path:
        self.events.append(("write_temp", content))
        return self.temp_path

    def unlink(self, path: Path) -> None:
        self.events.append(("unlink", path))
        self.existing_paths.discard(path)
        self.byte_files.pop(path, None)

    def path_exists(self, path: Path) -> bool:
        return path in self.existing_paths

    def is_dir(self, path: Path) -> bool:
        return path in self.directories

    def is_symlink(self, path: Path) -> bool:
        return path in self.symlinks

    def resolve_path(self, path: Path) -> Path:
        if path.is_absolute():
            return Path(os.path.normpath(path))
        return Path(os.path.normpath(_REPO / path))

    def write_receipt_temp(self, final_path: Path, content: bytes) -> Path:
        self.events.append(("write_receipt_temp", final_path))
        if content:
            assert (
                json.loads(content)["schema_version"]
                == "dev-wave-producer-receipt/v1"
            )
        else:
            assert content == b""
        self.receipt_temp_payload = content
        if isinstance(self.receipt_temp_result, BaseException):
            raise self.receipt_temp_result
        return self.receipt_temp_result

    def rename(self, source: Path, target: Path) -> None:
        self.events.append(("rename", source, target))
        if isinstance(self.rename_result, BaseException):
            raise self.rename_result
        self.receipt_published = True
        self.existing_paths.add(target)

    def archive_log(self, source: Path, target: Path) -> None:
        self.events.append(("archive_log", source, target))
        if target in self.existing_paths:
            raise FileExistsError(target)
        self.byte_files[target] = self.byte_files.pop(source)
        self.existing_paths.remove(source)
        self.existing_paths.add(target)

    def assert_drained(
        self, expected_events: list[tuple[object, ...]] | None = None
    ) -> None:
        if expected_events is not None:
            assert self.events == expected_events
        assert self.run_queue == []
        assert self.run_with_input_queue == []
        assert self.kill_queue == []
        assert self.is_file_queue == []
        assert self.read_text_queue == []
        assert self.stat_mtime_queue == []
        assert self.monotonic_queue == []


def _helper(
    action: str,
    sha: str | None = None,
    *,
    lease_dir: Path = _LEASE,
) -> tuple[str, ...]:
    argv = (
        sys.executable,
        str(_REPO / "tools" / "wave_land_window.py"),
        action,
        "--lease-dir",
        str(lease_dir),
        "--wave",
        _WAVE,
    )
    return argv + (("--main-sha", sha) if sha is not None else ())


def _preflight(fake: _FakeEffects, *, claim_guards: bool = True) -> None:
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
        _STATUS_ARGV,
        DW._CommandResult(0, ""),
    )
    fake.expect_run(_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_SUBMODULE_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_SUBMODULE_READY_ARGV, DW._CommandResult(0, ""))
    if not claim_guards:
        return
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    fake.expect_run(_history_provenance_argv())


def _prerun_status(
    fake: _FakeEffects,
    *,
    stdout: str = "",
    returncode: int = 0,
) -> None:
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(returncode, stdout))
    if returncode == 0 and not stdout:
        _fingerprint(fake)


def _fingerprint(fake: _FakeEffects, head: str = _SHA_A) -> None:
    fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(0, head + "\n"))
    fake.expect_run(_DIFF_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_SUBMODULE_STATUS_ARGV, DW._CommandResult(0, ""))


def _postrun_integrity(fake: _FakeEffects, head: str = _SHA_A) -> None:
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_SUBMODULE_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    _fingerprint(fake, head)


def _message_provenance(fake: _FakeEffects, result: object = None) -> None:
    fake.expect_run(
        _provenance_argv(),
        DW._CommandResult(0) if result is None else result,
    )


_BASE_PREFLIGHT_EVENTS = [
    ("run", ("git", "rev-parse", "--is-inside-work-tree"), _REPO, True),
    ("run", ("git", "rev-parse", "--show-toplevel"), _REPO, True),
    ("run", ("git", "symbolic-ref", "--quiet", "--short", "HEAD"), _REPO, True),
    ("run", _STATUS_ARGV, _REPO, True),
    ("run", _INDEX_FLAGS_ARGV, _REPO, True),
    ("run", _SUBMODULE_INDEX_FLAGS_ARGV, _REPO, True),
    ("run", _SUBMODULE_READY_ARGV, _REPO, True),
]
_PRECLAIM_GUARD_EVENTS = [
    (
        "run",
        ("git", "rev-list", "--count", "HEAD..main"),
        _REPO,
        True,
    ),
    ("run", _history_provenance_argv(), _REPO, True),
]
_PREFLIGHT_EVENTS = [*_BASE_PREFLIGHT_EVENTS, *_PRECLAIM_GUARD_EVENTS]
_FINGERPRINT_EVENTS = [
    ("run", ("git", "rev-parse", "HEAD"), _REPO, True),
    ("run", _DIFF_ARGV, _REPO, True),
    ("run", _SUBMODULE_STATUS_ARGV, _REPO, True),
]
_WAITER_GATE_EVENTS = [
    ("running_waiter_bytes_sha256",),
    ("tip_waiter_bytes_sha256", _REPO, _SHA_A),
    ("running_waiter_bytes_sha256",),
]
_POSTRUN_INTEGRITY_EVENTS = [
    ("run", _STATUS_ARGV, _REPO, True),
    ("run", _INDEX_FLAGS_ARGV, _REPO, True),
    ("run", _SUBMODULE_INDEX_FLAGS_ARGV, _REPO, True),
    *_FINGERPRINT_EVENTS,
]


def _claim(fake: _FakeEffects, sha: str, payload: str) -> None:
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, sha + "\n"))
    fake.expect_run(_helper("claim", sha), DW._CommandResult(0, payload))


def _acquired_payload(*, main_sha: str = _SHA_A) -> str:
    return json.dumps(
        {
            "state": "acquired",
            "holder": _HOLDER,
            "holder_self": True,
            "main_sha": main_sha,
            "age_seconds": 0,
            "source": {"status": "ok", "reason": None},
        }
    )


def _acquired(fake: _FakeEffects, sha: str = _SHA_A) -> None:
    _claim(fake, sha, _acquired_payload(main_sha=sha))


def _held_self_payload(**overrides: object) -> str:
    payload: dict[str, object] = {
        "state": "held-self",
        "holder": _HOLDER,
        "holder_self": True,
        "main_sha": _SHA_A,
        "age_seconds": 0,
        "source": {"status": "ok", "reason": None},
    }
    payload.update(overrides)
    return json.dumps(payload)


def _trusted_blob_git_argv(*args: str) -> tuple[str, ...]:
    return DW._trusted_blob_git_argv(_REPO, *args)


def _valid_receipt_arguments() -> dict[str, object]:
    fingerprint = DW._TreeFingerprint(
        digest="f" * 64,
        head_sha=_SHA_A,
        status_bytes=0,
        diff_bytes=0,
        submodule_status_bytes=0,
    )
    return {
        "wave": _WAVE,
        "holder": _HOLDER,
        "tested_main": _SHA_A,
        "tested_tip": _SHA_A,
        "command": ("python3", "tools/run_tests.py"),
        "resolved_runner_path": "tools/run_tests.py",
        "pre_fingerprint": fingerprint,
        "post_fingerprint": fingerprint,
        "waiter_blob_sha": _WAITER_BLOB,
        "environment": DW._AcceptanceEnvironment(None, None, None, None),
        "child_rc": 0,
        "verdict": "child-green",
        "log_sha256": "f" * 64,
        "effective_scheduler": "serial",
    }


def _launcher_receipt_bytes(**arguments: object) -> bytes:
    pre = arguments["pre_fingerprint"]
    post = arguments["post_fingerprint"]
    environment = arguments["environment"]
    assert isinstance(pre, DW._TreeFingerprint)
    assert isinstance(post, DW._TreeFingerprint)
    assert isinstance(environment, DW._AcceptanceEnvironment)
    log_sha256 = arguments["log_sha256"]
    if (
        not isinstance(log_sha256, str)
        or len(log_sha256) != 64
        or any(character not in "0123456789abcdef" for character in log_sha256)
    ):
        raise LA.LauncherFailure("invalid log digest")
    config = LA._Config(
        repo_root=_REPO,
        wave=arguments["wave"],
        lease_holder=arguments["holder"],
        tested_main=arguments["tested_main"],
        tested_tip=arguments["tested_tip"],
        launcher_source_revision="tested-main",
        launcher_blob_sha=_LAUNCHER_BLOB,
        launcher_executed_sha256=hashlib.sha256(
            _LAUNCHER_SOURCE
        ).hexdigest(),
        waiter_executed_sha256=_WAITER_BYTES_SHA256,
        waiter_blob_sha=arguments["waiter_blob_sha"],
        receipt_file=_RECEIPT_TEMP,
        log_file=_LOG,
        outcome_fd=10,
        completion_fd=11,
        pre_fingerprint=DW._fingerprint_json(pre),
        env_projection=environment.as_json(),
    )
    runner_argv = arguments["command"]
    LA._validate_config(config, runner_argv)
    payload = LA._receipt_bytes(
        config,
        runner_argv,
        arguments["child_rc"],
        hashlib.sha256(b"runner source").hexdigest(),
        log_sha256,
        {
            "effective_scheduler": arguments["effective_scheduler"],
            "post_fingerprint": DW._fingerprint_json(post),
            "red_check": None,
        },
    )
    if json.loads(payload)["verdict"] != arguments["verdict"]:
        raise LA.LauncherFailure("verdict mismatch")
    return payload

_LAUNCHER_START_EVENTS = [
    ("write_receipt_temp", _RECEIPT),
]
_LAUNCHER_FAILURE_CLEANUP_EVENTS = [
    ("unlink", _RECEIPT_TEMP),
]
_WAITER_BLOB_RESOLUTION_EVENTS = [
    (
        "run",
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        _REPO,
        True,
    ),
]
_SUCCESS_RECEIPT_EVENTS = [
    *_WAITER_BLOB_RESOLUTION_EVENTS,
    ("running_waiter_bytes_sha256",),
    ("run", ("git", "rev-parse", "main"), _REPO, True),
    ("run", _helper("claim", _SHA_A), _REPO, True),
    ("rename", _RECEIPT_TEMP, _RECEIPT),
]


def _lease_marker(tmp_path: Path) -> tuple[Path, Path, tuple[int, bytes]]:
    lease_dir = tmp_path / "lease"
    lease_dir.mkdir()
    lease_path = lease_dir / "acceptance.lease"
    lease_path.write_text(
        json.dumps(
            {
                "holder": _HOLDER,
                "main_sha": _SHA_A,
                "ttl": 2400,
            }
        )
        + "\n",
        encoding="ascii",
    )
    os.utime(lease_path, ns=(1_900_000_000_000_000_000,) * 2)
    before = (lease_path.stat().st_mtime_ns, lease_path.read_bytes())
    return lease_dir, lease_path, before


def _write_test_provenance_checker(repo: Path) -> None:
    checker = repo / "tools" / "check_ai_provenance.py"
    checker.write_text(
        "import argparse\n"
        "from pathlib import Path\n"
        "parser=argparse.ArgumentParser()\n"
        "parser.add_argument('--message-file', type=Path)\n"
        "args=parser.parse_args()\n"
        "expected='AI-Agent: product=codex; model=gpt-5; reasoning=high; "
        "role=author'\n"
        "raise SystemExit(0 if args.message_file is None or "
        "expected in args.message_file.read_text() else 1)\n",
        encoding="utf-8",
    )


def _write_path_aware_provenance_checker(repo: Path) -> None:
    checker = repo / "tools" / "check_ai_provenance.py"
    checker.write_text(
        "import argparse\n"
        "import subprocess\n"
        "from pathlib import Path\n"
        "parser=argparse.ArgumentParser()\n"
        "parser.add_argument('--message-file', type=Path)\n"
        "args=parser.parse_args()\n"
        "if args.message_file is None:\n"
        "    raise SystemExit(0)\n"
        "def changed(revision):\n"
        "    result=subprocess.run([\n"
        "        'git', 'diff', '--cached', '--name-only', '--no-renames',\n"
        "        '--diff-filter=ACMRDTUXB',\n"
        "        revision, '--',\n"
        "    ], capture_output=True, text=True, check=False)\n"
        "    if result.returncode != 0:\n"
        "        raise SystemExit(result.returncode)\n"
        "    return set(result.stdout.splitlines())\n"
        "merge_head=subprocess.run([\n"
        "    'git', 'rev-parse', '-q', '--verify', 'MERGE_HEAD',\n"
        "], capture_output=True, text=True, check=False)\n"
        "if merge_head.returncode != 0:\n"
        "    raise SystemExit(1)\n"
        "combined=changed('HEAD') & changed('MERGE_HEAD')\n"
        "implementation_basenames = {\n"
        "    'CMakeLists.txt', 'Makefile', 'GNUmakefile', 'pyproject.toml',\n"
        "    'pytest.ini',\n"
        "}\n"
        "implementation_prefixes = (\n"
        "    'orchestrator/', 'tools/', 'hooks/', '.github/', '.codex/',\n"
        "    'external/',\n"
        ")\n"
        "implementation_suffixes = (\n"
        "    '.py', '.sh', '.bash', '.c', '.cc', '.cpp', '.cxx',\n"
        "    '.h', '.hh', '.hpp', '.hxx', '.cmake', '.patch', '.diff',\n"
        ")\n"
        "def is_implementation(path):\n"
        "    normalized=path.removeprefix('./')\n"
        "    basename=normalized.rsplit('/', 1)[-1]\n"
        "    if basename in implementation_basenames:\n"
        "        return True\n"
        "    if normalized.endswith(implementation_suffixes):\n"
        "        return True\n"
        "    if normalized.startswith('patches/'):\n"
        "        return False\n"
        "    return (normalized.startswith(implementation_prefixes)\n"
        "            and not normalized.endswith(('.md', '.rst')))\n"
        "implementation={path for path in combined if is_implementation(path)}\n"
        "if not implementation:\n"
        "    raise SystemExit(0)\n"
        "expected='AI-Agent: product=codex; model=gpt-5; reasoning=high; "
        "role=author'\n"
        "raise SystemExit(0 if expected in args.message_file.read_text() else 1)\n",
        encoding="utf-8",
    )


def _write_exact_runner(repo: Path, source: str) -> None:
    body = textwrap.indent(source, "    ")
    if not body.endswith("\n"):
        body += "\n"
    (repo / "tools" / "run_tests.py").write_text(
        "def main(argv):\n"
        "    del argv\n"
        "    import hashlib as _binding_hashlib\n"
        "    import json as _binding_json\n"
        "    import os as _binding_os\n"
        "    _binding_fd = _binding_os.environ.get(\n"
        "        'IZANAGI_ACCEPTANCE_RUNNER_BINDING_FD')\n"
        "    _binding_nonce = _binding_os.environ.get(\n"
        "        'IZANAGI_ACCEPTANCE_RUNNER_BINDING_NONCE')\n"
        "    _binding_main = _binding_os.environ.get(\n"
        "        'IZANAGI_ACCEPTANCE_RUNNER_BINDING_TESTED_MAIN')\n"
        "    _binding_k = _binding_os.environ.get('IZANAGI_ACCEPTANCE_SHARDS')\n"
        "    if all((_binding_fd, _binding_nonce, _binding_main, _binding_k)):\n"
        "        _binding_source = __import__('pathlib').Path(__file__).read_bytes()\n"
        "        _binding_digest = _binding_hashlib.sha256(\n"
        "            _binding_source).hexdigest()\n"
        "        for _binding_index in range(int(_binding_k)):\n"
        "            _binding_report = {\n"
        "                'schema_version': 'dev-wave-runner-binding-report/v1',\n"
        "                'tested_main': _binding_main,\n"
        "                'nonce': _binding_nonce,\n"
        "                'runner_executed_sha256': _binding_digest,\n"
        "                'shard_count': int(_binding_k),\n"
        "                'shard_index': _binding_index,\n"
        "            }\n"
        "            _binding_line = (_binding_json.dumps(\n"
        "                _binding_report, ensure_ascii=True, sort_keys=True,\n"
        "                separators=(',', ':')) + '\\n').encode('ascii')\n"
        "            _binding_os.write(int(_binding_fd), _binding_line)\n"
        f"{body}"
        "    return 0\n",
        encoding="utf-8",
    )


def _real_waiter_repo(
    tmp_path: Path,
    *,
    wave: str,
) -> tuple[Path, Path, dict[str, str]]:
    repo = tmp_path / f"repo-{wave}"
    lease = tmp_path / f"lease-{wave}"
    repo.mkdir()
    lease.mkdir()
    tools = repo / "tools"
    tools.mkdir()
    shutil.copy2(_TOOL, tools / "dev_wave_wait.py")
    shutil.copy2(_LEASE_HELPER, tools / "wave_land_window.py")
    shutil.copy2(_LAUNCHER, tools / "acceptance_launcher.py")
    _write_exact_runner(
        repo,
        "print('IZANAGI_EFFECTIVE_SCHEDULER_V1 "
        "{\"effective_scheduler\":\"serial\"}')\n"
        "raise SystemExit(0)\n",
    )
    env = {
        **{
            key: value
            for key, value in os.environ.items()
            if key not in DW._GIT_ENV_KEYS
            and key not in {
                "PYTEST_ADDOPTS",
                "PYTEST_PLUGINS",
                "IZANAGI_TASK_RUN_ID",
                "IZANAGI_TASK_RUNS_ROOT",
            }
        },
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
        "PYTHONDONTWRITEBYTECODE": "1",
        "IZANAGI_ACCEPTANCE_SHARDS": "1",
    }

    def git(*args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=repo,
            env=env,
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    git("init", "-b", "main")
    git("add", "tools")
    git("commit", "-m", "base")
    git("checkout", "-b", f"worktree-{wave}")
    return repo, lease, env


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
    lease_dir: Path = _LEASE,
    lifecycle: object = None,
    receipt_file: Path = _RECEIPT,
    log_file: Path = _LOG,
    lease_optional: bool = False,
) -> object:
    return DW.run_acceptance(
        wave=_WAVE,
        lease_dir=lease_dir,
        merge_message_file=message,
        poll_seconds=30,
        max_wait_seconds=max_wait,
        command=_COMMAND,
        repo=_REPO,
        effects=fake.effects,
        receipt_file=receipt_file,
        log_file=log_file,
        owned_paths=owned_paths,
        lifecycle=lifecycle,
        lease_optional=lease_optional,
    )


def _queue_clean_acceptance_prefix(
    fake: _FakeEffects,
    *,
    claim_payload: str | None = None,
) -> None:
    _preflight(fake)
    _claim(
        fake,
        _SHA_A,
        _acquired_payload() if claim_payload is None else claim_payload,
    )
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    _prerun_status(fake)


class _RoutingAcceptanceEffects(_FakeEffects):
    def __init__(
        self,
        *,
        branch: str = f"feature-{_WAVE}",
        preclaim_behind: int = 0,
        behind: list[int] | None = None,
        message: str = "merge\nAI-Agent: codex\n",
        head_shas: list[str] | None = None,
        changed_paths: str = "",
        claim_payload: str | None = None,
        command_result: object = None,
        postclaim_rc: int = 0,
        final_main_sha: str | None = None,
        merge_result: object = None,
        preclaim_history_provenance_result: object = None,
        history_provenance_result: object = None,
        provenance_result: object = None,
        lease_dir: Path = _LEASE,
        remove_lease_on_release: bool = False,
    ) -> None:
        super().__init__()
        self.branch = branch
        self.preclaim_behind = preclaim_behind
        self.behind = list([0] if behind is None else behind)
        self.message = message
        self.head_shas = list([] if head_shas is None else head_shas)
        self.last_head_sha = self.head_shas[-1] if self.head_shas else _SHA_A
        self.changed_paths = changed_paths
        self.claim_payload = (
            _acquired_payload() if claim_payload is None else claim_payload
        )
        self.command_result = (
            DW._CommandResult(0) if command_result is None else command_result
        )
        self.postclaim_rc = postclaim_rc
        self.final_main_sha = final_main_sha
        self.merge_result = (
            DW._CommandResult(0) if merge_result is None else merge_result
        )
        self.preclaim_history_provenance_result = (
            DW._CommandResult(0)
            if preclaim_history_provenance_result is None
            else preclaim_history_provenance_result
        )
        self.history_provenance_result = (
            DW._CommandResult(0)
            if history_provenance_result is None
            else history_provenance_result
        )
        self.provenance_result = (
            DW._CommandResult(0)
            if provenance_result is None
            else provenance_result
        )
        self.lease_dir = lease_dir
        self.remove_lease_on_release = remove_lease_on_release
        self.claims = 0
        self.releases = 0
        self.submissions = 0
        self.main_reads = 0

    def run(self, argv: object, cwd: Path, capture: bool) -> object:
        actual = tuple(argv)
        self.events.append(("run", actual, cwd, capture))
        if actual == ("git", "rev-parse", "--is-inside-work-tree"):
            return DW._CommandResult(0, "true\n")
        if actual == ("git", "rev-parse", "--show-toplevel"):
            return DW._CommandResult(0, str(_REPO) + "\n")
        if actual == ("git", "symbolic-ref", "--quiet", "--short", "HEAD"):
            return DW._CommandResult(0, self.branch + "\n")
        if actual in {
            _STATUS_ARGV,
            _LEGACY_STATUS_ARGV,
        }:
            return DW._CommandResult(0, "")
        if actual in {_INDEX_FLAGS_ARGV, _SUBMODULE_INDEX_FLAGS_ARGV}:
            return DW._CommandResult(0, "")
        if actual == ("git", "rev-parse", "main"):
            self.main_reads += 1
            if self.main_reads == 2 and self.postclaim_rc != 0:
                return DW._CommandResult(self.postclaim_rc)
            if self.main_reads >= 3 and self.final_main_sha is not None:
                return DW._CommandResult(0, self.final_main_sha + "\n")
            return DW._CommandResult(0, _SHA_A + "\n")
        if actual == _helper("claim", _SHA_A, lease_dir=self.lease_dir):
            self.claims += 1
            if self.claims == 1:
                return DW._CommandResult(0, self.claim_payload)
            return DW._CommandResult(
                0,
                _held_self_payload(main_sha=_SHA_A),
            )
        if actual == ("git", "rev-list", "--count", "HEAD..main"):
            if self.claims == 0:
                return DW._CommandResult(0, f"{self.preclaim_behind}\n")
            assert self.behind
            return DW._CommandResult(0, f"{self.behind.pop(0)}\n")
        if actual == ("git", "diff", "--name-only", "HEAD...main"):
            return DW._CommandResult(0, self.changed_paths)
        if actual == ("git", "merge", "--no-ff", "--no-commit", "main"):
            return self.merge_result
        if actual == _history_provenance_argv():
            if self.claims == 0:
                return self.preclaim_history_provenance_result
            return self.history_provenance_result
        if actual == _provenance_argv():
            return self.provenance_result
        if actual in {
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
        }:
            return DW._CommandResult(0)
        if actual == ("git", "rev-parse", "HEAD"):
            if self.head_shas:
                self.last_head_sha = self.head_shas.pop(0)
            return DW._CommandResult(0, self.last_head_sha + "\n")
        if actual == (
            "git",
            "rev-parse",
            f"{self.last_head_sha}:tools/dev_wave_wait.py",
        ):
            return DW._CommandResult(0, _WAITER_BLOB + "\n")
        if actual == _helper(
            "claim",
            self.last_head_sha,
            lease_dir=self.lease_dir,
        ):
            self.claims += 1
            return DW._CommandResult(
                0,
                _held_self_payload(main_sha=self.last_head_sha),
            )
        if actual in {_DIFF_ARGV, _SUBMODULE_STATUS_ARGV}:
            return DW._CommandResult(0, "")
        if actual[:4] == ("git", "log", "-1", "--format=%B"):
            return DW._CommandResult(0, self.message)
        if actual == _COMMAND:
            self.submissions += 1
            if isinstance(self.command_result, BaseException):
                raise self.command_result
            return self.command_result
        if actual == _helper("release", lease_dir=self.lease_dir):
            self.releases += 1
            lease_path = self.lease_dir / "acceptance.lease"
            if self.remove_lease_on_release and lease_path.exists():
                lease_path.unlink()
            return DW._CommandResult(0, _RELEASE_JSON)
        if actual == ("git", "merge", "--abort"):
            return DW._CommandResult(0)
        if actual == ("git", "rev-parse", "-q", "--verify", "MERGE_HEAD"):
            return DW._CommandResult(1)
        raise AssertionError(f"unexpected run: {actual}")

    def is_file(self, path: Path) -> bool:
        self.events.append(("is_file", path))
        return True

    def read_text(self, path: Path) -> str:
        self.events.append(("read_text", path))
        return self.message


class _RetryAcceptanceEffects(_RoutingAcceptanceEffects):
    def __init__(
        self,
        *,
        command_results: list[int],
        logs: list[bytes],
        main_after_first: str = _SHA_A,
        head_shas: list[str] | None = None,
        advance_after_first: float = 0.0,
        advance_before_first_claim: float = 0.0,
        advance_on_claim: dict[int, float] | None = None,
        signal_on_claim: int | None = None,
        lease_dir: Path = _LEASE,
    ) -> None:
        super().__init__(
            behind=[0] * 16,
            head_shas=(
                [_SHA_A, _SHA_A] * len(command_results)
                if head_shas is None
                else head_shas
            ),
            lease_dir=lease_dir,
        )
        self.command_results = list(command_results)
        self.logs = list(logs)
        self.main_after_first = main_after_first
        self.advance_after_first = advance_after_first
        self.advance_before_first_claim = advance_before_first_claim
        self.advance_on_claim = dict(advance_on_claim or {})
        self.signal_on_claim = signal_on_claim
        self.inject_artifact_after_archive: Path | None = None
        self.env_after_archive: dict[str, str] | None = None
        self.lifecycle_to_observe: object | None = None
        self.submission_ownerships: list[object] = []
        self.claim_payload_overrides: dict[int, str] = {}
        self.lease_main_sha: str | None = None

    def run(self, argv: object, cwd: Path, capture: bool) -> object:
        actual = tuple(argv)
        if (
            actual == _history_provenance_argv()
            and self.claims == 0
            and self.advance_before_first_claim
        ):
            result = super().run(argv, cwd, capture)
            self.sleep(self.advance_before_first_claim)
            return result
        if actual == _COMMAND:
            self.events.append(("run", actual, cwd, capture))
            self.submissions += 1
            assert self.command_results
            return DW._CommandResult(self.command_results.pop(0))
        if actual == ("git", "rev-parse", "main"):
            self.events.append(("run", actual, cwd, capture))
            self.main_reads += 1
            main_sha = _SHA_A if self.submissions == 0 else self.main_after_first
            return DW._CommandResult(0, main_sha + "\n")
        if actual == ("git", "rev-list", "--count", "HEAD..main"):
            self.events.append(("run", actual, cwd, capture))
            return DW._CommandResult(0, "0\n")
        if len(actual) >= 5 and actual[2] == "claim" and actual[-2] == "--main-sha":
            self.events.append(("run", actual, cwd, capture))
            self.claims += 1
            if self.signal_on_claim == self.claims:
                raise DW._SignalReceived(signal.SIGTERM)
            main_sha = actual[-1]
            if self.lease_main_sha is None:
                self.lease_main_sha = main_sha
            payload = self.claim_payload_overrides.get(self.claims)
            if payload is None:
                payload = (
                    _acquired_payload(main_sha=main_sha)
                    if self.claims == 1
                    else _held_self_payload(main_sha=self.lease_main_sha)
                )
            if self.claims in self.advance_on_claim:
                self.sleep(self.advance_on_claim[self.claims])
            return DW._CommandResult(0, payload)
        return super().run(argv, cwd, capture)

    def run_logged(self, argv: object, cwd: Path, log_file: Path) -> object:
        result = self.run(argv, cwd, False)
        if self.lifecycle_to_observe is not None:
            self.submission_ownerships.append(
                self.lifecycle_to_observe.ownership
            )
        assert self.logs
        self.logged_bytes = self.logs.pop(0)
        self.byte_files[log_file] = self.logged_bytes
        self.existing_paths.add(log_file)
        if self.submissions == 1 and self.advance_after_first:
            self.sleep(self.advance_after_first)
        return result

    def archive_log(self, source: Path, target: Path) -> None:
        super().archive_log(source, target)
        if self.env_after_archive is not None:
            self.env = dict(self.env_after_archive)
        if self.inject_artifact_after_archive is not None:
            self.existing_paths.add(self.inject_artifact_after_archive)


class _RealLeaseRetryEffects(_RetryAcceptanceEffects):
    def __init__(
        self,
        *,
        lease_dir: Path,
        command_results: list[int],
        logs: list[bytes],
        competitor_wave: str | None = None,
        age_before_retry_seconds: int = 0,
    ) -> None:
        super().__init__(
            command_results=command_results,
            logs=logs,
            lease_dir=lease_dir,
        )
        self.competitor_wave = competitor_wave
        self.age_before_retry_seconds = age_before_retry_seconds
        self.competitor_claim: dict[str, object] | None = None
        self.renew_stats: list[
            tuple[os.stat_result, os.stat_result, dict[str, object]]
        ] = []
        self.release_results: list[dict[str, object]] = []
        self.aged_lease_stat: os.stat_result | None = None
        self.archive_lease_stat: os.stat_result | None = None

    def run(self, argv: object, cwd: Path, capture: bool) -> object:
        actual = tuple(argv)
        helper_prefix = (
            sys.executable,
            str(_REPO / "tools" / "wave_land_window.py"),
        )
        if actual[:2] == helper_prefix and len(actual) >= 7:
            action = actual[2]
            lease_dir = Path(actual[actual.index("--lease-dir") + 1])
            wave = actual[actual.index("--wave") + 1]
            self.events.append(("run", actual, cwd, capture))
            if action == "claim":
                main_sha = actual[actual.index("--main-sha") + 1]
                lease_path = lease_dir / "acceptance.lease"
                before = lease_path.stat() if lease_path.exists() else None
                result = WL.claim(
                    lease_dir,
                    wave,
                    main_sha,
                    DW._LEASE_TTL_SECONDS,
                )
                self.claims += 1
                if result.get("state") == "held-self" and before is not None:
                    self.renew_stats.append((before, lease_path.stat(), result))
                return DW._CommandResult(
                    0,
                    json.dumps(result, sort_keys=True) + "\n",
                )
            if action == "release":
                result = WL.release(lease_dir, wave)
                self.releases += 1
                self.release_results.append(result)
                return DW._CommandResult(
                    0,
                    json.dumps(result, sort_keys=True) + "\n",
                )
        return super().run(argv, cwd, capture)

    def run_logged(self, argv: object, cwd: Path, log_file: Path) -> object:
        result = super().run_logged(argv, cwd, log_file)
        lease_path = self.lease_dir / "acceptance.lease"
        if self.submissions == 1 and self.age_before_retry_seconds:
            aged_ns = time.time_ns() - self.age_before_retry_seconds * 1_000_000_000
            os.utime(lease_path, ns=(aged_ns, aged_ns))
            self.aged_lease_stat = lease_path.stat()
        if (
            self.submissions == 1
            and self.competitor_wave is not None
            and self.competitor_claim is None
        ):
            self.competitor_claim = WL.claim(
                self.lease_dir,
                self.competitor_wave,
                _SHA_A,
                DW._LEASE_TTL_SECONDS,
            )
        return result

    def archive_log(self, source: Path, target: Path) -> None:
        super().archive_log(source, target)
        self.archive_lease_stat = (
            self.lease_dir / "acceptance.lease"
        ).stat()


class _SubmoduleDirtyAcceptanceEffects(_RoutingAcceptanceEffects):
    def __init__(self, *, dirty_status_call: int) -> None:
        super().__init__(behind=[0, 0])
        self.dirty_status_call = dirty_status_call
        self.status_reads = 0

    def run(self, argv: object, cwd: Path, capture: bool) -> object:
        actual = tuple(argv)
        if actual in {_STATUS_ARGV, _LEGACY_STATUS_ARGV}:
            self.events.append(("run", actual, cwd, capture))
            self.status_reads += 1
            if (
                actual == _STATUS_ARGV
                and self.status_reads == self.dirty_status_call
            ):
                return DW._CommandResult(0, " m external/ccbench\n")
            return DW._CommandResult(0, "")
        return super().run(argv, cwd, capture)


def test_floor_job_staging_is_ignored_while_submissions_remain_tracked() -> None:
    lines = (_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    staging_pattern = "output/env/pegasus/floor/job-staging/"
    predecessor = "output/env/pegasus/silo_ladder_rung1/job-staging/"
    assert lines.count(staging_pattern) == 1
    assert lines.index(staging_pattern) == lines.index(predecessor) + 1
    assert [line for line in lines if "output/env/pegasus/floor/" in line] == [
        staging_pattern
    ]

    representative_relative = (
        staging_pattern + "0:873200.nqsv/hostname.stdout"
    )
    staging = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "--", representative_relative],
        cwd=_ROOT,
        check=False,
    )
    submissions = subprocess.run(
        [
            "git", "check-ignore", "--no-index", "-q", "--",
            "output/env/pegasus/floor/attempts/submissions/probe",
        ],
        cwd=_ROOT,
        check=False,
    )
    tracked_submissions = subprocess.run(
        [
            "git", "ls-files", "--",
            "output/env/pegasus/floor/attempts/submissions",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    tracked_staging = subprocess.run(
        ["git", "ls-files", "--", staging_pattern],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert staging.returncode == 0
    assert submissions.returncode == 1
    assert tracked_staging.returncode == 0
    assert tracked_staging.stdout == ""
    assert tracked_submissions.returncode == 0
    assert tracked_submissions.stdout


@pytest.mark.parametrize(
    ("prefix", "entry"),
    [("-", "external/uninitialized"), ("U", "external/conflicted")],
    ids=("uninitialized", "conflict"),
)
def test_submodule_not_ready_is_rejected_before_claim(
    prefix: str,
    entry: str,
) -> None:
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
        DW._CommandResult(0, f"feature-{_WAVE}\n"),
    )
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_SUBMODULE_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(
        _SUBMODULE_READY_ARGV,
        DW._CommandResult(0, f"{prefix}{_SHA_A} {entry}\n"),
    )

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(2, "preflight-submodule-ready")
    assert not any(
        event[0] == "run" and event[1] == _helper("claim", _SHA_A)
        for event in fake.events
    )
    fake.assert_drained()


def test_preflight_untracked_dirty_rejects_before_claim(tmp_path: Path) -> None:
    wave = "real-untracked"
    repo, lease, env = _real_waiter_repo(tmp_path, wave=wave)
    (repo / "untracked.py").write_text("foreign\n", encoding="utf-8")
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "dev_wave_wait.py"),
            "acceptance",
            "--wave",
            wave,
            "--lease-dir",
            str(lease),
            "--receipt-file",
            str(tmp_path / "untracked-receipt.json"),
            "--log-file",
            str(tmp_path / "untracked.log"),
            "--",
            "python3",
            "tools/run_tests.py",
        ],
        cwd=repo,
        env=env,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 2
    assert "stage=preflight-clean rc=2" in completed.stderr
    assert not (lease / "acceptance.lease").exists()
    assert not (tmp_path / "untracked-receipt.json").exists()


def test_prerun_untracked_dirty_blocks_submission_and_releases() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_A + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    _prerun_status(fake, stdout="?? untracked.py\n")
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "prerun-clean"
    assert not any(event[0] == "run" and event[1] == _COMMAND for event in fake.events)
    fake.assert_drained()


@pytest.mark.parametrize("tag", ["S", "h"], ids=("skip-worktree", "assume-unchanged"))
@pytest.mark.parametrize("source", ["root", "submodule"])
@pytest.mark.parametrize("phase", ["preflight", "postrun"])
def test_index_flags_fail_closed_before_claim_and_after_run(
    tag: str,
    source: str,
    phase: str,
) -> None:
    fake = _FakeEffects()
    flagged = f"{tag} hidden.py\0"
    if phase == "preflight":
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
        fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
        fake.expect_run(
            _INDEX_FLAGS_ARGV,
            DW._CommandResult(0, flagged if source == "root" else ""),
        )
        if source == "submodule":
            fake.expect_run(
                _SUBMODULE_INDEX_FLAGS_ARGV,
                DW._CommandResult(0, flagged),
            )
    else:
        _queue_clean_acceptance_prefix(fake)
        fake.expect_run(
            _COMMAND,
            DW._CommandResult(0),
            capture=False,
            unchanged_postrun=False,
        )
        fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
        fake.expect_run(
            _INDEX_FLAGS_ARGV,
            DW._CommandResult(0, flagged if source == "root" else ""),
        )
        if source == "submodule":
            fake.expect_run(
                _SUBMODULE_INDEX_FLAGS_ARGV,
                DW._CommandResult(0, flagged),
            )
        _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == f"{phase}-index-flags"
    if phase == "preflight":
        assert not any(
            event[0] == "run" and event[1] == _helper("claim", _SHA_A)
            for event in fake.events
        )
        assert not any(
            event[0] == "run" and event[1] == _COMMAND
            for event in fake.events
        )
    else:
        assert ("run", _COMMAND, _REPO, False) in fake.events
        assert ("run", _helper("release"), _REPO, True) in fake.events
    fake.assert_drained()


@pytest.mark.parametrize(
    ("kind", "status"),
    [
        ("tracked", " M tracked.py\n"),
        ("untracked", "?? untracked.py\n"),
        ("submodule", " m external/ccbench\n"),
    ],
)
def test_postrun_dirty_fails_closed_and_releases(
    kind: str,
    status: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    del kind
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, status))
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "postrun-clean"
    child_index = fake.events.index(("run", _COMMAND, _REPO, False))
    assert child_index < fake.events.index(
        ("run", _STATUS_ARGV, _REPO, True),
        child_index + 1,
    )
    assert status.strip() in capsys.readouterr().err
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    fake.assert_drained()


def test_postrun_clean_head_change_fails_fingerprint_and_releases() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake, _SHA_B)
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "postrun-fingerprint"
    fake.assert_drained()


@pytest.mark.parametrize("component", ["diff", "submodule-status"])
def test_postrun_fingerprint_binds_diff_and_submodule_status(
    component: str,
) -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_SUBMODULE_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(
        ("git", "rev-parse", "HEAD"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    fake.expect_run(
        _DIFF_ARGV,
        DW._CommandResult(0, "binary patch\n" if component == "diff" else ""),
    )
    fake.expect_run(
        _SUBMODULE_STATUS_ARGV,
        DW._CommandResult(
            0,
            f" {_SHA_B} external/ccbench\n"
            if component == "submodule-status"
            else "",
        ),
    )
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "postrun-fingerprint"
    fake.assert_drained()


def test_fingerprint_length_framing_disambiguates_concatenated_inputs() -> None:
    first = _FakeEffects()
    first.expect_run(
        ("git", "rev-parse", "HEAD"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    first.expect_run(_DIFF_ARGV, DW._CommandResult(0, "bc"))
    first.expect_run(_SUBMODULE_STATUS_ARGV, DW._CommandResult(0, ""))
    second = _FakeEffects()
    second.expect_run(
        ("git", "rev-parse", "HEAD"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    second.expect_run(_DIFF_ARGV, DW._CommandResult(0, "c"))
    second.expect_run(_SUBMODULE_STATUS_ARGV, DW._CommandResult(0, ""))

    first_fingerprint = DW._tree_fingerprint(
        first.effects,
        _REPO,
        "fingerprint-test",
        "a",
    )
    second_fingerprint = DW._tree_fingerprint(
        second.effects,
        _REPO,
        "fingerprint-test",
        "ab",
    )

    assert first_fingerprint.digest != second_fingerprint.digest
    assert first_fingerprint.status_bytes == 1
    assert second_fingerprint.status_bytes == 2
    first.assert_drained()
    second.assert_drained()


@pytest.mark.parametrize("phase", ["prerun", "postrun"])
def test_fingerprint_git_command_failure_fails_closed_and_releases(
    phase: str,
) -> None:
    fake = _FakeEffects()
    if phase == "prerun":
        _preflight(fake)
        _acquired(fake)
        fake.expect_run(
            ("git", "rev-parse", "main"),
            DW._CommandResult(0, _SHA_A + "\n"),
        )
        fake.expect_run(
            ("git", "rev-list", "--count", "HEAD..main"),
            DW._CommandResult(0, "0\n"),
        )
        fake.expect_run(
            ("git", "rev-list", "--count", "HEAD..main"),
            DW._CommandResult(0, "0\n"),
        )
        fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
        fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(9))
    else:
        _queue_clean_acceptance_prefix(fake)
        fake.expect_run(
            _COMMAND,
            DW._CommandResult(0),
            capture=False,
            unchanged_postrun=False,
        )
        fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
        fake.expect_run(_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
        fake.expect_run(_SUBMODULE_INDEX_FLAGS_ARGV, DW._CommandResult(0, ""))
        fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(9))
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == f"{phase}-fingerprint"
    assert outcome.source_rc == 9
    fake.assert_drained()


def test_nonzero_child_is_postchecked_before_propagation() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(23), capture=False)
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "acceptance-command"
    assert outcome.source_rc == 23
    child_index = fake.events.index(("run", _COMMAND, _REPO, False))
    release_index = fake.events.index(("run", _helper("release"), _REPO, True))
    assert ("run", _INDEX_FLAGS_ARGV, _REPO, True) in fake.events[child_index:release_index]
    assert not any(event[0] == "run_with_input" for event in fake.events)
    fake.assert_drained()


def test_postrun_dirty_overrides_nonzero_child_rc() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(23),
        capture=False,
        unchanged_postrun=False,
    )
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, "?? child-output\n"))
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "postrun-clean"
    fake.assert_drained()


def test_held_self_postrun_dirty_retains_lease() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake, claim_payload=_held_self_payload())
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, " M tracked.py\n"))

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "postrun-clean"
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


def test_unchanged_postrun_fingerprint_allows_success_and_retains_lease() -> None:
    fake = _FakeEffects()
    lifecycle = DW._AcceptanceLifecycle()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    assert outcome.rc == 0
    assert lifecycle.ownership is DW._LeaseOwnership.RETAINED
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


@pytest.mark.parametrize("scheduler", ["serial", "loadgroup"])
def test_success_receipt_binds_tip_argv_rc_fingerprints_holder_waiter_and_scheduler(
    scheduler: str,
) -> None:
    fake = _FakeEffects()
    fake.logged_bytes = _scheduler_marker(scheduler, relay=scheduler == "loadgroup")
    lifecycle = DW._AcceptanceLifecycle()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    assert outcome.rc == 0
    assert lifecycle.ownership is DW._LeaseOwnership.RETAINED
    assert lifecycle.receipt_published is True
    assert fake.receipt_published is True
    receipt = json.loads(fake.receipt_content)
    assert set(receipt) == {
        "schema_version", "authority_kind", "acceptance_wave", "lease_holder",
        "tested_main", "tested_tip", "argv", "resolved_runner_path", "child_rc",
        "pre_fingerprint", "post_fingerprint", "waiter_blob_sha",
        "env_projection", "verdict", "log_sha256", "checker_rc",
        "checker_status", "checker_blob_sha", "checker_receipt_sha256",
        "red_nodeids", "flake_nodeids", "effective_scheduler",
        "launcher_source_revision", "launcher_blob_sha",
        "launcher_executed_sha256", "waiter_executed_sha256",
        "runner_executed_sha256",
    }
    assert receipt["schema_version"] == "dev-wave-acceptance-receipt/v5"
    assert receipt["authority_kind"] == "dev-wave-acceptance-launcher"
    assert receipt["launcher_source_revision"] == "tested-main"
    assert receipt["launcher_blob_sha"] == _LAUNCHER_BLOB
    assert receipt["launcher_executed_sha256"] == hashlib.sha256(
        _LAUNCHER_SOURCE
    ).hexdigest()
    assert receipt["waiter_executed_sha256"] == _WAITER_BYTES_SHA256
    assert receipt["runner_executed_sha256"] == hashlib.sha256(
        b"runner source"
    ).hexdigest()
    assert receipt["acceptance_wave"] == _WAVE
    assert receipt["lease_holder"] == _HOLDER
    assert receipt["tested_main"] == _SHA_A
    assert receipt["tested_tip"] == _SHA_A
    assert receipt["argv"] == ["python3", "tools/run_tests.py"]
    assert receipt["resolved_runner_path"] == "tools/run_tests.py"
    assert receipt["child_rc"] == 0
    assert receipt["pre_fingerprint"] == receipt["post_fingerprint"]
    assert receipt["pre_fingerprint"]["head_sha"] == _SHA_A
    assert receipt["waiter_blob_sha"] == _WAITER_BLOB
    assert receipt["verdict"] == "child-green"
    assert receipt["log_sha256"] == hashlib.sha256(fake.logged_bytes).hexdigest()
    assert receipt["effective_scheduler"] == scheduler
    assert receipt["checker_rc"] is None
    assert receipt["checker_status"] is None
    assert receipt["checker_blob_sha"] is None
    assert receipt["checker_receipt_sha256"] is None
    assert receipt["red_nodeids"] == []
    assert receipt["flake_nodeids"] == []
    assert not any(event[0] == "run_with_input" for event in fake.events)
    assert receipt["env_projection"] == {
        "PYTEST_ADDOPTS": None,
        "PYTEST_PLUGINS": None,
        "IZANAGI_TASK_RUN_ID": None,
        "IZANAGI_TASK_RUNS_ROOT": None,
    }
    assert fake.events.count(("running_waiter_bytes_sha256",)) == 3
    assert fake.events.count(
        ("tip_waiter_bytes_sha256", _REPO, _SHA_A)
    ) == 1
    gate_index = fake.events.index(("running_waiter_bytes_sha256",))
    assert fake.events[gate_index - len(_FINGERPRINT_EVENTS):gate_index] == (
        _FINGERPRINT_EVENTS
    )
    assert gate_index < fake.events.index(
        ("tip_waiter_bytes_sha256", _REPO, _SHA_A)
    ) < fake.events.index(("run", _COMMAND, _REPO, False))
    assert fake.events.count(("run", _COMMAND, _REPO, False)) == 1
    fake.assert_drained()


def test_no_merge_waiter_bytes_mismatch_blocks_submission_and_releases() -> None:
    fake = _FakeEffects()
    fake.running_waiter_bytes_result = hashlib.sha256(b"version A").hexdigest()
    fake.tip_waiter_bytes_result = hashlib.sha256(b"version B").hexdigest()
    _queue_clean_acceptance_prefix(fake)
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "restart-required"
    detail = json.loads(outcome.detail)
    assert detail == {
        "reason": "receipt-waiter-sha256-mismatch",
        "observed": {
            "actual_sha256": fake.running_waiter_bytes_result,
            "expected_sha256": fake.tip_waiter_bytes_result,
            "tested_tip": _SHA_A,
        },
    }
    assert ("run", _COMMAND, _REPO, False) not in fake.events
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    assert fake.events.count(("run", _helper("release"), _REPO, True)) == 1
    fake.assert_drained()


@pytest.mark.parametrize(
    ("side", "value", "expected_source_rc", "expected_reason"),
    [
        (
            "running",
            DW._WaiterSourceUnavailable("PermissionError", 13),
            None,
            "running-source-binding-unavailable",
        ),
        ("running", OSError("read failed"), None, "running-source-read-failed"),
        (
            "running",
            UnicodeError("decode failed"),
            None,
            "running-source-read-failed",
        ),
        (
            "running",
            RuntimeError("unexpected"),
            None,
            "running-source-read-failed",
        ),
        ("tip", DW._TipWaiterBlobError("git-cat-file", 19), 19, "git-cat-file"),
        ("running", None, None, "running-sha256-type"),
        ("running", "", None, "running-sha256-format"),
        ("running", 7, None, "running-sha256-type"),
        ("running", "a" * 63, None, "running-sha256-format"),
        ("tip", None, None, "tip-sha256-type"),
        ("tip", "", None, "tip-sha256-format"),
        ("tip", 7, None, "tip-sha256-type"),
        ("tip", "a" * 63, None, "tip-sha256-format"),
    ],
    ids=(
        "binding-sentinel",
        "running-oserror",
        "running-unicode-error",
        "running-unexpected-error",
        "git-nonzero",
        "running-none",
        "running-empty",
        "running-invalid-type",
        "running-invalid-length",
        "tip-none",
        "tip-empty",
        "tip-invalid-type",
        "tip-invalid-length",
    ),
)
def test_waiter_bytes_unverifiable_is_restart_required_before_submission(
    side: str,
    value: object,
    expected_source_rc: int | None,
    expected_reason: str,
) -> None:
    fake = _FakeEffects()
    if side == "running":
        fake.running_waiter_bytes_result = value
    else:
        fake.tip_waiter_bytes_result = value
    _queue_clean_acceptance_prefix(fake)
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "restart-required"
    assert outcome.source_rc == expected_source_rc
    detail = json.loads(outcome.detail)
    assert set(detail) == {"reason", "observed"}
    assert detail["reason"] == "receipt-waiter-" + expected_reason
    observed = detail["observed"]
    assert set(observed) >= {
        "actual_sha256",
        "expected_sha256",
        "tested_tip",
    }
    assert observed["tested_tip"] == _SHA_A
    assert ("run", _COMMAND, _REPO, False) not in fake.events
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    assert fake.events.count(("run", _helper("release"), _REPO, True)) == 1
    fake.assert_drained()


def test_waiter_binding_failure_detail_omits_exception_message_and_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret_path = "/private/runtime/waiter-source.py"

    def fail_binding(source_file: object, module_spec: object) -> object:
        del source_file, module_spec
        raise OSError(13, "private binding message", secret_path)

    monkeypatch.setattr(DW, "_bind_waiter_source", fail_binding)
    unavailable = DW._initialize_waiter_source_binding()
    assert unavailable == DW._WaiterSourceUnavailable("PermissionError", 13)

    fake = _FakeEffects()
    fake.running_waiter_bytes_result = unavailable
    with pytest.raises(DW._StageFailure) as failure:
        DW._verify_waiter_source_bytes(fake.effects, _REPO, _SHA_A)

    assert failure.value.outcome == DW._Outcome(
        70,
        "restart-required",
        detail=json.dumps(
            {
                "reason": "receipt-waiter-running-source-binding-unavailable",
                "observed": {
                    "actual_sha256": None,
                    "errno": 13,
                    "exception_type": "PermissionError",
                    "expected_sha256": None,
                    "tested_tip": _SHA_A,
                },
            },
            separators=(",", ":"),
            sort_keys=True,
        ),
    )
    assert "private binding message" not in failure.value.outcome.detail
    assert secret_path not in failure.value.outcome.detail


def test_default_log_inspection_hashes_and_extracts_from_one_nofollow_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "acceptance.log"
    payload = b"x" * (DW._LOG_HASH_CHUNK_BYTES + 1) + b"\n" + _scheduler_marker(
        relay=True
    )
    path.write_bytes(payload)
    real_open = os.open
    calls: list[tuple[object, int]] = []

    def one_open(target: object, flags: int, *args: object) -> int:
        calls.append((target, flags))
        return real_open(target, flags, *args)

    monkeypatch.setattr(os, "open", one_open)
    monkeypatch.setattr(
        Path,
        "open",
        lambda *args, **kwargs: pytest.fail("acceptance log was opened twice"),
    )

    digest, scheduler = DW._default_inspect_acceptance_log(path)

    assert digest == hashlib.sha256(payload).hexdigest()
    assert scheduler == "serial"
    assert len(calls) == 1
    assert calls[0][1] & os.O_NOFOLLOW


def test_waiter_source_binding_accepts_regular_direct_source_and_inode_replacement(
    tmp_path: Path,
) -> None:
    tools = tmp_path / "tools"
    tools.mkdir()
    source = tools / "dev_wave_wait.py"
    payload = b"print('version A')\n"
    source.write_bytes(payload)

    binding = DW._bind_waiter_source(str(source), None)
    try:
        original_inode = os.stat(source, follow_symlinks=False).st_ino
        replacement = tools / "replacement.py"
        replacement.write_bytes(payload)
        os.replace(replacement, source)

        assert os.stat(source, follow_symlinks=False).st_ino != original_inode
        assert binding.initial_sha256 == hashlib.sha256(payload).hexdigest()
        assert binding.bytes_sha256() == binding.initial_sha256
        fake = _FakeEffects()
        fake.running_waiter_bytes_sha256 = binding.bytes_sha256
        fake.tip_waiter_bytes_result = binding.initial_sha256
        DW._verify_waiter_source_bytes(fake.effects, tmp_path, _SHA_A)
    finally:
        binding.close()


def test_waiter_source_binding_accepts_spec_with_same_file_origin(
    tmp_path: Path,
) -> None:
    tools = tmp_path / "tools"
    tools.mkdir()
    source = tools / "dev_wave_wait.py"
    payload = b"print('same origin')\n"
    source.write_bytes(payload)
    spec = importlib.util.spec_from_file_location("same_origin_waiter", source)
    assert spec is not None and spec.loader is not None

    binding = DW._bind_waiter_source(str(source), spec)
    try:
        assert binding.initial_sha256 == hashlib.sha256(payload).hexdigest()
        assert binding.bytes_sha256() == binding.initial_sha256
    finally:
        binding.close()


def test_waiter_source_binding_rejects_symlink(tmp_path: Path) -> None:
    tools = tmp_path / "tools"
    tools.mkdir()
    target = tmp_path / "target.py"
    target.write_text("print('target')\n", encoding="utf-8")
    (tools / "dev_wave_wait.py").symlink_to(target)

    with pytest.raises(OSError):
        DW._bind_waiter_source(str(tools / "dev_wave_wait.py"), None)


def test_waiter_source_binding_rejects_non_regular(tmp_path: Path) -> None:
    tools = tmp_path / "tools"
    tools.mkdir()
    (tools / "dev_wave_wait.py").mkdir()

    with pytest.raises(OSError):
        DW._bind_waiter_source(str(tools / "dev_wave_wait.py"), None)


def test_tip_waiter_bytes_sha256_hashes_blob_without_text_decoding(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    tools = repo / "tools"
    tools.mkdir(parents=True)
    payload = b"valid prefix\n\xff\xfe\x80\n"
    (tools / "dev_wave_wait.py").write_bytes(payload)
    env = {
        **{key: value for key, value in os.environ.items() if key not in DW._GIT_ENV_KEYS},
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repo,
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        ["git", "add", "tools/dev_wave_wait.py"],
        cwd=repo,
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        ["git", "commit", "-m", "binary waiter"],
        cwd=repo,
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert DW._default_tip_waiter_bytes_sha256(repo, "HEAD") == (
        hashlib.sha256(payload).hexdigest()
    )


def test_default_log_inspection_rejects_fstat_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "changing.log"
    path.write_bytes(_scheduler_marker())
    real_fstat = os.fstat
    calls = 0

    def changed_after_read(fd: int):
        nonlocal calls
        calls += 1
        value = real_fstat(fd)
        if calls == 1:
            return value
        fields = list(value)
        fields[6] += 1
        return os.stat_result(fields)

    monkeypatch.setattr(os, "fstat", changed_after_read)

    with pytest.raises(DW._StageFailure) as failure:
        DW._default_inspect_acceptance_log(path)

    assert failure.value.outcome.stage == "acceptance-scheduler-attestation"
    assert '"reason":"log-changed"' in failure.value.outcome.detail


def test_default_log_inspection_rejects_short_read_with_stable_fstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "short-read.log"
    path.write_bytes(_scheduler_marker())
    real_read = os.read
    calls = 0

    def short_read(fd: int, size: int) -> bytes:
        nonlocal calls
        calls += 1
        if calls == 1:
            return real_read(fd, 1)
        return b""

    monkeypatch.setattr(os, "read", short_read)

    with pytest.raises(DW._StageFailure) as failure:
        DW._default_inspect_acceptance_log(path)

    assert failure.value.outcome.stage == "acceptance-scheduler-attestation"
    assert '"reason":"log-changed"' in failure.value.outcome.detail
    assert '"total_read":1' in failure.value.outcome.detail


def test_default_log_inspection_rejects_mtime_ns_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "mtime-change.log"
    path.write_bytes(_scheduler_marker())
    real_fstat = os.fstat
    calls = 0

    def changed_after_read(fd: int):
        nonlocal calls
        calls += 1
        value = real_fstat(fd)
        if calls == 1:
            return value
        fields = list(value)
        fields[8] += 1
        return os.stat_result(fields)

    monkeypatch.setattr(os, "fstat", changed_after_read)

    with pytest.raises(DW._StageFailure) as failure:
        DW._default_inspect_acceptance_log(path)

    assert failure.value.outcome.stage == "acceptance-scheduler-attestation"
    assert '"reason":"log-changed"' in failure.value.outcome.detail


def test_relayed_loadgroup_literal_is_accepted() -> None:
    assert _RELAYED_LOADGROUP_MARKER == (
        b'| IZANAGI_EFFECTIVE_SCHEDULER_V1 {"effective_scheduler":"loadgroup"}'
    )
    _digest, payloads = DW._scan_acceptance_log_chunks(
        [_RELAYED_LOADGROUP_MARKER + b"\n"]
    )
    assert DW._scheduler_from_marker_payloads(payloads) == "loadgroup"


def test_shard_merger_output_exposes_exactly_one_waiter_accepted_marker(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from tools import acceptance_shards

    acceptance_shards._emit_merged(
        acceptance_shards.MergeResult(
            0,
            "ok",
            scheduler="loadgroup",
            universe=("orchestrator/tests/test_x.py::test_x",),
            terminal_counts=(("passed", 1),),
        )
    )
    output = capsys.readouterr().out.encode("ascii")
    _digest, payloads = DW._scan_acceptance_log_chunks([output])
    assert len(payloads) == 1
    assert DW._scheduler_from_marker_payloads(payloads) == "loadgroup"


def test_scanner_has_constant_extra_memory_for_huge_unterminated_line() -> None:
    chunk = b"x" * 65536

    def scan_peak(repetitions: int) -> tuple[int, str]:
        chunks = itertools.chain(
            itertools.repeat(chunk, repetitions),
            (b"\n" + _scheduler_marker(),),
        )
        tracemalloc.start()
        try:
            _digest, payloads = DW._scan_acceptance_log_chunks(chunks)
            scheduler = DW._scheduler_from_marker_payloads(payloads)
            _current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        return peak, scheduler

    small_peak, small_scheduler = scan_peak(2)
    large_peak, large_scheduler = scan_peak(128)

    assert (small_scheduler, large_scheduler) == ("serial", "serial")
    assert large_peak <= small_peak + 64 * 1024


def test_scanner_bounds_payload_and_stops_retaining_after_second_marker() -> None:
    oversized = (
        DW._EFFECTIVE_SCHEDULER_PREFIX
        + b"x" * (DW._MARKER_PAYLOAD_MAX_BYTES * 2)
        + b"\n"
    )
    _digest, payloads = DW._scan_acceptance_log_chunks(
        [
            oversized,
            _scheduler_marker(),
            _scheduler_marker("loadgroup", relay=True) * 32,
        ]
    )

    assert len(payloads) == 2
    assert len(payloads[0]) == DW._MARKER_PAYLOAD_MAX_BYTES + 1
    with pytest.raises(DW._StageFailure) as failure:
        DW._scheduler_from_marker_payloads(payloads)
    assert '"reason":"marker-count"' in failure.value.outcome.detail


def test_detail_text_normalizer_bounds_controls_and_non_ascii() -> None:
    assert DW._DETAIL_TEXT_MAX_BYTES == 256
    assert DW._bounded_detail_text("line\n\t\x00é") == (
        "line\\x0a\\x09\\x00\\xc3\\xa9"
    )
    assert DW._bounded_detail_text("x" * 300) == "x" * 253 + "..."

    class HostileRepr:
        def __repr__(self) -> str:
            raise AssertionError("repr must not run")

    assert DW._bounded_detail_text(HostileRepr()) == "HostileRepr"


def test_detail_text_normalizer_preserves_exact_byte_limit() -> None:
    value = "x" * 256

    normalized = DW._bounded_detail_text(value)

    assert normalized == value
    assert len(normalized.encode("ascii")) == 256


def test_attestation_detail_has_fixed_serialized_byte_limit() -> None:
    detail = DW._attestation_detail(
        "bounded-detail",
        {f"field-{index}": "x" * 1000 for index in range(32)},
    )

    assert DW._ATTESTATION_DETAIL_MAX_BYTES == 2048
    assert len(detail.encode("ascii")) <= 2048
    assert json.loads(detail) == {
        "reason": "bounded-detail",
        "observed": {
            "detail_truncated": True,
            "serialized_bytes": 8670,
        },
    }


def test_attestation_detail_preserves_exact_serialized_byte_limit() -> None:
    observed = {f"f{index}": "x" * 240 for index in range(8)}
    observed["p"] = "x" * 23
    expected = {"reason": "boundary", "observed": observed}

    detail = DW._attestation_detail("boundary", observed)

    assert len(detail.encode("ascii")) == 2048
    assert detail == json.dumps(expected, separators=(",", ":"), sort_keys=True)
    assert json.loads(detail) == expected


def test_diagnostic_generation_failure_preserves_receipt_stage_and_rc() -> None:
    class ExplodingString(str):
        def encode(self, *args: object, **kwargs: object) -> bytes:
            del args, kwargs
            raise RuntimeError("NORMALIZER-SECRET-SENTINEL")

    fake = _FakeEffects()
    argv = ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py")
    fake.expect_run(argv, DW._CommandResult(0, "not-a-sha\n"))

    with pytest.raises(DW._StageFailure) as failure:
        DW._blob_sha(
            fake.effects,
            _REPO,
            _SHA_A,
            "tools/dev_wave_wait.py",
            "acceptance-receipt",
            diagnostic_reason=ExplodingString("receipt-waiter-blob"),
        )

    outcome = failure.value.outcome
    assert (outcome.rc, outcome.stage) == (70, "acceptance-receipt")
    assert outcome.detail is not None
    assert len(outcome.detail.encode("ascii")) <= 2048
    assert json.loads(outcome.detail) == {
        "reason": "detail",
        "observed": {"detail_generation_failed": True},
    }
    assert "NORMALIZER-SECRET-SENTINEL" not in outcome.detail
    fake.assert_drained()


def test_exception_normalizer_ignores_hostile_errno_accessor() -> None:
    class HostileErrno(OSError):
        @property
        def errno(self) -> int:
            raise RuntimeError("ERRNO-SECRET-SENTINEL")

    observed = DW._exception_observed(HostileErrno("MESSAGE-SECRET-SENTINEL"))

    assert observed == {"exception_type": "HostileErrno", "errno": None}
    assert "SECRET" not in json.dumps(observed)


def test_launcher_verdict_mismatch_omits_hostile_text() -> None:
    class ExplodingString(str):
        def encode(self, *args: object, **kwargs: object) -> bytes:
            del args, kwargs
            raise RuntimeError("NORMALIZER-SECRET-SENTINEL")

    arguments = _valid_receipt_arguments()
    arguments["verdict"] = ExplodingString("unknown")

    with pytest.raises(LA.LauncherFailure) as failure:
        _launcher_receipt_bytes(**arguments)

    assert "NORMALIZER-SECRET-SENTINEL" not in str(failure.value)


def test_unknown_scheduler_is_rejected_by_launcher() -> None:
    fake = _FakeEffects()
    fake.logged_bytes = _scheduler_marker("unknown")
    lifecycle = DW._AcceptanceLifecycle()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    _release(fake)

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    assert outcome == DW._Outcome(70, "acceptance-launcher", source_rc=1)
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    fake.assert_drained()


_INVALID_SCHEDULER_LOGS = (
    ("missing", b"pytest completed without marker\n"),
    ("malformed-json", DW._EFFECTIVE_SCHEDULER_PREFIX + b"{\n"),
    (
        "duplicate-key",
        DW._EFFECTIVE_SCHEDULER_PREFIX
        + b'{"effective_scheduler":"serial","effective_scheduler":"serial"}\n',
    ),
    ("mixed-form-duplicate", _scheduler_marker() + _scheduler_marker(relay=True)),
    (
        "same-line-duplicate",
        _scheduler_marker().rstrip(b"\n") + _scheduler_marker(),
    ),
    (
        "conflicting-lines",
        _scheduler_marker("serial") + _scheduler_marker("loadgroup", relay=True),
    ),
    ("unknown-value", _scheduler_marker("mystery")),
    ("non-string-value", _scheduler_marker(1)),
    (
        "field-drift",
        DW._EFFECTIVE_SCHEDULER_PREFIX
        + b'{"effective_scheduler":"serial","extra":true}\n',
    ),
)


@pytest.mark.parametrize(
    ("case", "logged_bytes"),
    _INVALID_SCHEDULER_LOGS,
    ids=[case for case, _ in _INVALID_SCHEDULER_LOGS],
)
def test_scheduler_attestation_is_fail_closed_for_green_command(
    case: str,
    logged_bytes: bytes,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = _FakeEffects()
    fake.logged_bytes = logged_bytes
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70, case
    assert outcome.stage == "acceptance-scheduler-attestation", case
    assert outcome.detail is not None
    assert fake.receipt_content is None
    assert not any(event[0] == "run_with_input" for event in fake.events)
    DW._print_outcome(outcome)
    diagnostic = capsys.readouterr().err
    attestation_diagnostics = [
        line
        for line in diagnostic.splitlines()
        if "error: stage=acceptance-scheduler-attestation" in line
    ]
    assert len(attestation_diagnostics) == 1
    assert '"reason":' in attestation_diagnostics[0]
    assert '"observed":' in attestation_diagnostics[0]
    fake.assert_drained()


def test_failed_acceptance_does_not_launch_red_checker() -> None:
    """checker 呼出しを戻すと strict fake の未期待 command で赤になる pin。"""

    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(1), capture=False)
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, "acceptance-command", 1)
    assert not any(
        event[0] in {"run", "run_with_input"}
        and isinstance(event[1], tuple)
        and any(
            isinstance(argument, str)
            and "tools/check_acceptance_reds.py" in argument
            for argument in event[1]
        )
        for event in fake.events
    )
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    fake.assert_drained()


@pytest.mark.parametrize(
    "raw_child_rc",
    [2, 13, 16, 23, -signal.SIGTERM],
    ids=("pytest-usage", "deletion-gate", "dispatch", "audit", "signal"),
)
def test_non_pytest_failure_rc_rejected_without_extra_command(
    raw_child_rc: int,
) -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(raw_child_rc),
        capture=False,
    )
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(
        70,
        "acceptance-command",
        DW._normalize_child_rc(raw_child_rc),
    )
    assert not any(event[0] == "run_with_input" for event in fake.events)
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    fake.assert_drained()


@pytest.mark.parametrize(
    "postcheck",
    ("postrun-clean", "postrun-index-flags", "postrun-fingerprint"),
)
def test_postrun_integrity_failure_precedes_child_failure(postcheck: str) -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(1),
        capture=False,
        unchanged_postrun=False,
    )
    if postcheck == "postrun-clean":
        fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, " M changed.py\n"))
    elif postcheck == "postrun-index-flags":
        fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
        fake.expect_run(_INDEX_FLAGS_ARGV, DW._CommandResult(0, "S hidden.py\0"))
    else:
        _postrun_integrity(fake, head=_SHA_B)
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, postcheck)
    assert not any(event[0] == "run_with_input" for event in fake.events)
    fake.assert_drained()


@pytest.mark.parametrize(
    ("field", "value", "expected_observed"),
    (
        (
            "tested_main",
            "bad",
            {
                "tested_main": "bad",
                "tested_main_valid": False,
                "tested_tip": None,
                "tested_tip_valid": None,
                "log_sha256": None,
                "log_sha256_valid": None,
                "effective_scheduler": None,
                "scheduler_is_str": None,
                "scheduler_in_allowed": None,
            },
        ),
        (
            "tested_tip",
            "bad",
            {
                "tested_main": _SHA_A,
                "tested_main_valid": True,
                "tested_tip": "bad",
                "tested_tip_valid": False,
                "log_sha256": None,
                "log_sha256_valid": None,
                "effective_scheduler": None,
                "scheduler_is_str": None,
                "scheduler_in_allowed": None,
            },
        ),
        (
            "log_sha256",
            "bad",
            {
                "tested_main": _SHA_A,
                "tested_main_valid": True,
                "tested_tip": _SHA_A,
                "tested_tip_valid": True,
                "log_sha256": "bad",
                "log_sha256_valid": False,
                "effective_scheduler": None,
                "scheduler_is_str": None,
                "scheduler_in_allowed": None,
            },
        ),
        (
            "effective_scheduler",
            7,
            {
                "tested_main": _SHA_A,
                "tested_main_valid": True,
                "tested_tip": _SHA_A,
                "tested_tip_valid": True,
                "log_sha256": "f" * 64,
                "log_sha256_valid": True,
                "effective_scheduler": "int",
                "scheduler_is_str": False,
                "scheduler_in_allowed": None,
            },
        ),
        (
            "effective_scheduler",
            "mystery",
            {
                "tested_main": _SHA_A,
                "tested_main_valid": True,
                "tested_tip": _SHA_A,
                "tested_tip_valid": True,
                "log_sha256": "f" * 64,
                "log_sha256_valid": True,
                "effective_scheduler": "mystery",
                "scheduler_is_str": True,
                "scheduler_in_allowed": False,
            },
        ),
    ),
    ids=(
        "tested-main",
        "tested-tip",
        "log-sha256",
        "scheduler-type",
        "scheduler-allowed",
    ),
)
def test_launcher_receipt_rejects_invalid_fields(
    field: str,
    value: object,
    expected_observed: dict[str, object],
) -> None:
    del expected_observed
    arguments = _valid_receipt_arguments()
    arguments[field] = value

    with pytest.raises(LA.LauncherFailure):
        _launcher_receipt_bytes(**arguments)


def test_launcher_receipt_rejects_nonzero_child_for_child_green() -> None:
    arguments = _valid_receipt_arguments()
    arguments["child_rc"] = 1

    with pytest.raises(LA.LauncherFailure):
        _launcher_receipt_bytes(**arguments)


def test_child_green_receipt_does_not_require_main_tip_runner_equality() -> None:
    arguments = _valid_receipt_arguments()
    fingerprint = DW._TreeFingerprint(
        digest="e" * 64,
        head_sha=_SHA_B,
        status_bytes=0,
        diff_bytes=0,
        submodule_status_bytes=0,
    )
    arguments.update(
        tested_tip=_SHA_B,
        pre_fingerprint=fingerprint,
        post_fingerprint=fingerprint,
    )

    receipt = json.loads(_launcher_receipt_bytes(**arguments))

    assert receipt["verdict"] == "child-green"
    assert receipt["tested_main"] == _SHA_A
    assert receipt["tested_tip"] == _SHA_B
    assert receipt["red_nodeids"] == []
    assert receipt["flake_nodeids"] == []


def test_launcher_receipt_rejects_unknown_verdict() -> None:
    arguments = _valid_receipt_arguments()
    arguments["verdict"] = "v" * 300

    with pytest.raises(LA.LauncherFailure) as failure:
        _launcher_receipt_bytes(**arguments)

    assert str(failure.value) == "verdict mismatch"


def test_launcher_receipt_invalid_argv_omits_exception_text() -> None:
    sentinel = "ENCODE-SECRET-SENTINEL"

    class Unencodable:
        def __repr__(self) -> str:
            return sentinel

    arguments = _valid_receipt_arguments()
    arguments["command"] = (Unencodable(),)

    with pytest.raises(LA.LauncherFailure) as failure:
        _launcher_receipt_bytes(**arguments)

    assert sentinel not in str(failure.value)


def _assert_launcher_rc_zero_publishes() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    _postrun_integrity(fake)
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.launcher_outcome_without_runner = True
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    fake.expect_run(
        _helper("claim", _SHA_A),
        DW._CommandResult(0, _held_self_payload()),
    )

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(0)
    assert fake.receipt_content is not None
    assert fake.receipt_published is True
    fake.assert_drained()


def test_m8_launcher_nonzero_does_not_publish_receipt() -> None:
    _assert_launcher_rc_zero_publishes()
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    _postrun_integrity(fake)
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.launcher_outcome_without_runner = True
    fake.launcher_returncode = 70
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "acceptance-launcher"
    assert outcome.source_rc == 70
    assert fake.launcher_argv is not None
    assert fake.receipt_content is not None
    assert fake.receipt_published is False
    assert not any(
        event[:2] == ("run", _COMMAND) for event in fake.events
    )
    fake.assert_drained()


def test_waiter_bound_bytes_are_rechecked_after_launcher_exit() -> None:
    fake = _FakeEffects()
    fake.running_waiter_bytes_result = [
        _WAITER_BYTES_SHA256,
        _WAITER_BYTES_SHA256,
        hashlib.sha256(b"changed waiter source").hexdigest(),
    ]
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, "acceptance-launcher")
    assert fake.receipt_published is False
    assert ("unlink", _RECEIPT_TEMP) in fake.events
    fake.assert_drained()


def test_trusted_launcher_source_never_falls_back_to_tip() -> None:
    fake = _FakeEffects()
    tree = (
        f"100644 blob {_LAUNCHER_BLOB}\ttools/acceptance_launcher.py\0"
    ).encode("ascii")
    fake.expect_run_with_input(
        DW._trusted_blob_git_argv(
            _REPO,
            "ls-tree",
            "-z",
            _SHA_A,
            "--",
            "tools/acceptance_launcher.py",
        ),
        b"",
        DW._BinaryCommandResult(0, tree),
    )
    fake.expect_run_with_input(
        DW._trusted_blob_git_argv(
            _REPO, "cat-file", "blob", _LAUNCHER_BLOB
        ),
        b"",
        DW._BinaryCommandResult(0, _LAUNCHER_SOURCE),
    )
    fake.expect_run_with_input(
        DW._trusted_blob_git_argv(
            _REPO, "hash-object", "--stdin", "--no-filters"
        ),
        _LAUNCHER_SOURCE,
        DW._BinaryCommandResult(0, (_LAUNCHER_BLOB + "\n").encode("ascii")),
    )

    binding = DW._default_launcher_source(
        fake.effects,
        _REPO,
        _SHA_A,
        _SHA_B,
        "acceptance-launcher",
    )

    assert binding == DW._LauncherBinding(
        _LAUNCHER_SOURCE,
        _LAUNCHER_BLOB,
        "tested-main",
    )
    assert not any(
        _SHA_B in event[1] if len(event) > 1 else False
        for event in fake.events
    )
    fake.assert_drained()


def test_missing_main_launcher_selects_tested_tip_bootstrap() -> None:
    fake = _FakeEffects()
    tip_tree = (
        f"100644 blob {_LAUNCHER_BLOB}\ttools/acceptance_launcher.py\0"
    ).encode("ascii")
    for revision, tree in ((_SHA_A, b""), (_SHA_B, tip_tree)):
        fake.expect_run_with_input(
            DW._trusted_blob_git_argv(
                _REPO,
                "ls-tree",
                "-z",
                revision,
                "--",
                "tools/acceptance_launcher.py",
            ),
            b"",
            DW._BinaryCommandResult(0, tree),
        )
    fake.expect_run_with_input(
        DW._trusted_blob_git_argv(
            _REPO, "cat-file", "blob", _LAUNCHER_BLOB
        ),
        b"",
        DW._BinaryCommandResult(0, _LAUNCHER_SOURCE),
    )
    fake.expect_run_with_input(
        DW._trusted_blob_git_argv(
            _REPO, "hash-object", "--stdin", "--no-filters"
        ),
        _LAUNCHER_SOURCE,
        DW._BinaryCommandResult(0, (_LAUNCHER_BLOB + "\n").encode("ascii")),
    )

    binding = DW._default_launcher_source(
        fake.effects,
        _REPO,
        _SHA_A,
        _SHA_B,
        "acceptance-launcher",
    )

    assert binding.source_revision == "tested-tip-bootstrap"
    assert binding.blob_sha == _LAUNCHER_BLOB
    fake.assert_drained()


def test_launcher_argv_and_runner_tail_are_exact() -> None:
    fingerprint = DW._TreeFingerprint(
        digest="f" * 64,
        head_sha=_SHA_A,
        status_bytes=0,
        diff_bytes=0,
        submodule_status_bytes=0,
    )
    base = DW._launcher_argv(
        repo=_REPO,
        wave=_WAVE,
        holder=_HOLDER,
        tested_main=_SHA_A,
        tested_tip=_SHA_B,
        binding=DW._LauncherBinding(
            _LAUNCHER_SOURCE, _LAUNCHER_BLOB, "tested-main"
        ),
        waiter_executed_sha256=_WAITER_BYTES_SHA256,
        waiter_blob_sha=_WAITER_BLOB,
        receipt_temp=_RECEIPT_TEMP,
        log_file=_LOG,
        pre_fingerprint=fingerprint,
        environment=DW._AcceptanceEnvironment(None, None, None, None),
    )
    actual = DW._launcher_process_argv(base, 101, 102)

    assert actual == (
        sys.executable,
        "-I",
        "-c",
        DW._LAUNCHER_BOOTSTRAP,
        "/repo/tools/acceptance_launcher.py",
        "--repo-root",
        "/repo",
        "--wave",
        _WAVE,
        "--lease-holder",
        _HOLDER,
        "--tested-main",
        _SHA_A,
        "--tested-tip",
        _SHA_B,
        "--launcher-source-revision",
        "tested-main",
        "--launcher-blob-sha",
        _LAUNCHER_BLOB,
        "--waiter-executed-sha256",
        _WAITER_BYTES_SHA256,
        "--waiter-blob-sha",
        _WAITER_BLOB,
        "--receipt-file",
        str(_RECEIPT_TEMP),
        "--log-file",
        str(_LOG),
        "--pre-fingerprint-json",
        (
            '{"diff_bytes":0,"digest":"' + "f" * 64
            + '","head_sha":"' + _SHA_A
            + '","status_bytes":0,"submodule_status_bytes":0}'
        ),
        "--env-projection-json",
        (
            '{"IZANAGI_TASK_RUNS_ROOT":null,"IZANAGI_TASK_RUN_ID":null,'
            '"PYTEST_ADDOPTS":null,"PYTEST_PLUGINS":null}'
        ),
        "--outcome-fd",
        "101",
        "--completion-fd",
        "102",
        "--",
        "python3",
        "tools/run_tests.py",
    )
    assert "--launcher-executed-sha256" not in base
    assert '"--launcher-executed-sha256"' in DW._LAUNCHER_BOOTSTRAP


class _CapturedLauncherProcess:
    class _Stdin:
        def __init__(self) -> None:
            self.content = bytearray()
            self.closed = False

        def write(self, content: bytes) -> int:
            self.content.extend(content)
            return len(content)

        def close(self) -> None:
            self.closed = True

    def __init__(self) -> None:
        self.stdin = self._Stdin()
        self.returncode = 0

    def poll(self) -> int:
        return self.returncode

    def wait(self, timeout: object = None) -> int:
        del timeout
        return self.returncode

    def terminate(self) -> None:
        self.returncode = -signal.SIGTERM

    def kill(self) -> None:
        self.returncode = -signal.SIGKILL


def _capture_default_launcher_start(
    monkeypatch: pytest.MonkeyPatch,
    current_site: object,
    queue_result: object = (
        True,
        "キュー gen_S は ENA=ENA、STS=ACT、待ち数=0、実行数=0で、現在利用できます。",
    ),
) -> tuple[
    tuple[str, ...],
    dict[str, object],
    _CapturedLauncherProcess,
]:
    from orchestrator.campaign import queue_state, site_policy

    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []
    process = _CapturedLauncherProcess()

    def recording_popen(
        argv: tuple[str, ...], **kwargs: object
    ) -> _CapturedLauncherProcess:
        calls.append((argv, kwargs))
        return process

    if isinstance(current_site, BaseException):
        def resolve_site() -> str:
            raise current_site
    else:
        def resolve_site() -> str:
            assert isinstance(current_site, str)
            return current_site

    monkeypatch.setattr(site_policy, "current_site", resolve_site)

    def resolve_queue() -> object:
        if isinstance(queue_result, BaseException):
            raise queue_result
        return queue_result

    monkeypatch.setattr(queue_state, "dispatch_possible", resolve_queue)
    monkeypatch.setattr(DW.subprocess, "Popen", recording_popen)
    launcher_argv = ("python3", "launcher.py", "--fixed")
    session = DW._default_launch_launcher(
        launcher_argv,
        _REPO,
        _LAUNCHER_SOURCE,
    )
    session.abort()

    assert len(calls) == 1
    actual_argv, kwargs = calls[0]
    outcome_fd = int(actual_argv[-6])
    completion_fd = int(actual_argv[-4])
    assert actual_argv == (
        *launcher_argv,
        "--outcome-fd",
        str(outcome_fd),
        "--completion-fd",
        str(completion_fd),
        "--",
        "python3",
        "tools/run_tests.py",
    )
    assert process.stdin.content == _LAUNCHER_SOURCE
    assert process.stdin.closed is True
    return actual_argv, kwargs, process


def test_pegasus_login_acceptance_launcher_adds_three_shards_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from orchestrator.campaign import site_policy

    monkeypatch.delenv(DW._ACCEPTANCE_SHARDS_ENV, raising=False)
    monkeypatch.setenv("IZANAGI_EXISTING_ENV_SENTINEL", "preserved")
    parent_environment = dict(os.environ)

    _argv, kwargs, _process = _capture_default_launcher_start(
        monkeypatch,
        site_policy.PEGASUS_LOGIN,
    )

    assert kwargs["env"] == {
        **parent_environment,
        DW._ACCEPTANCE_SHARDS_ENV: "3",
    }
    assert kwargs["env"]["IZANAGI_EXISTING_ENV_SENTINEL"] == "preserved"


def test_standalone_waiter_sys_path_resolves_shard_injection(
    tmp_path: Path,
) -> None:
    probe = r'''
import importlib.util
import os
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
tool = Path(sys.argv[2]).resolve()
test_dir = Path(sys.argv[3]).resolve()
tools = root / "tools"
cwd = Path.cwd().resolve()
blocked = {root, cwd, test_dir}
clean = []
for entry in sys.path:
    if not entry:
        continue
    resolved = Path(entry).resolve()
    if resolved in blocked or resolved == tools:
        continue
    clean.append(entry)
sys.path[:] = [str(tools), *clean]
assert Path(sys.path[0]).resolve() == tools
assert all(Path(entry).resolve() not in blocked for entry in sys.path)

spec = importlib.util.spec_from_file_location("standalone_waiter_probe", tool)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

assert root in {Path(entry).resolve() for entry in sys.path}
from orchestrator.campaign import queue_state, site_policy
site_policy.current_site = lambda: site_policy.PEGASUS_LOGIN
queue_state.dispatch_possible = lambda: (
    True,
    "キュー gen_S は ENA=ENA、STS=ACT、待ち数=0、実行数=0で、現在利用できます。",
)
os.environ.pop("IZANAGI_ACCEPTANCE_SHARDS", None)
environment = module._acceptance_launcher_environment()
assert environment is not None
assert environment["IZANAGI_ACCEPTANCE_SHARDS"] == "3"
'''.strip()

    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            probe,
            str(_ROOT),
            str(_TOOL),
            str(Path(__file__).resolve().parent),
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


def test_empty_acceptance_shard_request_is_injected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from orchestrator.campaign import site_policy

    monkeypatch.setenv(DW._ACCEPTANCE_SHARDS_ENV, "")

    _argv, kwargs, _process = _capture_default_launcher_start(
        monkeypatch,
        site_policy.PEGASUS_LOGIN,
    )

    assert kwargs["env"][DW._ACCEPTANCE_SHARDS_ENV] == "3"


@pytest.mark.parametrize(
    "queue_result",
    [
        pytest.param((False, "queue unavailable"), id="unavailable"),
        pytest.param(RuntimeError("queue observation failed"), id="exception"),
        pytest.param(True, id="contract-drift"),
        pytest.param(
            (
                True,
                "キュー gen_S は ENA=不明、STS=不明、待ち数=不明、"
                "実行数=不明です（観測不能のため可用扱い）。",
            ),
            id="observation-unavailable-fail-open",
        ),
    ],
)
def test_acceptance_launcher_queue_not_confirmed_keeps_inherited_environment(
    monkeypatch: pytest.MonkeyPatch,
    queue_result: object,
) -> None:
    from orchestrator.campaign import site_policy

    monkeypatch.delenv(DW._ACCEPTANCE_SHARDS_ENV, raising=False)

    _argv, kwargs, process = _capture_default_launcher_start(
        monkeypatch,
        site_policy.PEGASUS_LOGIN,
        queue_result,
    )

    assert "env" not in kwargs
    assert process.returncode == 0


def test_non_pegasus_acceptance_launcher_does_not_inject_shards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from orchestrator.campaign import site_policy

    monkeypatch.delenv(DW._ACCEPTANCE_SHARDS_ENV, raising=False)

    _argv, kwargs, _process = _capture_default_launcher_start(
        monkeypatch,
        site_policy.OTHER,
    )

    assert "env" not in kwargs


def test_acceptance_launcher_preserves_explicit_shard_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from orchestrator.campaign import site_policy

    monkeypatch.setenv(DW._ACCEPTANCE_SHARDS_ENV, "1")

    _argv, kwargs, _process = _capture_default_launcher_start(
        monkeypatch,
        site_policy.PEGASUS_LOGIN,
    )

    assert "env" not in kwargs
    assert os.environ[DW._ACCEPTANCE_SHARDS_ENV] == "1"


def test_acceptance_launcher_site_error_keeps_inherited_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(DW._ACCEPTANCE_SHARDS_ENV, raising=False)

    _argv, kwargs, process = _capture_default_launcher_start(
        monkeypatch,
        RuntimeError("site unavailable"),
    )

    assert "env" not in kwargs
    assert process.returncode == 0


def test_acceptance_shards_are_not_injected_into_other_subprocess_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from orchestrator.campaign import site_policy

    popen_calls: list[tuple[list[str], dict[str, object]]] = []
    run_calls: list[tuple[list[str], dict[str, object]]] = []

    class Process:
        returncode = 0

        def communicate(self, timeout: object = None) -> tuple[str, str]:
            del timeout
            return "", ""

    def recording_popen(argv: list[str], **kwargs: object) -> Process:
        popen_calls.append((argv, kwargs))
        return Process()

    def recording_run(
        argv: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        run_calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.delenv(DW._ACCEPTANCE_SHARDS_ENV, raising=False)
    monkeypatch.setattr(
        site_policy,
        "current_site",
        lambda: site_policy.PEGASUS_LOGIN,
    )
    monkeypatch.setattr(DW.subprocess, "Popen", recording_popen)
    monkeypatch.setattr(DW.subprocess, "run", recording_run)

    DW._default_run(("git", "status"), _REPO, True)
    DW._default_run(_history_provenance_argv(), _REPO, True)
    DW._default_run(_helper("release"), _REPO, True)
    DW._default_run_unbounded(("plain-command",), _REPO, False)

    assert len(popen_calls) == 3
    assert len(run_calls) == 1
    for _argv, kwargs in [*popen_calls, *run_calls]:
        environment = kwargs.get("env")
        assert environment is None or DW._ACCEPTANCE_SHARDS_ENV not in environment


def test_acceptance_receipt_detail_is_printed_to_stdout_and_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    detail = (
        '{"observed":{"final_main_sha":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},'
        '"reason":"receipt-main-moved"}'
    )

    DW._print_outcome(DW._Outcome(70, "acceptance-receipt", detail=detail))

    captured = capsys.readouterr()
    assert captured.out == (
        "diagnostic: stage=acceptance-receipt rc=70 detail=" + detail + "\n"
    )
    assert captured.err == (
        "error: stage=acceptance-receipt rc=70 detail=" + detail + "\n"
    )
    assert not captured.out.startswith("error:")


def test_acceptance_receipt_temp_write_detail_omits_exception_text() -> None:
    fake = _FakeEffects()
    fake.receipt_temp_result = OSError(errno.EIO, "TEMP-SECRET-SENTINEL")

    with pytest.raises(DW._StageFailure) as failure:
        DW._prepare_acceptance_receipt(
            effects=fake.effects,
            receipt_file=_RECEIPT,
            content=b"",
        )

    expected = {
        "reason": "receipt-temp-write",
        "observed": {"exception_type": "OSError", "errno": errno.EIO},
    }
    assert failure.value.outcome == DW._Outcome(
        70,
        "acceptance-receipt",
        detail=json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert "TEMP-SECRET-SENTINEL" not in failure.value.outcome.detail


@pytest.mark.parametrize(
    ("temp_path", "observed"),
    (
        (
            Path("/other/.dev-wave-acceptance-receipt-test.tmp"),
            {"parent_matches": False, "prefix_matches": None},
        ),
        (
            Path("/receipts/wrong-prefix.tmp"),
            {"parent_matches": True, "prefix_matches": False},
        ),
    ),
    ids=("parent-mismatch", "prefix-mismatch"),
)
def test_acceptance_receipt_temp_contract_detail(
    temp_path: Path,
    observed: dict[str, object],
) -> None:
    fake = _FakeEffects()
    fake.receipt_temp_result = temp_path

    with pytest.raises(DW._StageFailure) as failure:
        DW._prepare_acceptance_receipt(
            effects=fake.effects,
            receipt_file=_RECEIPT,
            content=b"",
        )

    expected = {"reason": "receipt-temp-contract", "observed": observed}
    assert failure.value.outcome == DW._Outcome(
        70,
        "acceptance-receipt",
        detail=json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert str(temp_path) not in failure.value.outcome.detail
    assert ("unlink", temp_path) in fake.events


def test_acceptance_receipt_sigmask_detail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    lifecycle = DW._AcceptanceLifecycle(DW._LeaseOwnership.ACQUIRED)
    monkeypatch.delattr(signal, "pthread_sigmask")

    with pytest.raises(DW._StageFailure) as failure:
        DW._publish_acceptance_receipt(
            effects=fake.effects,
            lifecycle=lifecycle,
            receipt_file=_RECEIPT,
            temp_path=_RECEIPT_TEMP,
        )

    expected = {
        "reason": "receipt-sigmask",
        "observed": {"pthread_sigmask_available": False},
    }
    assert failure.value.outcome == DW._Outcome(
        70,
        "acceptance-receipt",
        detail=json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert lifecycle.ownership is DW._LeaseOwnership.ACQUIRED


@pytest.mark.parametrize(
    "injected",
    (
        OSError(errno.EBUSY, "SIGBLOCK-SECRET-SENTINEL"),
        ValueError("SIGBLOCK-SECRET-SENTINEL"),
    ),
    ids=("oserror", "valueerror"),
)
def test_acceptance_receipt_publish_sigblock_detail_restores_ownership(
    injected: BaseException,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    lifecycle = DW._AcceptanceLifecycle(DW._LeaseOwnership.ACQUIRED)
    known_mask = {signal.SIGUSR1}
    calls: list[tuple[object, object]] = []

    def fail_sigblock(how: object, mask: object) -> set[signal.Signals]:
        recorded_mask = tuple(mask) if how == signal.SIG_BLOCK else mask
        calls.append((how, recorded_mask))
        if how == signal.SIG_BLOCK and recorded_mask == ():
            return set(known_mask)
        if (
            how == signal.SIG_BLOCK
            and frozenset(mask) == frozenset(DW._HANDLED_SIGNALS)
        ):
            raise injected
        return set()

    monkeypatch.setattr(signal, "pthread_sigmask", fail_sigblock)

    with pytest.raises(DW._StageFailure) as failure:
        DW._publish_acceptance_receipt(
            effects=fake.effects,
            lifecycle=lifecycle,
            receipt_file=_RECEIPT,
            temp_path=_RECEIPT_TEMP,
        )

    expected = {
        "reason": "receipt-publish-sigblock",
        "observed": {
            "exception_type": type(injected).__name__,
            "errno": errno.EBUSY if isinstance(injected, OSError) else None,
        },
    }
    assert failure.value.outcome == DW._Outcome(
        70,
        "acceptance-receipt",
        detail=json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert "SIGBLOCK-SECRET-SENTINEL" not in failure.value.outcome.detail
    assert calls == [
        (signal.SIG_BLOCK, ()),
        (signal.SIG_BLOCK, DW._HANDLED_SIGNALS),
        (signal.SIG_SETMASK, known_mask),
    ]
    assert lifecycle.ownership is DW._LeaseOwnership.ACQUIRED
    assert lifecycle.receipt_published is False
    assert fake.receipt_published is False


def test_acceptance_receipt_publish_rename_builds_detail_after_mask_restore(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    fake.rename_result = OSError(errno.EIO, "RENAME-SECRET-SENTINEL")
    lifecycle = DW._AcceptanceLifecycle(DW._LeaseOwnership.ACQUIRED)
    mask_restored = False
    real_detail = DW._attestation_detail

    def record_mask(how: object, mask: object) -> set[signal.Signals]:
        nonlocal mask_restored
        del mask
        if how == signal.SIG_SETMASK:
            mask_restored = True
        return set()

    def detail_after_restore(reason: str, observed: object) -> str:
        if reason == "receipt-publish-rename":
            assert mask_restored is True
            assert lifecycle.ownership is DW._LeaseOwnership.ACQUIRED
        return real_detail(reason, observed)

    monkeypatch.setattr(signal, "pthread_sigmask", record_mask)
    monkeypatch.setattr(DW, "_attestation_detail", detail_after_restore)

    with pytest.raises(DW._StageFailure) as failure:
        DW._publish_acceptance_receipt(
            effects=fake.effects,
            lifecycle=lifecycle,
            receipt_file=_RECEIPT,
            temp_path=_RECEIPT_TEMP,
        )

    assert json.loads(failure.value.outcome.detail) == {
        "reason": "receipt-publish-rename",
        "observed": {"exception_type": "OSError", "errno": errno.EIO},
    }
    assert "RENAME-SECRET-SENTINEL" not in failure.value.outcome.detail


def test_acceptance_receipt_publish_rename_preserves_detail_when_mask_restore_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    fake.rename_result = OSError(errno.EIO, "RENAME-SECRET-SENTINEL")
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    _release(fake)
    publish_restore_failed = False

    def fail_mask_restore(
        how: object,
        mask: object,
    ) -> set[signal.Signals]:
        nonlocal publish_restore_failed
        del mask
        if how == signal.SIG_SETMASK and not publish_restore_failed:
            publish_restore_failed = True
            raise OSError(errno.EPERM, "MASK-RESTORE-SECRET-SENTINEL")
        return set()

    monkeypatch.setattr(signal, "pthread_sigmask", fail_mask_restore)

    outcome = _run_acceptance(fake)

    expected = {
        "reason": "receipt-publish-rename",
        "observed": {
            "exception_type": "OSError",
            "errno": errno.EIO,
            "mask_restore_failed": True,
            "mask_restore_exception_type": "PermissionError",
            "mask_restore_errno": errno.EPERM,
        },
    }
    assert outcome == DW._Outcome(
        70,
        "acceptance-receipt",
        detail=json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert json.loads(outcome.detail) == expected
    assert "RENAME-SECRET-SENTINEL" not in outcome.detail
    assert "MASK-RESTORE-SECRET-SENTINEL" not in outcome.detail
    assert fake.receipt_published is False
    assert ("unlink", _RECEIPT_TEMP) in fake.events
    assert ("run", _helper("release"), _REPO, True) in fake.events
    fake.assert_drained()


def test_acceptance_receipt_mask_restore_failure_is_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    fake.rename_result = DW._SignalReceived(signal.SIGTERM)
    lifecycle = DW._AcceptanceLifecycle(DW._LeaseOwnership.ACQUIRED)

    def fail_mask_restore(
        how: object,
        mask: object,
    ) -> set[signal.Signals]:
        del mask
        if how == signal.SIG_SETMASK:
            raise OSError(errno.EPERM, "MASK-RESTORE-SECRET-SENTINEL")
        return set()

    monkeypatch.setattr(signal, "pthread_sigmask", fail_mask_restore)

    with pytest.raises(DW._StageFailure) as failure:
        DW._publish_acceptance_receipt(
            effects=fake.effects,
            lifecycle=lifecycle,
            receipt_file=_RECEIPT,
            temp_path=_RECEIPT_TEMP,
        )

    expected = {
        "reason": "receipt-publish-mask-restore",
        "observed": {
            "exception_type": "PermissionError",
            "errno": errno.EPERM,
        },
    }
    assert failure.value.outcome == DW._Outcome(
        70,
        "acceptance-receipt",
        detail=json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert json.loads(failure.value.outcome.detail) == expected
    assert "MASK-RESTORE-SECRET-SENTINEL" not in failure.value.outcome.detail
    assert lifecycle.receipt_published is False


@pytest.mark.parametrize(
    "injected",
    (DW._SignalReceived(signal.SIGTERM), KeyboardInterrupt()),
    ids=("signal", "keyboard-interrupt"),
)
def test_acceptance_receipt_temp_writer_control_flow_passthrough(
    injected: BaseException,
) -> None:
    fake = _FakeEffects()
    fake.receipt_temp_result = injected

    with pytest.raises(type(injected)) as raised:
        DW._prepare_acceptance_receipt(
            effects=fake.effects,
            receipt_file=_RECEIPT,
            content=b"",
        )

    assert raised.value is injected


@pytest.mark.parametrize(
    "injected",
    (DW._SignalReceived(signal.SIGTERM), KeyboardInterrupt()),
    ids=("signal", "keyboard-interrupt"),
)
def test_acceptance_receipt_rename_control_flow_passthrough(
    injected: BaseException,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    fake.rename_result = injected
    lifecycle = DW._AcceptanceLifecycle(DW._LeaseOwnership.ACQUIRED)
    masks: list[tuple[object, object]] = []

    def record_mask(how: object, mask: object) -> set[signal.Signals]:
        recorded_mask = tuple(mask) if how == signal.SIG_BLOCK else mask
        masks.append((how, recorded_mask))
        return set()

    monkeypatch.setattr(signal, "pthread_sigmask", record_mask)

    with pytest.raises(type(injected)) as raised:
        DW._publish_acceptance_receipt(
            effects=fake.effects,
            lifecycle=lifecycle,
            receipt_file=_RECEIPT,
            temp_path=_RECEIPT_TEMP,
        )

    assert raised.value is injected
    assert masks == [
        (signal.SIG_BLOCK, ()),
        (signal.SIG_BLOCK, DW._HANDLED_SIGNALS),
        (signal.SIG_SETMASK, set()),
    ]
    assert lifecycle.ownership is DW._LeaseOwnership.ACQUIRED


def test_receipt_publish_failure_is_fail_closed_and_releases() -> None:
    fake = _FakeEffects()
    fake.rename_result = OSError("rename failed")
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    _release(fake)

    outcome = _run_acceptance(fake)

    expected = {
        "reason": "receipt-publish-rename",
        "observed": {"exception_type": "OSError", "errno": None},
    }
    assert outcome == DW._Outcome(
        70,
        "acceptance-receipt",
        detail=json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert json.loads(outcome.detail) == expected
    assert fake.receipt_published is False
    assert ("unlink", _RECEIPT_TEMP) in fake.events
    assert ("run", _helper("release"), _REPO, True) in fake.events
    fake.assert_drained()


def test_receipt_publishes_at_minimum_lease_ttl_boundary() -> None:
    fake = _FakeEffects()
    fake.final_claim_age_seconds = 2100
    lifecycle = DW._AcceptanceLifecycle()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    assert outcome.rc == 0
    assert lifecycle.ownership is DW._LeaseOwnership.RETAINED
    assert lifecycle.receipt_published is True
    assert fake.receipt_published is True
    assert fake.receipt_content is not None
    receipt = json.loads(fake.receipt_content)
    assert receipt["lease_holder"] == _HOLDER
    assert receipt["tested_main"] == _SHA_A
    assert receipt["tested_tip"] == _SHA_A
    assert receipt["child_rc"] == 0
    assert receipt["verdict"] == "child-green"
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


def test_receipt_requires_sufficient_lease_ttl_and_releases() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake)
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    fake.expect_run(
        _helper("claim", _SHA_A),
        DW._CommandResult(
            0,
            _held_self_payload(age_seconds=2101),
        ),
    )
    _release(fake)

    outcome = _run_acceptance(fake)

    expected = {
        "reason": "receipt-lease-check",
        "observed": {
            "state": "held-self",
            "holder_matches": True,
            "main_sha_matches": True,
            "claimed_main_sha": _SHA_A,
            "final_main_sha": _SHA_A,
            "remaining_seconds": 299,
            "required_seconds": 300,
            "ttl_sufficient": False,
        },
    }
    assert outcome == DW._Outcome(
        70,
        "acceptance-receipt",
        detail=json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert json.loads(outcome.detail) == expected
    assert fake.receipt_content is not None
    assert fake.receipt_published is False
    assert ("unlink", _RECEIPT_TEMP) in fake.events
    fake.assert_drained()


def test_receipt_reconfirms_same_lease_holder_before_publish() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake)
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    fake.expect_run(
        _helper("claim", _SHA_A),
        DW._CommandResult(0, json.dumps({"state": "held"})),
    )
    _release(fake)

    outcome = _run_acceptance(fake)

    expected = {
        "reason": "receipt-lease-check",
        "observed": {
            "state": "held",
            "holder_matches": None,
            "main_sha_matches": None,
            "claimed_main_sha": None,
            "final_main_sha": _SHA_A,
            "remaining_seconds": None,
            "required_seconds": None,
            "ttl_sufficient": None,
        },
    }
    assert outcome == DW._Outcome(
        70,
        "acceptance-receipt",
        detail=json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert json.loads(outcome.detail) == expected
    assert fake.receipt_content is not None
    assert fake.receipt_published is False
    assert ("unlink", _RECEIPT_TEMP) in fake.events
    fake.assert_drained()


def test_held_self_reacquired_before_receipt_is_released_once() -> None:
    fake = _FakeEffects()
    lifecycle = DW._AcceptanceLifecycle()
    _queue_clean_acceptance_prefix(
        fake,
        claim_payload=_held_self_payload(),
    )
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake)
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    fake.expect_run(
        _helper("claim", _SHA_A),
        DW._CommandResult(0, _acquired_payload()),
    )
    _release(fake)

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    expected = {
        "reason": "receipt-lease-check",
        "observed": {
            "state": "acquired",
            "holder_matches": None,
            "main_sha_matches": None,
            "claimed_main_sha": _SHA_A,
            "final_main_sha": _SHA_A,
            "remaining_seconds": None,
            "required_seconds": None,
            "ttl_sufficient": None,
        },
    }
    assert outcome == DW._Outcome(
        70,
        "acceptance-receipt",
        detail=json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert json.loads(outcome.detail) == expected
    assert fake.events.count(("run", _helper("release"), _REPO, True)) == 1
    assert fake.receipt_published is False
    assert ("unlink", _RECEIPT_TEMP) in fake.events
    fake.assert_drained()


@pytest.mark.parametrize(
    ("result", "observed", "source_rc"),
    (
        (
            DW._CommandResult(9),
            {
                "revision": _SHA_A,
                "path": "tools/dev_wave_wait.py",
                "failure_kind": "command",
                "source_rc": 9,
                "exception_type": None,
            },
            9,
        ),
        (
            OSError(errno.EIO, "BLOB-COMMAND-SECRET"),
            {
                "revision": _SHA_A,
                "path": "tools/dev_wave_wait.py",
                "failure_kind": "command",
                "source_rc": None,
                "exception_type": "OSError",
            },
            None,
        ),
        (
            DW._CommandResult(0, "é\n"),
            {
                "revision": _SHA_A,
                "path": "tools/dev_wave_wait.py",
                "failure_kind": "invalid-sha",
                "stdout_bytes": 2,
                "stdout_class": "non-ascii",
            },
            None,
        ),
    ),
    ids=("command-failure", "command-exception", "invalid-sha"),
)
def test_acceptance_receipt_waiter_blob_detail(
    result: object,
    observed: dict[str, object],
    source_rc: int | None,
) -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake)
    argv = ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py")
    fake.expect_run(argv, result)
    _release(fake)

    outcome = _run_acceptance(fake)

    expected = {"reason": "receipt-waiter-blob", "observed": observed}
    assert outcome == DW._Outcome(
        70,
        "acceptance-receipt",
        source_rc,
        json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert json.loads(outcome.detail) == expected
    assert "BLOB-COMMAND-SECRET" not in outcome.detail
    assert "sha256" not in observed
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    fake.assert_drained()


@pytest.mark.parametrize(
    ("result", "observed", "source_rc"),
    (
        (
            DW._CommandResult(8),
            {
                "failure_kind": "command",
                "source_rc": 8,
                "exception_type": None,
            },
            8,
        ),
        (
            OSError(errno.EACCES, "MAIN-COMMAND-SECRET"),
            {
                "failure_kind": "command",
                "source_rc": None,
                "exception_type": "PermissionError",
            },
            None,
        ),
        (
            DW._CommandResult(0, "g" * 40 + "\n"),
            {
                "failure_kind": "invalid-sha",
                "stdout_bytes": 40,
                "stdout_class": "non-hex",
            },
            None,
        ),
    ),
    ids=("command-failure", "command-exception", "invalid-sha"),
)
def test_acceptance_receipt_main_resolve_detail(
    result: object,
    observed: dict[str, object],
    source_rc: int | None,
) -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake)
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.expect_run(("git", "rev-parse", "main"), result)
    _release(fake)

    outcome = _run_acceptance(fake)

    expected = {"reason": "receipt-main-resolve", "observed": observed}
    assert outcome == DW._Outcome(
        70,
        "acceptance-receipt",
        source_rc,
        json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert json.loads(outcome.detail) == expected
    assert "MAIN-COMMAND-SECRET" not in outcome.detail
    assert "sha256" not in observed
    assert fake.receipt_content is not None
    assert fake.receipt_published is False
    assert ("unlink", _RECEIPT_TEMP) in fake.events
    fake.assert_drained()


def test_acceptance_receipt_main_moved_detail() -> None:
    fake = _FakeEffects()
    lifecycle = DW._AcceptanceLifecycle()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake)
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._CommandResult(0, _SHA_B + "\n"),
    )
    fake.expect_run(
        _helper("claim", _SHA_A),
        DW._CommandResult(0, _held_self_payload()),
    )

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    assert outcome == DW._Outcome(0)
    assert lifecycle.ownership is DW._LeaseOwnership.RETAINED
    assert lifecycle.receipt_published is True
    assert fake.receipt_published is True
    assert fake.receipt_content is not None
    receipt = json.loads(fake.receipt_content)
    assert receipt["schema_version"] == "dev-wave-acceptance-receipt/v5"
    assert receipt["tested_main"] == _SHA_A
    assert receipt["tested_tip"] == _SHA_A
    assert set(receipt) == {
        "schema_version", "authority_kind", "acceptance_wave", "lease_holder",
        "tested_main", "tested_tip", "argv", "resolved_runner_path", "child_rc",
        "pre_fingerprint", "post_fingerprint", "waiter_blob_sha",
        "env_projection", "verdict", "log_sha256", "checker_rc",
        "checker_status", "checker_blob_sha", "checker_receipt_sha256",
        "red_nodeids", "flake_nodeids", "effective_scheduler",
        "launcher_source_revision", "launcher_blob_sha",
        "launcher_executed_sha256", "waiter_executed_sha256",
        "runner_executed_sha256",
    }
    assert (
        "run", _helper("claim", _SHA_A), _REPO, True
    ) in fake.events
    assert (
        "run", _helper("claim", _SHA_B), _REPO, True
    ) not in fake.events
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


@pytest.mark.parametrize(
    ("confirmed", "expected_gate"),
    (
        pytest.param(
            DW._ClaimContext("held", _HOLDER, _SHA_A, 0),
            {
                "state": "held",
                "holder_matches": None,
                "main_sha_matches": None,
                "ttl_sufficient": None,
            },
            id="not-held-self",
        ),
        pytest.param(
            DW._ClaimContext("held-self", "f" * 12, _SHA_A, 0),
            {
                "state": "held-self",
                "holder_matches": False,
                "main_sha_matches": None,
                "ttl_sufficient": None,
            },
            id="holder-mismatch",
        ),
        pytest.param(
            DW._ClaimContext("held-self", _HOLDER, _SHA_A, 2101),
            {
                "state": "held-self",
                "holder_matches": True,
                "main_sha_matches": True,
                "remaining_seconds": 299,
                "required_seconds": 300,
                "ttl_sufficient": False,
            },
            id="insufficient-ttl",
        ),
    ),
)
def test_acceptance_main_moved_keeps_lease_publish_gates(
    confirmed: object,
    expected_gate: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    original_claim_once = DW._claim_once
    reclaimed_main_shas: list[str] = []

    def final_confirmation(
        effects: object,
        repo: Path,
        lease_dir: Path,
        wave: str,
        main_sha: str,
        lifecycle: object = None,
        *,
        diagnostic_reason: str | None = None,
    ) -> object:
        if diagnostic_reason == "receipt-reclaim":
            reclaimed_main_shas.append(main_sha)
            return confirmed
        return original_claim_once(
            effects,
            repo,
            lease_dir,
            wave,
            main_sha,
            lifecycle,
            diagnostic_reason=diagnostic_reason,
        )

    monkeypatch.setattr(DW, "_claim_once", final_confirmation)
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake)
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._CommandResult(0, _SHA_B + "\n"),
    )
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "acceptance-receipt"
    detail = json.loads(outcome.detail)
    assert detail["reason"] == "receipt-lease-check"
    for key, value in expected_gate.items():
        assert detail["observed"][key] == value
    assert fake.receipt_published is False
    assert reclaimed_main_shas == [_SHA_A]
    fake.assert_drained()


@pytest.mark.parametrize(
    (
        "claim_result",
        "failure_kind",
        "exception_type",
        "source_stage",
        "source_rc",
        "ownership",
    ),
    (
        (
            DW._CommandResult(9),
            "command",
            None,
            "claim",
            9,
            "unknown",
        ),
        (
            OSError(errno.EIO, "RECLAIM-COMMAND-SECRET"),
            "command",
            "OSError",
            "claim",
            None,
            "unknown",
        ),
        (
            DW._CommandResult(0, "not-json"),
            "claim-json",
            None,
            "claim-json",
            None,
            "unknown",
        ),
        (
            DW._CommandResult(0, json.dumps({"state": "free"})),
            "claim-state",
            None,
            "claim-state",
            None,
            "unknown",
        ),
        (
            DW._CommandResult(
                0,
                json.dumps(
                    {
                        "state": "unavailable",
                        "holder_self": True,
                        "source": {"reason": "self-renew-failed"},
                    }
                ),
            ),
            "self-renew-failed",
            None,
            "claim-self-renew-failed",
            None,
            "held-self",
        ),
        (
            DW._CommandResult(
                0,
                _held_self_payload(holder_self=False),
            ),
            "holder-self",
            None,
            "claim-self-unverified",
            None,
            "held-self",
        ),
        (
            DW._CommandResult(
                0,
                _held_self_payload(holder=7),
            ),
            "holder-type",
            None,
            "claim-self-unverified",
            None,
            "held-self",
        ),
        (
            DW._CommandResult(
                0,
                _held_self_payload(holder="not-a-holder"),
            ),
            "holder-format",
            None,
            "claim-self-unverified",
            None,
            "held-self",
        ),
        (
            DW._CommandResult(
                0,
                _held_self_payload(holder="f" * 12),
            ),
            "holder-mismatch",
            None,
            "claim-self-unverified",
            None,
            "held-self",
        ),
        (
            DW._CommandResult(
                0,
                _held_self_payload(main_sha=_SHA_B),
            ),
            "main-sha-mismatch",
            None,
            "claim-self-unverified",
            None,
            "held-self",
        ),
        (
            DW._CommandResult(
                0,
                _held_self_payload(age_seconds=True),
            ),
            "age-type",
            None,
            "claim-self-unverified",
            None,
            "held-self",
        ),
        (
            DW._CommandResult(
                0,
                _held_self_payload(age_seconds=2400),
            ),
            "age-range",
            None,
            "claim-self-unverified",
            None,
            "held-self",
        ),
        (
            DW._CommandResult(
                0,
                _held_self_payload(
                    source={"status": "error", "reason": "test"}
                ),
            ),
            "source",
            None,
            "claim-self-unverified",
            None,
            "held-self",
        ),
        (
            DW._CommandResult(
                0,
                _held_self_payload(state="held"),
            ),
            "unexpected-holder-self",
            None,
            "claim-self-unverified",
            None,
            "held-self",
        ),
    ),
    ids=(
        "claim-rc",
        "claim-exception",
        "claim-json",
        "claim-state",
        "self-renew-failed",
        "holder-self",
        "holder-type",
        "holder-format",
        "holder-mismatch",
        "main-sha-mismatch",
        "age-type",
        "age-range",
        "source",
        "unexpected-holder-self",
    ),
)
def test_acceptance_receipt_reclaim_detail(
    claim_result: object,
    failure_kind: str,
    exception_type: str | None,
    source_stage: str,
    source_rc: int | None,
    ownership: str,
) -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake)
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._CommandResult(0, _SHA_A + "\n"),
    )
    fake.expect_run(_helper("claim", _SHA_A), claim_result)
    _release(fake)

    outcome = _run_acceptance(fake)

    expected = {
        "reason": "receipt-reclaim",
        "observed": {
            "failure_kind": failure_kind,
            "exception_type": exception_type,
            "source_stage": source_stage,
            "source_rc": source_rc,
            "confirmation_ownership": ownership,
        },
    }
    assert outcome == DW._Outcome(
        70,
        "acceptance-receipt",
        source_rc,
        json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert json.loads(outcome.detail) == expected
    assert "RECLAIM-COMMAND-SECRET" not in outcome.detail
    assert fake.receipt_published is False
    assert ("unlink", _RECEIPT_TEMP) in fake.events
    fake.assert_drained()


def test_acceptance_receipt_reclaim_holder_hash_detail() -> None:
    wave = "wave-\udc80"
    fake = _FakeEffects()
    fake.expect_run(
        DW._lease_command(_REPO, "claim", _LEASE, wave, _SHA_A),
        DW._CommandResult(0, _held_self_payload()),
    )
    lifecycle = DW._AcceptanceLifecycle()

    with pytest.raises(DW._StageFailure) as failure:
        DW._claim_once(
            fake.effects,
            _REPO,
            _LEASE,
            wave,
            _SHA_A,
            lifecycle,
            diagnostic_reason="receipt-reclaim",
        )

    expected = {
        "reason": "receipt-reclaim",
        "observed": {"failure_kind": "holder-hash"},
    }
    assert failure.value.outcome == DW._Outcome(
        70,
        "claim-self-unverified",
        detail=json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert json.loads(failure.value.outcome.detail) == expected
    assert lifecycle.ownership is DW._LeaseOwnership.HELD_SELF
    fake.assert_drained()


def test_signal_before_receipt_publish_leaves_no_final_and_releases() -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake)
    fake.expect_run(
        ("git", "rev-parse", f"{_SHA_A}:tools/dev_wave_wait.py"),
        DW._CommandResult(0, _WAITER_BLOB + "\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "main"),
        DW._SignalReceived(signal.SIGTERM),
    )
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(143, "signal-15")
    assert fake.receipt_published is False
    assert _RECEIPT not in fake.existing_paths
    assert fake.events.index(("write_receipt_temp", _RECEIPT)) < max(
        index
        for index, event in enumerate(fake.events)
        if event == ("run", ("git", "rev-parse", "main"), _REPO, True)
    )
    assert ("unlink", _RECEIPT_TEMP) in fake.events
    fake.assert_drained()


def test_signal_after_receipt_publish_does_not_reverse_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    lifecycle = DW._AcceptanceLifecycle()
    entry_mask = set(_REAL_PTHREAD_SIGMASK(signal.SIG_BLOCK, ()))
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    real_sigmask = DW.signal.pthread_sigmask

    def delayed_signal(how: int, signals: object):
        previous_mask = real_sigmask(how, signals)
        if how == signal.SIG_SETMASK:
            raise DW._SignalReceived(signal.SIGTERM)
        return previous_mask

    monkeypatch.setattr(DW.signal, "pthread_sigmask", delayed_signal)

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    assert outcome.rc == 0
    assert lifecycle.receipt_published is True
    assert fake.receipt_published is True
    assert lifecycle.ownership is DW._LeaseOwnership.RETAINED
    fake.assert_drained()
    assert set(_REAL_PTHREAD_SIGMASK(signal.SIG_BLOCK, ())) == entry_mask


@pytest.mark.parametrize(
    "case",
    [
        "inside-repo",
        "existing",
        "dangling-symlink",
        "missing-parent",
        "reserved-temp-name",
    ],
)
def test_receipt_path_rejected_before_claim(case: str) -> None:
    fake = _FakeEffects()
    _preflight(fake, claim_guards=False)
    if case == "inside-repo":
        receipt = _REPO / "receipt.json"
    elif case == "reserved-temp-name":
        receipt = _RECEIPT.parent / ".dev-wave-acceptance-receipt-final.json"
    else:
        receipt = _RECEIPT
    if case == "existing":
        fake.existing_paths.add(receipt)
    if case == "dangling-symlink":
        fake.symlinks.add(receipt)
    if case == "missing-parent":
        fake.directories.clear()

    outcome = _run_acceptance(fake, receipt_file=receipt)

    assert outcome == DW._Outcome(2, "acceptance-receipt-preflight")
    assert not any(
        event[0] == "run" and event[1] == _helper("claim", _SHA_A)
        for event in fake.events
    )
    fake.assert_drained()


def test_existing_log_path_is_rejected_before_claim() -> None:
    fake = _FakeEffects()
    fake.existing_paths.add(_LOG)
    _preflight(fake, claim_guards=False)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(2, "acceptance-log-preflight")
    assert not any(
        event[0] == "run" and event[1] == _helper("claim", _SHA_A)
        for event in fake.events
    )
    fake.assert_drained()


def test_dangling_log_path_is_rejected_before_claim() -> None:
    fake = _FakeEffects()
    fake.symlinks.add(_LOG)
    _preflight(fake, claim_guards=False)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(2, "acceptance-log-preflight")
    assert not any(
        event[0] == "run" and event[1] == _helper("claim", _SHA_A)
        for event in fake.events
    )
    fake.assert_drained()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("PYTEST_ADDOPTS", "-k nothing"),
        ("PYTEST_PLUGINS", "foreign_plugin"),
        ("IZANAGI_TASK_RUN_ID", "run-inside-repo"),
    ],
)
def test_acceptance_environment_rejected_before_claim(key: str, value: str) -> None:
    fake = _FakeEffects()
    fake.env[key] = value
    _preflight(fake, claim_guards=False)

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(2, "acceptance-env-preflight")
    assert not any(
        event[0] == "run" and event[1] == _helper("claim", _SHA_A)
        for event in fake.events
    )
    fake.assert_drained()


def test_real_pytest_addopts_is_rejected_before_claim(tmp_path: Path) -> None:
    wave = "real-env-closed"
    repo, lease, env = _real_waiter_repo(tmp_path, wave=wave)
    env["PYTEST_ADDOPTS"] = "-k nothing"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    receipt = tmp_path / "env-receipt.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "dev_wave_wait.py"),
            "acceptance",
            "--wave",
            wave,
            "--lease-dir",
            str(lease),
            "--receipt-file",
            str(receipt),
            "--log-file",
            str(tmp_path / "env.log"),
            "--",
            "python3",
            "tools/run_tests.py",
        ],
        cwd=repo,
        env=env,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 2
    assert "stage=acceptance-env-preflight rc=2" in completed.stderr
    assert not (lease / "acceptance.lease").exists()
    assert not receipt.exists()


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
        "--check-only",
        "--receipt-file",
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


def test_producer_check_only_requires_receipt_file() -> None:
    parser = DW._producer_parser()
    with pytest.raises(DW._StageFailure) as raised:
        parser.parse_args(
            [
                "--done-file",
                "done",
                "--artifact-file",
                "artifact",
                "--pid",
                "1",
                "--check-only",
            ]
        )
    assert raised.value.outcome == DW._Outcome(2, "cli-usage")


def test_atomic_publish_json_moves_fsynced_temp_to_final_path() -> None:
    fake = _FakeEffects()
    payload = {
        "schema_version": "dev-wave-producer-receipt/v1",
        "status": "success",
    }

    DW._atomic_publish_json(_RECEIPT, payload, fake.effects)

    assert fake.events == [
        ("write_receipt_temp", _RECEIPT),
        ("rename", _RECEIPT_TEMP, _RECEIPT),
    ]
    assert fake.receipt_temp_payload == DW._canonical_json_line(payload)
    assert _RECEIPT in fake.existing_paths
    fake.assert_drained()


def test_producer_check_only_success_is_single_pass_and_publishes_receipt() -> None:
    fake = _FakeEffects()
    pid = 123
    stat_path = Path(f"/proc/{pid}/stat")
    fake.read_text_queue.append((stat_path, _stat_text(pid, 17)))
    fake.kill_queue.append(ProcessLookupError(errno.ESRCH, "gone"))
    fake.is_file_queue.extend(
        [(Path("done"), True), (Path("artifact"), True)]
    )
    fake.stat_mtime_queue.extend(
        [(Path("done"), 101), (Path("artifact"), 202)]
    )

    outcome = DW.main(
        [
            "producer",
            "--done-file",
            "done",
            "--artifact-file",
            "artifact",
            "--pid",
            str(pid),
            "--check-only",
            "--receipt-file",
            str(_RECEIPT),
        ],
        effects=fake.effects,
    )

    assert outcome == DW.RC_OK
    assert not any(event[0] == "sleep" for event in fake.events)
    assert json.loads(fake.receipt_temp_payload) == {
        "artifact_file": str(DW._absolute_path(Path("artifact"))),
        "artifact_mtime_ns": 202,
        "done_file": str(DW._absolute_path(Path("done"))),
        "done_mtime_ns": 101,
        "pid_source": str(DW._absolute_path(Path(f"/proc/{pid}/stat"))),
        "schema_version": "dev-wave-producer-receipt/v1",
        "status": "success",
    }
    assert _RECEIPT in fake.existing_paths
    fake.assert_drained()


@pytest.mark.parametrize(
    "missing",
    ["producer", "done", "artifact"],
    ids=["producer-alive", "done-missing", "artifact-missing"],
)
def test_producer_check_only_missing_condition_is_fail_closed(
    missing: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = _FakeEffects()
    pid = 124
    stat_path = Path(f"/proc/{pid}/stat")
    if missing == "producer":
        fake.read_text_queue.extend(
            [(stat_path, _stat_text(pid, 18)), (stat_path, _stat_text(pid, 18))]
        )
        fake.kill_queue.append(None)
    else:
        fake.read_text_queue.append((stat_path, _stat_text(pid, 18)))
        fake.kill_queue.append(ProcessLookupError(errno.ESRCH, "gone"))
    fake.is_file_queue.extend(
        [
            (Path("done"), missing != "done"),
            (Path("artifact"), missing != "artifact"),
        ]
    )

    outcome = DW.main(
        [
            "producer",
            "--done-file",
            "done",
            "--artifact-file",
            "artifact",
            "--pid",
            str(pid),
            "--check-only",
            "--receipt-file",
            str(_RECEIPT),
        ],
        effects=fake.effects,
    )

    assert outcome == DW.RC_FAIL_CLOSED
    assert fake.receipt_temp_payload is None
    assert _RECEIPT not in fake.existing_paths
    assert not any(event[0] == "sleep" for event in fake.events)
    diagnostic = capsys.readouterr()
    expected_missing = {
        "producer": "producer-dead",
        "done": "done-file",
        "artifact": "artifact-file",
    }[missing]
    assert expected_missing in diagnostic.err
    fake.assert_drained()


@pytest.mark.parametrize(
    "state",
    [
        pytest.param(
            DW._ProducerState(DW._PidState.ALIVE, True, True),
            id="producer-alive",
        ),
        pytest.param(
            DW._ProducerState(DW._PidState.DEAD, False, True),
            id="done-missing",
        ),
        pytest.param(
            DW._ProducerState(DW._PidState.DEAD, True, False),
            id="artifact-missing",
        ),
    ],
)
def test_producer_receipt_gate_rejects_incomplete_state_with_real_files(
    tmp_path: Path,
    state: DW._ProducerState,
) -> None:
    done_file = tmp_path / "producer.done"
    artifact_file = tmp_path / "artifact.json"
    receipt_file = tmp_path / "producer-receipt.json"
    done_file.write_text("0\n", encoding="utf-8")
    artifact_file.write_text("{}\n", encoding="utf-8")

    # Keep both files real so a gate-bypassing mutation reaches real stat()
    # calls instead of being masked by an injected mtime failure.
    outcome = DW._publish_producer_receipt(
        receipt_file=receipt_file,
        pid_source=tmp_path / "pid-source",
        done_file=done_file,
        artifact_file=artifact_file,
        state=state,
        effects=DW._default_effects(),
    )

    assert outcome.rc == DW.RC_FAIL_CLOSED
    assert not receipt_file.exists()


@pytest.mark.parametrize(
    "signal_to_send",
    [signal.SIGKILL, signal.SIGTERM],
    ids=["sigkill", "sigterm"],
)
def test_producer_waiter_kill_requires_later_check_only_receipt(
    tmp_path: Path,
    signal_to_send: signal.Signals,
) -> None:
    done_file = tmp_path / "producer.done"
    artifact_file = tmp_path / "artifact.json"
    receipt_file = tmp_path / "producer-receipt.json"
    producer = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        cwd=_ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    waiter: subprocess.Popen[str] | None = None
    try:
        waiter = subprocess.Popen(
            [
                sys.executable,
                str(_TOOL),
                "producer",
                "--done-file",
                str(done_file),
                "--artifact-file",
                str(artifact_file),
                "--pid",
                str(producer.pid),
                "--max-wait-seconds",
                "60",
                "--receipt-file",
                str(receipt_file),
            ],
            cwd=_ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 30
        while waiter.poll() is None and time.monotonic() < deadline:
            if receipt_file.exists():
                break
            time.sleep(0.02)
        assert waiter.poll() is None
        assert not receipt_file.exists()

        waiter.send_signal(signal_to_send)
        waiter.wait(timeout=120)
        assert not receipt_file.exists()

        done_file.write_text("0\n", encoding="utf-8")
        artifact_file.write_text("{}\n", encoding="utf-8")
        producer.terminate()
        producer.wait(timeout=120)

        checked = subprocess.run(
            [
                sys.executable,
                str(_TOOL),
                "producer",
                "--done-file",
                str(done_file),
                "--artifact-file",
                str(artifact_file),
                "--pid",
                str(producer.pid),
                "--check-only",
                "--receipt-file",
                str(receipt_file),
            ],
            cwd=_ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=120,
        )
        assert checked.returncode == DW.RC_OK, checked.stderr
        assert receipt_file.exists()
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        assert receipt["schema_version"] == "dev-wave-producer-receipt/v1"
        assert receipt["status"] == "success"
        assert receipt["done_file"] == str(done_file)
        assert receipt["artifact_file"] == str(artifact_file)
    finally:
        if waiter is not None and waiter.poll() is None:
            waiter.kill()
            waiter.wait(timeout=120)
        if producer.poll() is None:
            producer.kill()
            producer.wait(timeout=120)


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
    ("state", "lease_optional"),
    [
        pytest.param("held", False, id="held-default"),
        pytest.param("held", True, id="held-legacy-flag"),
        pytest.param("queued", False, id="queued-default"),
        pytest.param("queued", True, id="queued-legacy-flag"),
    ],
)
def test_acceptance_claim_is_single_nonblocking(
    state: str,
    lease_optional: bool,
) -> None:
    """Pin A: 未取得経路では、投入前の claim を一度だけ試みる。"""

    def run_once(flag: bool) -> tuple[object, ...]:
        fake = _RoutingAcceptanceEffects(
            behind=[0, 0],
            claim_payload=json.dumps({"state": state}),
        )
        outcome = _run_acceptance(fake, lease_optional=flag)

        assert outcome.rc == 0
        assert (fake.claims, fake.submissions, fake.releases) == (1, 1, 0)
        assert not any(event[0] == "sleep" for event in fake.events)
        assert fake.receipt_published is True
        assert fake.receipt_content is not None
        receipt = json.loads(fake.receipt_content)
        assert receipt["lease_holder"] == _HOLDER
        assert not any(
            event[0] == "run" and event[1] == _helper("release")
            for event in fake.events
        )
        fake.assert_drained()
        return (
            outcome.rc,
            fake.claims,
            fake.submissions,
            fake.releases,
            receipt["lease_holder"],
        )

    observed = run_once(lease_optional)
    other_flag = run_once(not lease_optional)
    assert observed == other_flag == (0, 1, 1, 0, _HOLDER)


@pytest.mark.parametrize(
    "state", ["stale-held", "unavailable"],
    ids=("stale-held", "unavailable"),
)
def test_acceptance_rejects_non_nonblocking_claim_state(state: str) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _claim(fake, _SHA_A, json.dumps({"state": state}))
    outcome = _run_acceptance(fake, max_wait=1)

    assert outcome.rc == 70
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
    ]
    fake.assert_drained()


@pytest.mark.parametrize("age_seconds", [0, 7], ids=("zero-age", "observed-age"))
def test_acceptance_held_self_runs_command_without_polling(age_seconds: int) -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[0, 0],
        claim_payload=_held_self_payload(age_seconds=age_seconds),
    )

    outcome = _run_acceptance(fake)

    assert outcome.rc == 0
    assert (fake.claims, fake.submissions, fake.releases) == (2, 1, 0)
    assert fake.events.count(("sleep", 30)) == 0
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )


def test_acceptance_held_self_waiter_bytes_mismatch_blocks_without_release(
) -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[0, 0],
        claim_payload=_held_self_payload(),
    )
    fake.running_waiter_bytes_result = hashlib.sha256(b"version A").hexdigest()
    fake.tip_waiter_bytes_result = hashlib.sha256(b"version B").hexdigest()

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "restart-required"
    detail = json.loads(outcome.detail)
    assert detail == {
        "reason": "receipt-waiter-sha256-mismatch",
        "observed": {
            "actual_sha256": fake.running_waiter_bytes_result,
            "expected_sha256": fake.tip_waiter_bytes_result,
            "tested_tip": _SHA_A,
        },
    }
    assert (fake.claims, fake.submissions, fake.releases) == (1, 0, 0)
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )


def test_acceptance_real_acquired_payload_runs_command_and_releases_on_failure(
) -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[0, 0],
        claim_payload=_acquired_payload(),
        command_result=DW._CommandResult(23),
    )

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "acceptance-command"
    assert outcome.source_rc == 23
    assert (fake.claims, fake.submissions, fake.releases) == (1, 1, 1)
    assert fake.events.count(("sleep", 30)) == 0


def test_claim_once_real_acquired_payload_grants_acquired_ownership() -> None:
    fake = _FakeEffects()
    fake.expect_run(
        _helper("claim", _SHA_A),
        DW._CommandResult(0, _acquired_payload()),
    )
    lifecycle = DW._AcceptanceLifecycle()

    claim = DW._claim_once(
        fake.effects,
        _REPO,
        _LEASE,
        _WAVE,
        _SHA_A,
        lifecycle,
    )

    assert claim == DW._ClaimContext("acquired", _HOLDER, _SHA_A, 0)
    assert lifecycle.ownership is DW._LeaseOwnership.ACQUIRED
    fake.assert_drained()


@pytest.mark.parametrize("state", ["held", "queued"])
def test_try_claim_once_without_wait_builds_unclaimed_context(
    state: str,
) -> None:
    fake = _FakeEffects()
    _claim(fake, _SHA_A, json.dumps({"state": state}))
    lifecycle = DW._AcceptanceLifecycle()

    started_at, claim = DW._try_claim_once_without_wait(
        fake.effects,
        _REPO,
        _LEASE,
        _WAVE,
        7200.0,
        lifecycle,
    )

    assert started_at == 0.0
    assert claim == DW._ClaimContext(
        state,
        _HOLDER,
        _SHA_A,
        None,
        True,
    )
    assert lifecycle.ownership is DW._LeaseOwnership.NONE
    assert not any(event[0] == "sleep" for event in fake.events)
    fake.assert_drained()


def test_acceptance_lease_optional_is_noop_for_acquired_path() -> None:
    def run_once(flag: bool) -> tuple[object, ...]:
        fake = _RoutingAcceptanceEffects(
            behind=[0, 0],
            claim_payload=_acquired_payload(),
        )
        lifecycle = DW._AcceptanceLifecycle()
        outcome = _run_acceptance(
            fake,
            lifecycle=lifecycle,
            lease_optional=flag,
        )

        assert outcome.rc == 0
        assert lifecycle.ownership is DW._LeaseOwnership.RETAINED
        assert (fake.claims, fake.submissions, fake.releases) == (2, 1, 0)
        assert fake.receipt_published is True
        assert json.loads(fake.receipt_content)["lease_holder"] == _HOLDER
        assert not any(event[0] == "sleep" for event in fake.events)
        fake.assert_drained()
        return (
            outcome.rc,
            lifecycle.ownership,
            fake.claims,
            fake.submissions,
            fake.releases,
            json.loads(fake.receipt_content)["lease_holder"],
        )

    assert run_once(False) == run_once(True)


@pytest.mark.parametrize(
    ("state", "lease_optional"),
    [
        pytest.param("held", False, id="held-default"),
        pytest.param("held", True, id="held-legacy-flag"),
        pytest.param("queued", False, id="queued-default"),
        pytest.param("queued", True, id="queued-legacy-flag"),
    ],
)
def test_acceptance_unclaimed_path_skips_wait_reclaim_and_release(
    state: str, lease_optional: bool, tmp_path: Path,
) -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[0, 0],
        claim_payload=json.dumps({"state": state}),
    )
    lifecycle = DW._AcceptanceLifecycle()

    outcome = _run_acceptance(
        fake,
        lifecycle=lifecycle,
        lease_optional=lease_optional,
    )

    assert outcome.rc == 0
    assert lifecycle.ownership is DW._LeaseOwnership.NONE
    assert (fake.claims, fake.submissions, fake.releases) == (1, 1, 0)
    assert fake.receipt_published is True
    receipt = json.loads(fake.receipt_content)
    assert receipt["lease_holder"] == hashlib.sha256(
        _WAVE.encode("utf-8")
    ).hexdigest()[:12]
    receipt_path = tmp_path / "acceptance.json"
    receipt_path.write_bytes(fake.receipt_content)
    raw_receipt = receipt_path.read_bytes()
    assert LAND._release_authority_digest(
        receipt_path,
        _WAVE,
    ) == hashlib.sha256(raw_receipt).hexdigest()
    assert fake.events.count(("sleep", 30)) == 0
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


@pytest.mark.parametrize(
    ("state", "lease_optional"),
    [
        pytest.param("held", False, id="held-default"),
        pytest.param("held", True, id="held-legacy-flag"),
        pytest.param("queued", False, id="queued-default"),
        pytest.param("queued", True, id="queued-legacy-flag"),
    ],
)
def test_pin_c_unclaimed_keeps_main_drift_check(
    state: str, lease_optional: bool
) -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[0, 0],
        claim_payload=json.dumps({"state": state}),
        final_main_sha=_SHA_B,
    )
    lifecycle = DW._AcceptanceLifecycle()

    outcome = _run_acceptance(
        fake,
        lifecycle=lifecycle,
        lease_optional=lease_optional,
    )

    assert outcome == DW._Outcome(0)
    assert lifecycle.ownership is DW._LeaseOwnership.NONE
    assert (fake.claims, fake.submissions, fake.releases) == (1, 1, 0)
    assert fake.receipt_published is True
    assert fake.receipt_content is not None
    receipt = json.loads(fake.receipt_content)
    assert receipt["schema_version"] == "dev-wave-acceptance-receipt/v5"
    assert receipt["tested_main"] == _SHA_A
    assert receipt["tested_tip"] == _SHA_A
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


@pytest.mark.parametrize(
    ("state", "lease_optional"),
    [
        pytest.param("held", False, id="held-default"),
        pytest.param("held", True, id="held-legacy-flag"),
        pytest.param("queued", False, id="queued-default"),
        pytest.param("queued", True, id="queued-legacy-flag"),
    ],
)
def test_pin_c_unclaimed_postrun_dirty_blocks_without_receipt(
    state: str, lease_optional: bool
) -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(
        fake,
        claim_payload=json.dumps({"state": state}),
    )
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, " M changed.py\n"))

    outcome = _run_acceptance(fake, lease_optional=lease_optional)

    assert outcome == DW._Outcome(70, "postrun-clean")
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


@pytest.mark.parametrize(
    ("state", "lease_optional"),
    [
        pytest.param("held", False, id="held-default"),
        pytest.param("held", True, id="held-legacy-flag"),
        pytest.param("queued", False, id="queued-default"),
        pytest.param("queued", True, id="queued-legacy-flag"),
    ],
)
def test_pin_c_unclaimed_postrun_index_flags_block_without_receipt(
    state: str, lease_optional: bool
) -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(
        fake,
        claim_payload=json.dumps({"state": state}),
    )
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, ""))
    fake.expect_run(_INDEX_FLAGS_ARGV, DW._CommandResult(0, "S hidden.py\0"))

    outcome = _run_acceptance(fake, lease_optional=lease_optional)

    assert outcome == DW._Outcome(70, "postrun-index-flags")
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


@pytest.mark.parametrize(
    ("state", "lease_optional"),
    [
        pytest.param("held", False, id="held-default"),
        pytest.param("held", True, id="held-legacy-flag"),
        pytest.param("queued", False, id="queued-default"),
        pytest.param("queued", True, id="queued-legacy-flag"),
    ],
)
def test_pin_c_unclaimed_postrun_fingerprint_blocks_without_receipt(
    state: str, lease_optional: bool
) -> None:
    fake = _FakeEffects()
    _queue_clean_acceptance_prefix(
        fake,
        claim_payload=json.dumps({"state": state}),
    )
    fake.expect_run(
        _COMMAND,
        DW._CommandResult(0),
        capture=False,
        unchanged_postrun=False,
    )
    _postrun_integrity(fake, head=_SHA_B)

    outcome = _run_acceptance(fake, lease_optional=lease_optional)

    assert outcome == DW._Outcome(70, "postrun-fingerprint")
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


def test_pin_d_unclaimed_failure_does_not_release_foreign_lease() -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[0, 0],
        claim_payload=json.dumps({"state": "held"}),
        command_result=DW._CommandResult(23),
    )

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "acceptance-command"
    assert outcome.source_rc == 23
    assert fake.receipt_content is None
    assert fake.receipt_published is False
    assert fake.releases == 0
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


def test_acceptance_legacy_self_held_fails_closed_without_polling() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _claim(
        fake,
        _SHA_A,
        json.dumps(
            {
                "state": "held",
                "holder": _HOLDER,
                "holder_self": True,
                "age_seconds": 1,
                "source": {"status": "ok", "reason": None},
            }
        ),
    )

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "claim-self-unverified"
    assert fake.events.count(("sleep", 30)) == 0
    assert not any(event[0] == "run" and event[1] == _COMMAND for event in fake.events)
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


@pytest.mark.parametrize(
    "overrides",
    [
        {"holder_self": False},
        {"age_seconds": "0"},
        {"source": {"status": "unavailable", "reason": "lease-unavailable"}},
        {"holder": "not-a-holder"},
        {"source": {"status": "ok", "reason": None, "extra": "rejected"}},
        {"source": {"status": "ok"}},
        {"age_seconds": True},
        {"holder": "ABCDEF012345"},
    ],
    ids=(
        "holder-false",
        "age-non-int",
        "source-unavailable",
        "holder-non-hex",
        "source-extra-key",
        "source-missing-key",
        "age-bool",
        "holder-uppercase-hex",
    ),
)
def test_acceptance_invalid_held_self_fails_closed(
    overrides: dict[str, object],
) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _claim(fake, _SHA_A, _held_self_payload(**overrides))

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "claim-self-unverified"
    assert fake.events.count(("sleep", 30)) == 0
    assert not any(event[0] == "run" and event[1] == _COMMAND for event in fake.events)
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
    fake.assert_drained()


def test_public_main_self_renew_failure_reports_reason_without_poll_or_release(
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _claim(
        fake,
        _SHA_A,
        json.dumps(
            {
                "state": "unavailable",
                "holder": _HOLDER,
                "holder_self": True,
                "main_sha": _SHA_A,
                "age_seconds": 17,
                "source": {
                    "status": "unavailable",
                    "reason": "self-renew-failed",
                },
            }
        ),
    )

    rc = DW.main(
        [
            "acceptance",
            "--wave",
            _WAVE,
            "--lease-dir",
            str(_LEASE),
            "--receipt-file",
            str(_RECEIPT),
            "--log-file",
            str(_LOG),
            "--",
            *_COMMAND,
        ],
        effects=fake.effects,
        repo=_REPO,
    )
    captured = capsys.readouterr()

    assert rc == 70
    assert captured.out == ""
    assert captured.err.splitlines().count(
        "acceptance: held-self lease retained; "
        "this invocation has no release authority"
    ) == 1
    assert captured.err.splitlines().count(
        "error: stage=claim-self-renew-failed rc=70"
    ) == 1
    assert fake.events.count(("sleep", 30)) == 0
    assert not any(event[0] == "run" and event[1] == _COMMAND for event in fake.events)
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )
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
            if actual == _STATUS_ARGV:
                return DW._CommandResult(0, "")
            if actual in {_INDEX_FLAGS_ARGV, _SUBMODULE_INDEX_FLAGS_ARGV}:
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

    claim = DW._claim_once(fake.effects, _REPO, _LEASE, _WAVE, _SHA_A)

    assert claim.state == "held"
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


@pytest.mark.parametrize("state", ["held", "queued"])
def test_unclaimed_acceptance_claim_does_not_refresh_or_retry(state: str) -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[0, 0],
        claim_payload=json.dumps({"state": state}),
    )

    outcome = _run_acceptance(fake)

    assert outcome.rc == 0
    assert fake.claims == 1
    assert fake.events.count(("sleep", 30)) == 0
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )


def test_acquired_reloads_main_before_behind_check() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake, _SHA_A)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    _prerun_status(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    outcome = _run_acceptance(fake)
    assert outcome.rc == 0
    rev_parse_outputs = [
        event for event in fake.events
        if event[0] == "run" and event[1] == ("git", "rev-parse", "main")
    ]
    # postclaim、behind 検査、rename 直前の再確認で main を計 3 回読む。
    assert len(rev_parse_outputs) == 3
    fake.assert_drained()


def test_self_reported_merge_message_has_exact_trailer() -> None:
    fake = _FakeEffects()

    result = DW._self_reported_merge_message_copy(fake.effects)

    assert result == _VALIDATED_MESSAGE
    assert fake.events == [("write_temp", _SELF_REPORTED_MERGE_MESSAGE)]


def test_preclaim_behind_without_message_claims_and_submits_without_release() -> None:
    fake = _RoutingAcceptanceEffects(
        preclaim_behind=13,
        behind=[0, 0],
    )

    outcome = _run_acceptance(fake)

    assert outcome.rc == 0
    assert (fake.claims, fake.submissions, fake.releases) == (2, 1, 0)
    preclaim_behind = fake.events.index(
        (
            "run",
            ("git", "rev-list", "--count", "HEAD..main"),
            _REPO,
            True,
        )
    )
    preclaim_provenance = fake.events.index(
        ("run", _history_provenance_argv(), _REPO, True)
    )
    first_claim = next(
        index
        for index, event in enumerate(fake.events)
        if event[0] == "run"
        and len(event[1]) > 2
        and event[1][2] == "claim"
    )
    assert preclaim_behind < preclaim_provenance < first_claim
    assert not any(
        event[0] == "run"
        and event[1] == _helper("release")
        for event in fake.events
    )


def test_preclaim_behind_without_message_reaches_claim() -> None:
    fake = _RoutingAcceptanceEffects(
        preclaim_behind=1,
        behind=[0, 0],
    )

    outcome = _run_acceptance(fake)

    assert outcome.rc == 0
    assert fake.claims == 2
    preclaim_provenance = fake.events.index(
        ("run", _history_provenance_argv(), _REPO, True)
    )
    first_claim = next(
        index
        for index, event in enumerate(fake.events)
        if event[0] == "run"
        and len(event[1]) > 2
        and event[1][2] == "claim"
    )
    assert preclaim_provenance < first_claim


def test_preclaim_behind_with_merge_message_reaches_claim() -> None:
    fake = _RoutingAcceptanceEffects(
        preclaim_behind=1,
        behind=[1, 0],
        head_shas=[_SHA_C, _SHA_C],
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 0
    assert fake.claims == 2
    first_claim = next(
        index
        for index, event in enumerate(fake.events)
        if event[0] == "run" and "claim" in event[1]
    )
    preclaim_behind = fake.events.index(
        (
            "run",
            ("git", "rev-list", "--count", "HEAD..main"),
            _REPO,
            True,
        )
    )
    preclaim_provenance = fake.events.index(
        ("run", _history_provenance_argv(), _REPO, True)
    )
    assert preclaim_behind < preclaim_provenance < first_claim


def test_preclaim_not_behind_reaches_claim() -> None:
    fake = _RoutingAcceptanceEffects(behind=[0, 0])

    outcome = _run_acceptance(fake)

    assert outcome.rc == 0
    assert fake.claims == 2


def test_postclaim_main_race_self_report_reaches_submission_without_release() -> None:
    fake = _RoutingAcceptanceEffects(
        preclaim_behind=0,
        behind=[1, 0],
        head_shas=[_SHA_C, _SHA_C],
    )

    outcome = _run_acceptance(fake)

    assert outcome.rc == 0
    assert (fake.claims, fake.submissions, fake.releases) == (2, 1, 0)
    assert ("write_temp", _SELF_REPORTED_MERGE_MESSAGE) in fake.events
    assert any(
        event[0] == "run" and event[1] == _provenance_argv()
        for event in fake.events
    )


def test_postclaim_merge_without_implementation_conflict_accepts_self_report() -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1, 0],
        head_shas=[_SHA_C, _SHA_C],
        provenance_result=DW._CommandResult(0),
    )

    outcome = _run_acceptance(fake)

    assert outcome.rc == 0
    message_index = next(
        index
        for index, event in enumerate(fake.events)
        if event == ("write_temp", _SELF_REPORTED_MERGE_MESSAGE)
    )
    selected = [
        event
        for event in fake.events[message_index:]
        if event[0] == "write_temp"
        or (
            len(event) > 1
            and event[1]
            in {
                ("git", "merge", "--no-ff", "--no-commit", "main"),
                _provenance_argv(),
                ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
                ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
                _history_provenance_argv(),
                _COMMAND,
            }
        )
    ]
    assert [
        (event[0], event[1]) if event[0] == "run" else event
        for event in selected
    ] == [
        ("write_temp", _SELF_REPORTED_MERGE_MESSAGE),
        ("run", ("git", "merge", "--no-ff", "--no-commit", "main")),
        ("run", _provenance_argv()),
        ("run", ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE))),
        ("run", ("git", "commit", "-F", str(_VALIDATED_MESSAGE))),
        ("run", _history_provenance_argv()),
        ("run", _COMMAND),
    ]


def test_postclaim_merge_provenance_failure_rejects_self_report() -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1],
        provenance_result=DW._CommandResult(1),
    )

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(
        70,
        "merge-message-provenance",
        source_rc=1,
    )
    assert ("write_temp", _SELF_REPORTED_MERGE_MESSAGE) in fake.events
    assert fake.submissions == 0
    assert fake.releases == 1
    assert any(
        event[0] == "run"
        and event[1] == ("git", "merge", "--abort")
        for event in fake.events
    )
    assert not any(
        event[0] == "run"
        and event[1]
        in {
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
            _COMMAND,
        }
        for event in fake.events
    )


def test_preclaim_history_provenance_failure_never_claims_and_returns_reason(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    lease_dir = tmp_path / "lease"
    lease_dir.mkdir()
    violation = (
        "21582897ece7: 実装面に Codex role=author がない — "
        "paths=tools/example.py"
    )
    fake = _RoutingAcceptanceEffects(
        preclaim_history_provenance_result=DW._CommandResult(
            1,
            stderr=violation + "\n",
        ),
        lease_dir=lease_dir,
    )

    outcome = _run_acceptance(fake, lease_dir=lease_dir)

    assert outcome == DW._Outcome(
        70,
        "preclaim-history-provenance",
        source_rc=1,
        detail=violation,
    )
    assert (fake.claims, fake.submissions, fake.releases) == (0, 0, 0)
    assert list(lease_dir.iterdir()) == []
    DW._print_outcome(outcome)
    assert violation in capsys.readouterr().err


def test_merge_without_message_file_self_report_reaches_submission() -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1, 0],
        head_shas=[_SHA_C, _SHA_C],
    )

    outcome = _run_acceptance(fake)
    assert outcome.rc == 0
    assert fake.submissions == 1
    assert ("write_temp", _SELF_REPORTED_MERGE_MESSAGE) in fake.events


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
        *_BASE_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        *_PRECLAIM_GUARD_EVENTS,
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
        *_BASE_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        *_PRECLAIM_GUARD_EVENTS,
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
    assert (fake.claims, fake.submissions, fake.releases) == (2, 1, 0)
    selected_calls = [
        event[1]
        for event in fake.events
        if event[0] == "run"
        and event[1]
        in {
            ("git", "diff", "--name-only", "HEAD...main"),
            ("git", "merge", "--no-ff", "--no-commit", "main"),
            _provenance_argv(),
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
            _history_provenance_argv(),
            _COMMAND,
        }
    ]
    assert selected_calls == [
        _history_provenance_argv(),
        ("git", "diff", "--name-only", "HEAD...main"),
        ("git", "merge", "--no-ff", "--no-commit", "main"),
        _provenance_argv(),
        ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
        ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
        _history_provenance_argv(),
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
    assert (fake.claims, fake.submissions, fake.releases) == (2, 1, 0)
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
            _provenance_argv(),
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
            _history_provenance_argv(),
            _COMMAND,
        }
    ]
    assert selected_calls == [
        _history_provenance_argv(),
        ("git", "merge", "--no-ff", "--no-commit", "main"),
        _provenance_argv(),
        ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
        ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
        _history_provenance_argv(),
        _COMMAND,
    ]
    warning = (
        "acceptance: --owned-path 未指定のため所有実装面 overlap 判定を省略します"
    )
    assert capsys.readouterr().err.splitlines().count(warning) == 1


def test_missing_message_preflight_does_not_release_foreign_lease() -> None:
    fake = _FakeEffects()
    _preflight(fake, claim_guards=False)
    fake.is_file_queue.append((_MESSAGE, False))

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 2
    assert outcome.stage == "merge-message-preflight"
    assert fake.events == [*_BASE_PREFLIGHT_EVENTS, ("is_file", _MESSAGE)]
    fake.assert_drained()


def test_merge_sequence_and_postcheck_are_exact(capsys: pytest.CaptureFixture[str]) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.monotonic_queue[:] = [0.0, 100.0]
    fake.final_claim_age_seconds = 30
    fake.is_file_queue.append((_MESSAGE, True))
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "2\n"))
    fake.is_file_queue.append((_MESSAGE, True))
    fake.read_text_queue.append((_MESSAGE, "merge\n\nAI-Agent: codex\n"))
    fake.expect_run(("git", "merge", "--no-ff", "--no-commit", "main"))
    _message_provenance(fake)
    fake.expect_run(("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)))
    fake.expect_run(("git", "commit", "-F", str(_VALIDATED_MESSAGE)))
    fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(0, _SHA_C + "\n"))
    fake.expect_run(_history_provenance_argv())
    fake.expect_run(
        ("git", "log", "-1", "--format=%B", _SHA_C),
        DW._CommandResult(0, "merge\n\nAI-Agent: codex\n"),
    )
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(0, _SHA_C + "\n"))
    _prerun_status(fake)
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
    "merge-message-provenance",
    "commit-dry-run",
    "commit",
    "commit-rev-parse",
    "merge-history-provenance",
    "commit-message-postcheck",
    "postcheck",
    "commit-head-postcheck",
    "prerun-clean",
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
            DW._CommandResult(9)
            if stage == "claim"
            else DW._CommandResult(0, _acquired_payload()),
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
        "merge", "merge-history-provenance", "merge-message-provenance",
        "commit-dry-run", "commit",
        "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck", "prerun-clean",
    }
    if stage in merge_stages:
        fake.is_file_queue.extend([(_MESSAGE, True), (_MESSAGE, True)])
        fake.read_text_queue.append((_MESSAGE, "merge\nAI-Agent: codex\n"))
        fake.expect_run(
            ("git", "merge", "--no-ff", "--no-commit", "main"),
            DW._CommandResult(9) if stage == "merge" else DW._CommandResult(0),
        )
    if stage in {
        "merge-history-provenance",
        "merge-message-provenance", "commit-dry-run", "commit",
        "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck", "prerun-clean",
    }:
        _message_provenance(
            fake,
            DW._CommandResult(9)
            if stage == "merge-message-provenance"
            else DW._CommandResult(0),
        )
    if stage in {
        "merge-history-provenance",
        "commit-dry-run", "commit", "commit-rev-parse",
        "commit-message-postcheck", "postcheck", "commit-head-postcheck",
        "prerun-clean",
    }:
        fake.expect_run(
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            DW._CommandResult(9) if stage == "commit-dry-run" else DW._CommandResult(0),
        )
    if stage in {
        "merge-history-provenance",
        "commit", "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck", "prerun-clean",
    }:
        fake.expect_run(
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
            DW._CommandResult(9) if stage == "commit" else DW._CommandResult(0),
        )
    if stage in {
        "merge-history-provenance",
        "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck", "prerun-clean",
    }:
        fake.expect_run(
            ("git", "rev-parse", "HEAD"),
            DW._CommandResult(9) if stage == "commit-rev-parse"
            else DW._CommandResult(0, _SHA_C + "\n"),
        )
    history_provenance_stages = {
        "merge-history-provenance",
        "commit-message-postcheck", "postcheck", "commit-head-postcheck",
        "prerun-clean",
    }
    if stage in history_provenance_stages:
        fake.expect_run(
            _history_provenance_argv(),
            DW._CommandResult(9)
            if stage == "merge-history-provenance"
            else DW._CommandResult(0),
        )
    if stage in {
        "commit-message-postcheck", "postcheck", "commit-head-postcheck",
        "prerun-clean",
    }:
        fake.expect_run(
            ("git", "log", "-1", "--format=%B", _SHA_C),
            DW._CommandResult(9) if stage == "commit-message-postcheck"
            else DW._CommandResult(0, "merge\nAI-Agent: codex\n"),
        )
    if stage in {"postcheck", "commit-head-postcheck", "prerun-clean"}:
        fake.expect_run(
            ("git", "rev-list", "--count", "HEAD..main"),
            DW._CommandResult(9) if stage == "postcheck"
            else DW._CommandResult(0, "0\n"),
        )
    if stage in {"commit-head-postcheck", "prerun-clean"}:
        fake.expect_run(
            ("git", "rev-parse", "HEAD"),
            DW._CommandResult(9)
            if stage == "commit-head-postcheck"
            else DW._CommandResult(0, _SHA_C + "\n"),
        )
    if stage == "prerun-clean":
        _prerun_status(fake, returncode=9)
    if stage in {
        "merge", "merge-message-provenance",
        "commit-dry-run", "commit",
    }:
        _abort_clean(fake)
    if stage != "preclaim-rev-parse":
        _release(fake)

    outcome = _run_acceptance(fake, message=_MESSAGE if stage in merge_stages else None)

    assert outcome.rc == 70
    assert outcome.stage == stage
    expected = [
        *(
            _BASE_PREFLIGHT_EVENTS
            if stage in merge_stages
            else _PREFLIGHT_EVENTS
        )
    ]
    if stage in merge_stages:
        expected.append(("is_file", _MESSAGE))
        expected.extend(_PRECLAIM_GUARD_EVENTS)
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
        "merge-history-provenance",
        "merge-message-provenance", "commit-dry-run", "commit",
        "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck", "prerun-clean",
    }:
        expected.append(("run", _provenance_argv(), _REPO, True))
    if stage in {
        "merge-history-provenance",
        "commit-dry-run", "commit", "commit-rev-parse",
        "commit-message-postcheck", "postcheck", "commit-head-postcheck",
        "prerun-clean",
    }:
        expected.append(
            ("run", ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)), _REPO, True)
        )
    if stage in {
        "merge-history-provenance",
        "commit", "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck", "prerun-clean",
    }:
        expected.append(
            ("run", ("git", "commit", "-F", str(_VALIDATED_MESSAGE)), _REPO, True)
        )
    if stage in {
        "merge-history-provenance",
        "commit-rev-parse", "commit-message-postcheck", "postcheck",
        "commit-head-postcheck", "prerun-clean",
    }:
        expected.append(("run", ("git", "rev-parse", "HEAD"), _REPO, True))
    if stage in history_provenance_stages:
        expected.append(("run", _history_provenance_argv(), _REPO, True))
    if stage in {
        "commit-message-postcheck", "postcheck", "commit-head-postcheck",
        "prerun-clean",
    }:
        expected.append(
            ("run", ("git", "log", "-1", "--format=%B", _SHA_C), _REPO, True)
        )
    if stage in {"postcheck", "commit-head-postcheck", "prerun-clean"}:
        expected.append(
            ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True)
        )
    if stage in {"commit-head-postcheck", "prerun-clean"}:
        expected.append(("run", ("git", "rev-parse", "HEAD"), _REPO, True))
    if stage == "prerun-clean":
        expected.append(("run", _STATUS_ARGV, _REPO, True))
    if stage in merge_stages:
        expected.append(("unlink", _VALIDATED_MESSAGE))
    if stage in {
        "merge", "merge-message-provenance",
        "commit-dry-run", "commit",
    }:
        expected.extend(_ABORT_CLEAN_EVENTS)
    if stage != "preclaim-rev-parse":
        expected.append(("run", _helper("release"), _REPO, True))
    assert fake.events == expected
    fake.assert_drained()


def test_prerun_clean_allows_acceptance_submission_without_release() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(
        ("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n")
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    _prerun_status(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 0
    fake.assert_drained(
        [
            *_PREFLIGHT_EVENTS,
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
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            ("run", _STATUS_ARGV, _REPO, True),
            *_FINGERPRINT_EVENTS,
            *_WAITER_GATE_EVENTS,
            *_LAUNCHER_START_EVENTS,
            ("run", _COMMAND, _REPO, False),
            *_POSTRUN_INTEGRITY_EVENTS,
            *_SUCCESS_RECEIPT_EVENTS,
        ]
    )
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )


def test_prerun_tracked_dirty_blocks_submission_and_releases(
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(
        ("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n")
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    _prerun_status(fake, stdout=" M tracked.py\n")
    _release(fake)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "prerun-clean"
    assert outcome.source_rc is None
    assert "tracked.py" in capsys.readouterr().err
    fake.assert_drained(
        [
            *_PREFLIGHT_EVENTS,
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
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            ("run", _STATUS_ARGV, _REPO, True),
            ("run", _helper("release"), _REPO, True),
        ]
    )
    assert not any(
        event[0] == "run" and event[1] == _COMMAND for event in fake.events
    )


def test_prerun_submodule_dirty_blocks_submission_and_releases() -> None:
    fake = _SubmoduleDirtyAcceptanceEffects(dirty_status_call=2)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "prerun-clean"
    assert outcome.source_rc is None
    assert fake.status_reads == 2
    assert fake.claims == 1
    assert fake.submissions == 0
    assert fake.releases == 1
    assert fake.behind == []
    fake.assert_drained(
        [
            *_PREFLIGHT_EVENTS,
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
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            ("run", _STATUS_ARGV, _REPO, True),
            ("run", _helper("release"), _REPO, True),
        ]
    )


def test_postmerge_tracked_dirty_blocks_submission_and_releases() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    fake.is_file_queue.append((_MESSAGE, True))
    _acquired(fake)
    fake.expect_run(
        ("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n")
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "1\n"),
    )
    fake.is_file_queue.append((_MESSAGE, True))
    fake.read_text_queue.append(
        (_MESSAGE, "merge\n\nAI-Agent: product=codex; model=gpt-5; "
         "reasoning=high; role=author\n")
    )
    fake.expect_run(("git", "merge", "--no-ff", "--no-commit", "main"))
    _message_provenance(fake)
    fake.expect_run(
        ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE))
    )
    fake.expect_run(("git", "commit", "-F", str(_VALIDATED_MESSAGE)))
    fake.expect_run(
        ("git", "rev-parse", "HEAD"), DW._CommandResult(0, _SHA_C + "\n")
    )
    fake.expect_run(_history_provenance_argv())
    fake.expect_run(
        ("git", "log", "-1", "--format=%B", _SHA_C),
        DW._CommandResult(
            0,
            "merge\n\nAI-Agent: product=codex; model=gpt-5; "
            "reasoning=high; role=author\n",
        ),
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    fake.expect_run(
        ("git", "rev-parse", "HEAD"), DW._CommandResult(0, _SHA_C + "\n")
    )
    _prerun_status(fake, stdout=" M postmerge.py\n")
    _release(fake)

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "prerun-clean"
    assert outcome.source_rc is None
    expected_message = (
        b"merge\n\nAI-Agent: product=codex; model=gpt-5; "
        b"reasoning=high; role=author\n"
    )
    fake.assert_drained(
        [
            *_BASE_PREFLIGHT_EVENTS,
            ("is_file", _MESSAGE),
            *_PRECLAIM_GUARD_EVENTS,
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
            ("is_file", _MESSAGE),
            ("read_text", _MESSAGE),
            ("write_temp", expected_message),
            (
                "run",
                ("git", "merge", "--no-ff", "--no-commit", "main"),
                _REPO,
                True,
            ),
            ("run", _provenance_argv(), _REPO, True),
            (
                "run",
                ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
                _REPO,
                True,
            ),
            (
                "run",
                ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
                _REPO,
                True,
            ),
            ("run", ("git", "rev-parse", "HEAD"), _REPO, True),
            ("run", _history_provenance_argv(), _REPO, True),
            (
                "run",
                ("git", "log", "-1", "--format=%B", _SHA_C),
                _REPO,
                True,
            ),
            (
                "run",
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            ("run", ("git", "rev-parse", "HEAD"), _REPO, True),
            ("run", _STATUS_ARGV, _REPO, True),
            ("unlink", _VALIDATED_MESSAGE),
            ("run", _helper("release"), _REPO, True),
        ]
    )
    assert not any(
        event[0] == "run" and event[1] == _COMMAND for event in fake.events
    )


def test_held_self_prerun_dirty_blocks_without_releasing_lease() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _claim(fake, _SHA_A, _held_self_payload())
    fake.expect_run(
        ("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n")
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    fake.expect_run(
        ("git", "rev-list", "--count", "HEAD..main"),
        DW._CommandResult(0, "0\n"),
    )
    _prerun_status(fake, stdout=" M retained.py\n")

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "prerun-clean"
    assert outcome.source_rc is None
    fake.assert_drained(
        [
            *_PREFLIGHT_EVENTS,
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
                ("git", "rev-list", "--count", "HEAD..main"),
                _REPO,
                True,
            ),
            ("run", _STATUS_ARGV, _REPO, True),
        ]
    )
    assert not any(
        event[0] == "run" and event[1] in {_COMMAND, _helper("release")}
        for event in fake.events
    )


def test_malformed_ai_agent_message_fails_provenance_before_commit() -> None:
    message = "merge\n\nAI-Agent: codex\n"
    assert DW._message_has_ai_agent(message)
    fake = _RoutingAcceptanceEffects(
        behind=[1, 0],
        message=message,
        head_shas=[_SHA_C, _SHA_C],
        provenance_result=DW._CommandResult(9),
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "merge-message-provenance"
    assert outcome.source_rc == 9
    assert fake.claims == 1
    assert fake.submissions == 0
    assert fake.releases == 1
    assert (
        "run",
        ("git", "merge", "--abort"),
        _REPO,
        True,
    ) in fake.events
    assert not any(
        event[0] == "run"
        and event[1]
        in {
            ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
            ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
            _COMMAND,
        }
        for event in fake.events
    )
    fake.assert_drained(
        [
            *_BASE_PREFLIGHT_EVENTS,
            ("is_file", _MESSAGE),
            *_PRECLAIM_GUARD_EVENTS,
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
            ("is_file", _MESSAGE),
            ("read_text", _MESSAGE),
            ("write_temp", message.encode("utf-8")),
            (
                "run",
                ("git", "merge", "--no-ff", "--no-commit", "main"),
                _REPO,
                True,
            ),
            ("run", _provenance_argv(), _REPO, True),
            ("unlink", _VALIDATED_MESSAGE),
            *_ABORT_CLEAN_EVENTS,
            ("run", _helper("release"), _REPO, True),
        ]
    )


def test_merge_history_provenance_failure_blocks_submission_releases_and_returns_reason(
) -> None:
    violation = (
        "21582897ece7: 実装面に Codex role=author がない — "
        "paths=tools/example.py"
    )
    fake = _RoutingAcceptanceEffects(
        behind=[1],
        history_provenance_result=DW._CommandResult(
            1,
            stderr=violation + "\n",
        ),
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "merge-history-provenance"
    assert outcome.source_rc == 1
    assert outcome.detail == violation
    assert (fake.claims, fake.submissions, fake.releases) == (1, 0, 1)
    calls = [event[1] for event in fake.events if event[0] == "run"]
    assert ("git", "merge", "--abort") not in calls
    assert _COMMAND not in calls
    history_index = len(calls) - 1 - calls[::-1].index(_history_provenance_argv())
    for argv in (
        _provenance_argv(),
        ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)),
        ("git", "commit", "-F", str(_VALIDATED_MESSAGE)),
        ("git", "rev-parse", "HEAD"),
    ):
        assert calls.index(argv) < history_index


def test_merge_history_provenance_unexpected_rc_fails_closed() -> None:
    reason = "provenance audit infrastructure unavailable"
    fake = _RoutingAcceptanceEffects(
        behind=[1],
        history_provenance_result=DW._CommandResult(
            29,
            stderr=reason + "\n",
        ),
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "merge-history-provenance"
    assert outcome.source_rc == 29
    assert outcome.detail == reason
    assert (fake.claims, fake.submissions, fake.releases) == (1, 0, 1)

    calls = [event[1] for event in fake.events if event[0] == "run"]
    assert ("git", "commit", "-F", str(_VALIDATED_MESSAGE)) in calls
    assert ("git", "merge", "--abort") not in calls


def test_preflight_submodule_dirty_rejects_before_claim() -> None:
    fake = _SubmoduleDirtyAcceptanceEffects(dirty_status_call=1)

    outcome = _run_acceptance(fake)

    assert outcome.rc == 2
    assert outcome.stage == "preflight-clean"
    assert outcome.source_rc is None
    assert fake.status_reads == 1
    assert fake.claims == 0
    assert fake.submissions == 0
    assert fake.releases == 0
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
            ("run", _STATUS_ARGV, _REPO, True),
        ]
    )


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
        *_BASE_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        *_PRECLAIM_GUARD_EVENTS,
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


def test_held_self_merge_failure_aborts_without_releasing_lease() -> None:
    fake = _RoutingAcceptanceEffects(
        behind=[1],
        claim_payload=_held_self_payload(),
        merge_result=DW._CommandResult(1),
    )

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "merge"
    assert fake.releases == 0
    assert fake.submissions == 0
    assert fake.events.count(("sleep", 30)) == 0
    assert (
        "run",
        ("git", "merge", "--abort"),
        _REPO,
        True,
    ) in fake.events
    assert not any(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    )


def test_held_self_acceptance_red_retains_real_lease_without_polling(
    tmp_path: Path,
) -> None:
    lease_dir, lease_path, before = _lease_marker(tmp_path)
    fake = _RoutingAcceptanceEffects(
        behind=[0, 0],
        claim_payload=_held_self_payload(),
        command_result=DW._CommandResult(23),
        lease_dir=lease_dir,
        remove_lease_on_release=True,
    )

    outcome = _run_acceptance(fake, lease_dir=lease_dir)

    assert outcome.rc == 70
    assert outcome.stage == "acceptance-command"
    assert outcome.source_rc == 23
    assert fake.releases == 0
    assert fake.events.count(("sleep", 30)) == 0
    assert (lease_path.stat().st_mtime_ns, lease_path.read_bytes()) == before


def test_held_self_postclaim_failure_retains_real_lease_without_polling(
    tmp_path: Path,
) -> None:
    lease_dir, lease_path, before = _lease_marker(tmp_path)
    fake = _RoutingAcceptanceEffects(
        claim_payload=_held_self_payload(),
        postclaim_rc=9,
        lease_dir=lease_dir,
        remove_lease_on_release=True,
    )

    outcome = _run_acceptance(fake, lease_dir=lease_dir)

    assert outcome.rc == 70
    assert outcome.stage == "postclaim-rev-parse"
    assert outcome.source_rc == 9
    assert fake.submissions == 0
    assert fake.releases == 0
    assert fake.events.count(("sleep", 30)) == 0
    assert (lease_path.stat().st_mtime_ns, lease_path.read_bytes()) == before


def test_held_self_signal_retains_real_lease_without_polling(tmp_path: Path) -> None:
    lease_dir, lease_path, before = _lease_marker(tmp_path)
    fake = _RoutingAcceptanceEffects(
        behind=[0, 0],
        claim_payload=_held_self_payload(),
        command_result=DW._SignalReceived(signal.SIGTERM),
        lease_dir=lease_dir,
        remove_lease_on_release=True,
    )

    outcome = _run_acceptance(fake, lease_dir=lease_dir)

    assert outcome.rc == 143
    assert outcome.stage == "signal-15"
    assert fake.submissions == 1
    assert fake.releases == 0
    assert fake.events.count(("sleep", 30)) == 0
    assert (lease_path.stat().st_mtime_ns, lease_path.read_bytes()) == before


def test_acceptance_command_red_is_propagated_after_release() -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    _prerun_status(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(23), capture=False)
    _release(fake)
    outcome = _run_acceptance(fake)
    assert outcome.rc == 70
    assert outcome.stage == "acceptance-command"
    assert outcome.source_rc == 23
    assert fake.events == [
        *_PREFLIGHT_EVENTS,
        ("monotonic",),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("monotonic",),
        ("run", _helper("claim", _SHA_A), _REPO, True),
        ("run", ("git", "rev-parse", "main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", ("git", "rev-list", "--count", "HEAD..main"), _REPO, True),
        ("run", _STATUS_ARGV, _REPO, True),
        *_FINGERPRINT_EVENTS,
        *_WAITER_GATE_EVENTS,
        *_LAUNCHER_START_EVENTS,
        ("run", _COMMAND, _REPO, False),
        *_POSTRUN_INTEGRITY_EVENTS,
        *_LAUNCHER_FAILURE_CLEANUP_EVENTS,
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
        _claim(fake, _SHA_A, '{"state":"held"}')
        fake.expect_run(("git", "rev-parse", "main"), KeyboardInterrupt())
    if kind == "subprocess-error":
        outcome = _run_acceptance(fake)
    else:
        outcome = _run_acceptance(fake)
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
                ("run", ("git", "rev-parse", "main"), _REPO, True),
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
    _prerun_status(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(1), capture=False)
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
        ("run", _STATUS_ARGV, _REPO, True),
        *_FINGERPRINT_EVENTS,
        *_WAITER_GATE_EVENTS,
        *_LAUNCHER_START_EVENTS,
        ("run", _COMMAND, _REPO, False),
        *_POSTRUN_INTEGRITY_EVENTS,
        *_LAUNCHER_FAILURE_CLEANUP_EVENTS,
        ("run", _helper("release"), _REPO, True),
    ]
    fake.assert_drained()


def test_cleanup_failure_preserves_primary_receipt_detail() -> None:
    fake = _FakeEffects()
    fake.rename_result = OSError("rename failed")
    _queue_clean_acceptance_prefix(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    _release(fake, DW._CommandResult(0, '{"state":"unavailable"}'))

    outcome = _run_acceptance(fake)

    primary_detail = {
        "reason": "receipt-publish-rename",
        "observed": {"exception_type": "OSError", "errno": None},
    }
    expected = {
        "reason": "cleanup-overrode-primary",
        "observed": {
            "cleanup_detail": None,
            "primary": {
                "stage": "acceptance-receipt",
                "detail": primary_detail,
            },
        },
    }
    assert outcome == DW._Outcome(
        74,
        "release-state",
        0,
        json.dumps(expected, separators=(",", ":"), sort_keys=True),
    )
    assert json.loads(outcome.detail) == expected
    assert fake.receipt_published is False
    assert ("unlink", _RECEIPT_TEMP) in fake.events
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
    _prerun_status(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(1), capture=False)
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
        ("run", _STATUS_ARGV, _REPO, True),
        *_FINGERPRINT_EVENTS,
        *_WAITER_GATE_EVENTS,
        *_LAUNCHER_START_EVENTS,
        ("run", _COMMAND, _REPO, False),
        *_POSTRUN_INTEGRITY_EVENTS,
        *_LAUNCHER_FAILURE_CLEANUP_EVENTS,
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
        *_BASE_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        *_PRECLAIM_GUARD_EVENTS,
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
    assert {
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_NOSYSTEM",
    } <= DW._GIT_ENV_KEYS
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
    assert processes[2].communicate_calls == [1200, 100]
    assert group_kills == [(4321, signal.SIGTERM)]


def test_provenance_checker_is_sanitized_bounded_stage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    popen_calls: list[tuple[list[str], dict[str, object]]] = []
    group_kills: list[tuple[int, int]] = []

    class Process:
        pid = 5432
        returncode = 0

        def __init__(self) -> None:
            self.communicate_calls: list[object] = []

        def communicate(self, timeout: object = None) -> tuple[str, str]:
            self.communicate_calls.append(timeout)
            if len(self.communicate_calls) == 1:
                raise subprocess.TimeoutExpired(_provenance_argv(), timeout)
            self.returncode = -signal.SIGKILL
            return "", ""

        def kill(self) -> None:
            self.returncode = -signal.SIGKILL

        def wait(self, timeout: object = None) -> int:
            del timeout
            return self.returncode

    process = Process()

    def recording_popen(argv: list[str], **kwargs: object) -> Process:
        popen_calls.append((argv, kwargs))
        return process

    for key in DW._GIT_ENV_KEYS:
        monkeypatch.setenv(key, f"bad-{key}")
    monkeypatch.setattr(DW.subprocess, "Popen", recording_popen)
    monkeypatch.setattr(
        DW.os, "killpg", lambda pid, signum: group_kills.append((pid, signum))
    )

    with pytest.raises(DW._StageFailure) as exc_info:
        DW._run_capture(
            DW._default_effects(),
            _provenance_argv(),
            _REPO,
            "merge-message-provenance",
        )

    assert exc_info.value.outcome.rc == 70
    assert exc_info.value.outcome.stage == "merge-message-provenance"
    assert exc_info.value.outcome.source_rc is None
    assert len(popen_calls) == 1
    checker_argv, checker_kwargs = popen_calls[0]
    assert checker_argv == list(_provenance_argv())
    assert checker_kwargs["start_new_session"] is True
    assert all(key not in checker_kwargs["env"] for key in DW._GIT_ENV_KEYS)
    assert process.communicate_calls == [1200, 100]
    assert group_kills == [(5432, signal.SIGTERM)]


@pytest.mark.parametrize(
    "case", ["missing-delimiter", "empty-command", "poll-29", "poll-121", "default-30"],
)
def test_acceptance_cli_contract(case: str) -> None:
    base = [
        "acceptance", "--wave", _WAVE, "--lease-dir", str(_LEASE),
        "--receipt-file", str(_RECEIPT),
        "--log-file", str(_LOG),
    ]
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
        assert args.lease_optional is False
        assert child == ["harmless"]
        lease_optional_action = next(
            action
            for action in DW._acceptance_parser()._actions
            if "--lease-optional" in action.option_strings
        )
        assert (
            "後方互換のため受理する no-op。"
            "挙動を選択する flag ではない"
            in lease_optional_action.help
        )
        merge_message_action = next(
            action
            for action in DW._acceptance_parser()._actions
            if "--merge-message-file" in action.option_strings
        )
        assert "省略時は self-report を使い" in merge_message_action.help
        assert "両親と異なる実装面 path がある場合だけ" in merge_message_action.help
        return
    with pytest.raises(DW._StageFailure) as raised:
        DW._parse_cli(argv)
    assert raised.value.outcome.rc == 2


def test_acceptance_cli_lease_optional_is_legacy_noop() -> None:
    command, args, child = DW._parse_cli(
        [
            "acceptance",
            "--wave",
            _WAVE,
            "--lease-dir",
            str(_LEASE),
            "--lease-optional",
            "--receipt-file",
            str(_RECEIPT),
            "--log-file",
            str(_LOG),
            "--",
            "harmless",
        ]
    )

    assert command == "acceptance"
    assert args.lease_optional is True
    assert child == ["harmless"]


def test_acceptance_owned_path_is_repeatable() -> None:
    command, args, child = DW._parse_cli(
        [
            "acceptance",
            "--wave",
            _WAVE,
            "--lease-dir",
            str(_LEASE),
            "--receipt-file",
            str(_RECEIPT),
            "--log-file",
            str(_LOG),
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


def test_acceptance_cli_requires_receipt_file() -> None:
    with pytest.raises(DW._StageFailure) as raised:
        DW._parse_cli([
            "acceptance",
            "--wave",
            _WAVE,
            "--lease-dir",
            str(_LEASE),
            "--log-file",
            str(_LOG),
            "--",
            "harmless",
        ])
    assert raised.value.outcome == DW._Outcome(2, "cli-usage")


def test_acceptance_cli_requires_log_file() -> None:
    with pytest.raises(DW._StageFailure) as raised:
        DW._parse_cli([
            "acceptance",
            "--wave",
            _WAVE,
            "--lease-dir",
            str(_LEASE),
            "--receipt-file",
            str(_RECEIPT),
            "--",
            "harmless",
        ])
    assert raised.value.outcome == DW._Outcome(2, "cli-usage")


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
        fake.expect_run(_STATUS_ARGV, DW._CommandResult(0, status))
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
            ("run", _STATUS_ARGV, _REPO, True)
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
    _message_provenance(fake)
    fake.expect_run(("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)))
    fake.expect_run(("git", "commit", "-F", str(_VALIDATED_MESSAGE)))
    fake.expect_run(("git", "rev-parse", "HEAD"), DW._CommandResult(0, _SHA_C + "\n"))
    fake.expect_run(_history_provenance_argv())
    fake.expect_run(
        ("git", "log", "-1", "--format=%B", _SHA_C),
        DW._CommandResult(0, "merge without trailer\n"),
    )
    _release(fake)

    outcome = _run_acceptance(fake, message=_MESSAGE)

    assert outcome.rc == 70
    assert outcome.stage == "commit-message-postcheck"
    assert fake.events == [
        *_BASE_PREFLIGHT_EVENTS,
        ("is_file", _MESSAGE),
        *_PRECLAIM_GUARD_EVENTS,
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
        ("run", _provenance_argv(), _REPO, True),
        ("run", ("git", "commit", "--dry-run", "-F", str(_VALIDATED_MESSAGE)), _REPO, True),
        ("run", ("git", "commit", "-F", str(_VALIDATED_MESSAGE)), _REPO, True),
        ("run", ("git", "rev-parse", "HEAD"), _REPO, True),
        ("run", _history_provenance_argv(), _REPO, True),
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


@pytest.mark.parametrize(
    ("ownership", "release_count"),
    [
        (DW._LeaseOwnership.ACQUIRED, 1),
        (DW._LeaseOwnership.HELD_SELF, 0),
    ],
    ids=("acquired", "held-self"),
)
def test_cleanup_consumes_ownership_before_release_and_is_idempotent(
    ownership: DW._LeaseOwnership,
    release_count: int,
) -> None:
    fake = _FakeEffects()
    if release_count:
        _release(fake)
    lifecycle = DW._AcceptanceLifecycle(ownership=ownership)

    first = DW._cleanup_lifecycle(lifecycle, fake.effects, _REPO, _LEASE, _WAVE)
    second = DW._cleanup_lifecycle(lifecycle, fake.effects, _REPO, _LEASE, _WAVE)

    assert first is None
    assert second is None
    assert lifecycle.ownership is DW._LeaseOwnership.NONE
    assert sum(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    ) == release_count
    fake.assert_drained(
        [("run", _helper("release"), _REPO, True)] if release_count else []
    )


def test_signal_after_core_success_uses_restored_real_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    _preflight(fake)
    _acquired(fake)
    fake.expect_run(("git", "rev-parse", "main"), DW._CommandResult(0, _SHA_B + "\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    fake.expect_run(("git", "rev-list", "--count", "HEAD..main"), DW._CommandResult(0, "0\n"))
    _prerun_status(fake)
    fake.expect_run(_COMMAND, DW._CommandResult(0), capture=False)
    restored_handler_calls: list[int] = []
    restore_calls = 0
    real_restore = DW._restore_signal_handlers
    real_install = DW._install_signal_handlers
    internal_handler_completed = threading.Event()

    def install_observed_handler() -> dict[int, object]:
        previous = real_install()
        installed_handler = signal.getsignal(signal.SIGTERM)
        assert callable(installed_handler)

        def observed_handler(signum: int, frame: object) -> None:
            internal_handler_completed.set()
            installed_handler(signum, frame)

        signal.signal(signal.SIGTERM, observed_handler)
        return previous

    def inject_signal_then_restore(previous: dict[int, object]) -> None:
        nonlocal restore_calls
        restore_calls += 1
        if restore_calls == 1:
            os.kill(os.getpid(), signal.SIGTERM)
        real_restore(previous)

    monkeypatch.setattr(DW, "_install_signal_handlers", install_observed_handler)
    monkeypatch.setattr(DW, "_restore_signal_handlers", inject_signal_then_restore)
    original = signal.getsignal(signal.SIGTERM)
    handler_completed = threading.Event()

    def restored_handler(signum: int, frame: object) -> None:
        del frame
        restored_handler_calls.append(signum)
        handler_completed.set()

    read_fd, write_fd = os.pipe()
    os.set_blocking(read_fd, False)
    os.set_blocking(write_fd, False)
    previous_wakeup_fd = signal.set_wakeup_fd(write_fd)
    signal.signal(signal.SIGTERM, restored_handler)
    try:
        rc = DW.main(
            [
                "acceptance", "--wave", _WAVE, "--lease-dir", str(_LEASE),
                "--receipt-file", str(_RECEIPT),
                "--log-file", str(_LOG),
                "--", *_COMMAND,
            ],
            effects=fake.effects,
            repo=_REPO,
        )
        _await_python_handler(internal_handler_completed)
        _await_wakeup_token(read_fd, signal.SIGTERM)
        os.kill(os.getpid(), signal.SIGTERM)
        _await_python_handler(handler_completed)
        _await_wakeup_token(read_fd, signal.SIGTERM)
    finally:
        signal.signal(signal.SIGTERM, original)
        signal.set_wakeup_fd(previous_wakeup_fd)
        os.close(read_fd)
        os.close(write_fd)

    assert rc == 0
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
        ("run", _STATUS_ARGV, _REPO, True),
        *_FINGERPRINT_EVENTS,
        *_WAITER_GATE_EVENTS,
        *_LAUNCHER_START_EVENTS,
        ("run", _COMMAND, _REPO, False),
        *_POSTRUN_INTEGRITY_EVENTS,
        *_SUCCESS_RECEIPT_EVENTS,
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
    handler_completed = threading.Event()

    def restored_handler(signum: int, frame: object) -> None:
        del frame
        restored_handler_calls.append(signum)
        handler_completed.set()

    read_fd, write_fd = os.pipe()
    os.set_blocking(read_fd, False)
    os.set_blocking(write_fd, False)
    previous_wakeup_fd = signal.set_wakeup_fd(write_fd)
    signal.signal(signal.SIGTERM, restored_handler)
    try:
        rc = DW.main(
            [
                "acceptance", "--wave", _WAVE, "--lease-dir", str(_LEASE),
                "--receipt-file", str(_RECEIPT),
                "--log-file", str(_LOG),
                "--", *_COMMAND,
            ],
            effects=fake.effects,
            repo=_REPO,
        )
        os.kill(os.getpid(), signal.SIGTERM)
        _await_python_handler(handler_completed)
        _await_wakeup_token(read_fd, signal.SIGTERM)
    finally:
        signal.signal(signal.SIGTERM, original)
        signal.set_wakeup_fd(previous_wakeup_fd)
        os.close(read_fd)
        os.close(write_fd)

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


@pytest.mark.parametrize(
    "signum",
    (signal.SIGTERM, signal.SIGHUP, signal.SIGINT),
    ids=("sigterm", "sighup", "sigint"),
)
def test_public_main_installs_and_restores_each_handler(signum: int) -> None:
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
    observed_during_main: list[object] = []
    original_run = fake.run

    def inspecting_run(argv: object, cwd: Path, capture: bool) -> object:
        observed_during_main.append(signal.getsignal(signum))
        return original_run(argv, cwd, capture)

    fake.run = inspecting_run  # type: ignore[method-assign]

    def external_handler(received: int, frame: object) -> None:
        del received, frame

    original_handler = signal.getsignal(signum)
    signal.signal(signum, external_handler)
    try:
        rc = DW.main(
            [
                "acceptance", "--wave", _WAVE, "--lease-dir", str(_LEASE),
                "--receipt-file", str(_RECEIPT),
                "--log-file", str(_LOG),
                "--", *_COMMAND,
            ],
            effects=fake.effects,
            repo=_REPO,
        )
        assert rc == 2
        assert observed_during_main
        assert all(
            installed is not external_handler
            for installed in observed_during_main
        )
        assert all(
            installed is not signal.SIG_IGN
            and installed is not signal.SIG_DFL
            and callable(installed)
            for installed in observed_during_main
        )
        installed_handler = observed_during_main[0]
        assert callable(installed_handler)
        assert signal.getsignal(signum) is external_handler
        with pytest.raises(DW._SignalReceived) as received:
            installed_handler(signum, None)
        assert received.value.signum == signum
    finally:
        signal.signal(signum, original_handler)

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


def test_restore_sigblock_interruption_preserves_exact_mask(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry_mask = set(_REAL_PTHREAD_SIGMASK(signal.SIG_BLOCK, ()))
    proxy = _InterruptAfterHandledSigblock()
    monkeypatch.setattr(DW.signal, "pthread_sigmask", proxy)

    try:
        with pytest.raises(DW._SignalReceived) as raised:
            DW._restore_signal_handlers(
                {signal.SIGTERM: signal.getsignal(signal.SIGTERM)}
            )
        assert raised.value.signum == signal.SIGTERM
        assert proxy.injected is True
        assert set(_REAL_PTHREAD_SIGMASK(signal.SIG_BLOCK, ())) == entry_mask
    finally:
        _REAL_PTHREAD_SIGMASK(signal.SIG_SETMASK, entry_mask)


def test_cleanup_sigblock_interruption_preserves_exact_mask_without_release(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    entry_mask = set(_REAL_PTHREAD_SIGMASK(signal.SIG_BLOCK, ()))
    proxy = _InterruptAfterHandledSigblock()
    monkeypatch.setattr(DW.signal, "pthread_sigmask", proxy)

    try:
        with pytest.raises(DW._SignalReceived) as raised:
            DW._cleanup_after_claim(
                fake.effects,
                _REPO,
                _LEASE,
                _WAVE,
                merge_pending=False,
                release_lease=True,
            )
        assert raised.value.signum == signal.SIGTERM
        assert proxy.injected is True
        assert set(_REAL_PTHREAD_SIGMASK(signal.SIG_BLOCK, ())) == entry_mask
        assert fake.events == []
        fake.assert_drained()
    finally:
        _REAL_PTHREAD_SIGMASK(signal.SIG_SETMASK, entry_mask)


def test_receipt_sigblock_interruption_restores_ownership_and_exact_mask(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeEffects()
    lifecycle = DW._AcceptanceLifecycle(DW._LeaseOwnership.ACQUIRED)
    entry_mask = set(_REAL_PTHREAD_SIGMASK(signal.SIG_BLOCK, ()))
    proxy = _InterruptAfterHandledSigblock()
    monkeypatch.setattr(DW.signal, "pthread_sigmask", proxy)

    try:
        with pytest.raises(DW._SignalReceived) as raised:
            DW._publish_acceptance_receipt(
                effects=fake.effects,
                lifecycle=lifecycle,
                receipt_file=_RECEIPT,
                temp_path=_RECEIPT_TEMP,
            )
        assert raised.value.signum == signal.SIGTERM
        assert proxy.injected is True
        assert set(_REAL_PTHREAD_SIGMASK(signal.SIG_BLOCK, ())) == entry_mask
        assert lifecycle.ownership is DW._LeaseOwnership.ACQUIRED
        assert lifecycle.receipt_published is False
        assert fake.receipt_published is False
        fake.assert_drained()
    finally:
        _REAL_PTHREAD_SIGMASK(signal.SIG_SETMASK, entry_mask)


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
        fake.effects,
        _REPO,
        _LEASE,
        _WAVE,
        merge_pending=False,
        release_lease=True,
    )

    assert outcome is None
    assert fake.events == [
        ("mask", signal.SIG_BLOCK, ()),
        ("mask", signal.SIG_BLOCK, DW._HANDLED_SIGNALS),
        ("run", _helper("release"), _REPO, True),
        ("mask", signal.SIG_SETMASK, previous_mask),
    ]
    fake.assert_drained()


def test_real_git_dirty_after_claim_blocks_acceptance_command(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo-dirty"
    lease = tmp_path / "lease-dirty"
    repo.mkdir()
    lease.mkdir()
    tools = repo / "tools"
    tools.mkdir()
    real_helper = tools / "wave_land_window_real.py"
    shutil.copy2(_LEASE_HELPER, real_helper)
    helper = tools / "wave_land_window.py"
    helper.write_text(
        "import subprocess,sys\n"
        "from pathlib import Path\n"
        "real=Path(__file__).with_name('wave_land_window_real.py')\n"
        "result=subprocess.run([sys.executable,str(real),*sys.argv[1:]],"
        "capture_output=True,text=True)\n"
        "if len(sys.argv)>1 and sys.argv[1]=='claim' and result.returncode==0:\n"
        "    (Path(__file__).resolve().parents[1]/'tracked.txt').write_text("
        "'dirty after claim\\n',encoding='utf-8')\n"
        "sys.stdout.write(result.stdout)\n"
        "sys.stderr.write(result.stderr)\n"
        "raise SystemExit(result.returncode)\n",
        encoding="utf-8",
    )
    _write_test_provenance_checker(repo)
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
    git(
        "add",
        "tracked.txt",
        "tools/wave_land_window.py",
        "tools/wave_land_window_real.py",
        "tools/check_ai_provenance.py",
    )
    git("commit", "-m", "base")
    git("checkout", "-b", "worktree-dirty-real")
    git_env["PYTHONDONTWRITEBYTECODE"] = "1"
    sentinel = "REAL-DIRTY-COMMAND-SENTINEL"

    result = subprocess.run(
        [
            sys.executable,
            str(_TOOL),
            "acceptance",
            "--wave",
            "dirty-real",
            "--lease-dir",
            str(lease),
            "--receipt-file",
            str(tmp_path / "dirty-receipt.json"),
            "--log-file",
            str(tmp_path / "dirty.log"),
            "--",
            sys.executable,
            "-c",
            f"print({sentinel!r})",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=git_env,
    )

    assert result.returncode == 70
    assert "error: stage=prerun-clean rc=70" in result.stderr
    assert "tracked.txt" in result.stderr
    assert sentinel not in result.stdout
    assert not (lease / "acceptance.lease").exists()


def test_real_git_main_only_history_violation_blocks_acceptance_after_commit(
    tmp_path: Path,
) -> None:
    wave = "main-only-history"
    repo, lease, env = _real_waiter_repo(tmp_path, wave=wave)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    sha_file = tmp_path / "violation.sha"
    trace_file = tmp_path / "checker.jsonl"
    count_file = tmp_path / "runner.count"
    count_file.write_text("", encoding="utf-8")
    reason = "main-only provenance violation"
    (repo / "tools" / "check_ai_provenance.py").write_text(
        "import json, subprocess, sys\n"
        "from pathlib import Path\n"
        "head = subprocess.run(['git', 'rev-parse', 'HEAD'], check=True,\n"
        "    capture_output=True, text=True, timeout=120).stdout.strip()\n"
        "kind = 'message' if '--message-file' in sys.argv else 'history'\n"
        "rc = 0\n"
        "if kind == 'history':\n"
        f"    sha = Path({str(sha_file)!r}).read_text().strip()\n"
        "    ancestor = subprocess.run(\n"
        "        ['git', 'merge-base', '--is-ancestor', sha, 'HEAD'],\n"
        "        capture_output=True, text=True, timeout=120).returncode\n"
        "    rc = 1 if ancestor == 0 else 0 if ancestor == 1 else ancestor\n"
        "    if rc:\n"
        f"        print({reason!r} + ': ' + sha, file=sys.stderr)\n"
        f"with Path({str(trace_file)!r}).open('a') as stream:\n"
        "    stream.write(json.dumps({'kind': kind, 'head': head, 'rc': rc,\n"
        f"        'lease': Path({str(lease / 'acceptance.lease')!r}).exists()"
        "}) + '\\n')\n"
        "raise SystemExit(rc)\n",
        encoding="utf-8",
    )
    _write_exact_runner(
        repo,
        "from pathlib import Path\n"
        f"with Path({str(count_file)!r}).open('a') as stream:\n"
        "    stream.write('run\\n')\n"
        "print('IZANAGI_EFFECTIVE_SCHEDULER_V1 "
        "{\"effective_scheduler\":\"serial\"}')\n",
    )

    def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=repo, env=env, check=check,
            capture_output=True, text=True, timeout=120,
        )

    git("add", "tools")
    git("commit", "-m", "install history fixture")
    start_tip = git("rev-parse", "HEAD").stdout.strip()
    git("checkout", "main")
    git("merge", "--ff-only", f"worktree-{wave}")
    (repo / "main-only.txt").write_text("violation fixture\n", encoding="utf-8")
    git("add", "main-only.txt")
    git("commit", "-m", "main-only violation")
    main_tip = git("rev-parse", "HEAD").stdout.strip()
    sha_file.write_text(main_tip + "\n", encoding="ascii")
    git("checkout", f"worktree-{wave}")
    assert git("merge-base", "--is-ancestor", main_tip, start_tip, check=False).returncode == 1
    assert git("merge-base", "--is-ancestor", main_tip, "main").returncode == 0
    message = tmp_path / "merge-message.txt"
    message.write_text(
        "merge main\n\nAI-Agent: product=codex; model=gpt-5; "
        "reasoning=high; role=author\n", encoding="utf-8",
    )
    receipt = tmp_path / "receipt.json"
    log = tmp_path / "acceptance.log"
    result = subprocess.run(
        [
            sys.executable, str(repo / "tools" / "dev_wave_wait.py"), "acceptance",
            "--wave", wave, "--lease-dir", str(lease),
            "--merge-message-file", str(message),
            "--receipt-file", str(receipt), "--log-file", str(log),
            "--", sys.executable, str(repo / "tools" / "run_tests.py"),
        ],
        cwd=repo, env=env, capture_output=True, text=True, check=False, timeout=120,
    )

    assert count_file.read_text(encoding="utf-8").splitlines() == []
    assert result.returncode == 70, result.stderr
    assert "stage=merge-history-provenance rc=70" in result.stderr
    assert "source_rc=1" in result.stderr
    assert f"{reason}: {main_tip}" in result.stderr
    assert not (lease / "acceptance.lease").exists()
    end_tip = git("rev-parse", "HEAD").stdout.strip()
    assert end_tip != start_tip
    assert git("show", "-s", "--format=%P", "HEAD").stdout.split() == [start_tip, main_tip]
    assert git("merge-base", "--is-ancestor", main_tip, end_tip).returncode == 0
    assert git("rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).returncode == 1
    assert git("status", "--porcelain", "--untracked-files=no").stdout == ""
    assert not receipt.exists()
    assert not log.exists()
    trace = [json.loads(line) for line in trace_file.read_text().splitlines()]
    assert trace == [
        {"kind": "history", "head": start_tip, "rc": 0, "lease": False},
        {"kind": "message", "head": start_tip, "rc": 0, "lease": True},
        {"kind": "history", "head": end_tip, "rc": 1, "lease": True},
    ]


def test_real_git_production_provenance_rejects_malformed_merge_message(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo-production-provenance"
    lease = tmp_path / "lease-production-provenance"
    repo.mkdir()
    lease.mkdir()
    tools = repo / "tools"
    tools.mkdir()
    shutil.copy2(_LEASE_HELPER, tools / "wave_land_window.py")
    shutil.copy2(_TOOL, tools / "dev_wave_wait.py")
    shutil.copy2(_LAUNCHER, tools / "acceptance_launcher.py")
    shutil.copy2(_ROOT / "tools" / "check_ai_provenance.py", tools)
    shutil.copytree(
        _ROOT / "tools" / "known_violations",
        tools / "known_violations",
    )
    _write_exact_runner(
        repo,
        "print('IZANAGI_EFFECTIVE_SCHEDULER_V1 "
        "{\"effective_scheduler\":\"serial\"}')\n",
    )
    campaign = repo / "orchestrator" / "campaign"
    campaign.mkdir(parents=True)
    shutil.copy2(_ROOT / "orchestrator" / "campaign" / "__init__.py", campaign)
    shutil.copy2(_ROOT / "orchestrator" / "campaign" / "site_policy.py", campaign)
    with (campaign / "site_policy.py").open("a", encoding="utf-8") as stream:
        stream.write(
            "\n"
            "def current_site(*, require_evidence=False):\n"
            "    del require_evidence\n"
            "    return OTHER\n"
        )
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
    docs = repo / "docs"
    docs.mkdir()
    (docs / "ai-provenance.md").write_text(
        "実装面を変更する AI 関与 commit は Codex author を必須\n",
        encoding="utf-8",
    )
    valid_trailer = (
        "AI-Agent: product=codex; model=gpt-5; reasoning=high; role=author"
    )
    git("add", "tracked.txt", "tools", "orchestrator", "docs")
    git("commit", "-m", f"base\n\n{valid_trailer}")
    base_sha = git("rev-parse", "HEAD").stdout.strip()
    git("checkout", "-b", "worktree-production-provenance")
    git("checkout", "main")
    tracked.write_text("main advanced\n", encoding="utf-8")
    git("add", "tracked.txt")
    git("commit", "-m", f"advance main\n\n{valid_trailer}")
    git("checkout", "worktree-production-provenance")
    message = tmp_path / "malformed-merge-message.txt"
    message.write_text("merge main\n\nAI-Agent: codex\n", encoding="utf-8")
    git_env["PYTHONDONTWRITEBYTECODE"] = "1"
    sentinel = "PRODUCTION-PROVENANCE-COMMAND-SENTINEL"

    result = subprocess.run(
        [
            sys.executable,
            str(_TOOL),
            "acceptance",
            "--wave",
            "production-provenance",
            "--lease-dir",
            str(lease),
            "--merge-message-file",
            str(message),
            "--receipt-file",
            str(tmp_path / "provenance-receipt.json"),
            "--log-file",
            str(tmp_path / "provenance.log"),
            "--",
            sys.executable,
            "-c",
            f"print({sentinel!r})",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=git_env,
    )

    assert result.returncode == 70
    assert "error: stage=merge-message-provenance rc=70 source_rc=1" in result.stderr
    assert sentinel not in result.stdout
    assert git("rev-parse", "HEAD").stdout.strip() == base_sha
    assert git("rev-list", "--count", "HEAD..main").stdout.strip() == "1"
    assert git(
        "status", "--porcelain", "--untracked-files=no",
        "--ignore-submodules=none",
    ).stdout == ""
    merge_head = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=git_env,
    )
    assert merge_head.returncode == 1
    assert not (lease / "acceptance.lease").exists()


def _run_real_self_report_merge_case(
    tmp_path: Path,
    *,
    combined: bool,
) -> tuple[
    subprocess.CompletedProcess[str],
    Path,
    Path,
    Path,
    Path,
    dict[str, str],
    str,
]:
    wave = "self-report-combined" if combined else "self-report-main-only"
    repo, lease, env = _real_waiter_repo(tmp_path, wave=wave)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            env=env,
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()

    _write_path_aware_provenance_checker(repo)
    target = repo / "tools" / "self_report_target.py"
    target.write_text(
        "base-one\nbase-two\nbase-three\n"
        if combined
        else "base\n",
        encoding="utf-8",
    )
    git("add", "tools/check_ai_provenance.py", "tools/self_report_target.py")
    git("commit", "-m", "add self-report merge target")
    branch = f"worktree-{wave}"
    git("checkout", "main")
    git("merge", "--ff-only", branch)
    git("checkout", branch)

    if combined:
        target.write_text(
            "wave-one\nbase-two\nbase-three\n",
            encoding="utf-8",
        )
        git("add", "tools/self_report_target.py")
        git("commit", "-m", "wave changes implementation target")
        git("checkout", "main")
        target.write_text(
            "base-one\nbase-two\nmain-three\n",
            encoding="utf-8",
        )
        git("add", "tools/self_report_target.py")
        git("commit", "-m", "main changes implementation target")
        git("checkout", branch)
    else:
        git("checkout", "main")
        target.write_text("main\n", encoding="utf-8")
        git("add", "tools/self_report_target.py")
        git("commit", "-m", "main-only implementation change")
        git("checkout", branch)

    wave_head = git("rev-parse", "HEAD")
    receipt = tmp_path / "self-report-receipt.json"
    log = tmp_path / "self-report.log"
    result = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "dev_wave_wait.py"),
            "acceptance",
            "--wave",
            wave,
            "--lease-dir",
            str(lease),
            "--receipt-file",
            str(receipt),
            "--log-file",
            str(log),
            "--",
            sys.executable,
            str(repo / "tools" / "run_tests.py"),
        ],
        cwd=repo,
        env=env,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result, repo, lease, receipt, log, env, wave_head


def test_real_git_self_report_allows_main_only_implementation_merge(
    tmp_path: Path,
) -> None:
    result, repo, lease, receipt, log, env, _wave_head = (
        _run_real_self_report_merge_case(tmp_path, combined=False)
    )

    assert result.returncode == 0, result.stderr
    assert receipt.is_file()
    assert log.is_file()
    assert "merge-message-provenance" not in result.stderr
    message = subprocess.run(
        ["git", "log", "-1", "--format=%B", "HEAD"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "product=claude" in message
    assert "role=integrator" in message
    assert (lease / "acceptance.lease").is_file()


def test_real_git_self_report_rejects_combined_implementation_path_merge(
    tmp_path: Path,
) -> None:
    result, repo, lease, receipt, log, env, wave_head = (
        _run_real_self_report_merge_case(tmp_path, combined=True)
    )

    assert result.returncode == 70
    assert "error: stage=merge-message-provenance rc=70 source_rc=1" in result.stderr
    assert "acceptance-command argv=" not in result.stderr
    assert not receipt.exists()
    assert not log.exists()
    assert not (lease / "acceptance.lease").exists()
    assert subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip() == wave_head
    assert subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    ).stdout == ""


def test_default_wiring_with_real_git_and_lease_helper(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    lease = tmp_path / "lease"
    repo.mkdir()
    lease.mkdir()
    tools = repo / "tools"
    tools.mkdir()
    shutil.copy2(_LEASE_HELPER, tools / "wave_land_window.py")
    shutil.copy2(_TOOL, tools / "dev_wave_wait.py")
    shutil.copy2(_LAUNCHER, tools / "acceptance_launcher.py")
    _write_test_provenance_checker(repo)
    _write_exact_runner(
        repo,
        "from pathlib import Path\n"
        "assert Path.cwd() == Path(__file__).resolve().parents[1]\n"
        "print('CHILD-STDOUT-SENTINEL')\n"
        "print('IZANAGI_EFFECTIVE_SCHEDULER_V1 "
        "{\"effective_scheduler\":\"serial\"}')\n"
        "print('CHILD-STDERR-SENTINEL', file=__import__('sys').stderr)\n",
    )

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
    git(
        "add",
        "tracked.txt",
        "tools/wave_land_window.py",
        "tools/dev_wave_wait.py",
        "tools/acceptance_launcher.py",
        "tools/run_tests.py",
        "tools/check_ai_provenance.py",
    )
    git("commit", "-m", "base")
    git("checkout", "-b", "worktree-integration")
    git("checkout", "main")
    tracked.write_text("main advanced\n", encoding="utf-8")
    git("add", "tracked.txt", "tools/wave_land_window.py")
    git("commit", "-m", "advance main")
    git("checkout", "worktree-integration")
    message = tmp_path / "merge-message.txt"
    message.write_text(
        "merge main\n\nAI-Agent: product=codex; model=gpt-5; "
        "reasoning=high; role=author\n",
        encoding="utf-8",
    )

    child = (
        "import pathlib,sys; "
        "expected=pathlib.Path(sys.argv[1]); "
        "assert pathlib.Path.cwd()==expected; "
        "print('CHILD-STDOUT-SENTINEL'); "
        "print('IZANAGI_EFFECTIVE_SCHEDULER_V1 "
        "{\"effective_scheduler\":\"serial\"}'); "
        "print('CHILD-STDERR-SENTINEL', file=sys.stderr)"
    )
    waiter_env = {
        **git_env,
        "IZANAGI_WAVE_LEASE_DIR": str(lease),
        "IZANAGI_ACCEPTANCE_SHARDS": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }

    result = subprocess.run(
        [
            sys.executable,
            str(_TOOL),
            "acceptance",
            "--wave",
            "integration",
            "--merge-message-file",
            str(message),
            "--receipt-file",
            str(tmp_path / "integration-receipt.json"),
            "--log-file",
            str(tmp_path / "integration.log"),
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
    captured_log = (tmp_path / "integration.log").read_text(encoding="utf-8")
    assert "CHILD-STDOUT-SENTINEL" in captured_log
    assert "CHILD-STDERR-SENTINEL" in captured_log
    assert "CHILD-STDOUT-SENTINEL" not in result.stdout
    stderr_without_diagnostic_argv = "\n".join(
        line
        for line in result.stderr.splitlines()
        if not line.startswith("acceptance-command argv=")
    )
    assert "CHILD-STDERR-SENTINEL" not in stderr_without_diagnostic_argv
    integration_receipt = json.loads(
        (tmp_path / "integration-receipt.json").read_text(encoding="ascii")
    )
    assert integration_receipt["log_sha256"] == hashlib.sha256(
        (tmp_path / "integration.log").read_bytes()
    ).hexdigest()
    assert "AI-Agent: product=codex" in git(
        "log", "-1", "--format=%B", "HEAD"
    ).stdout
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


def _run_runtime_waiter_bytes_case(
    tmp_path: Path,
    *,
    wave: str,
    change_waiter_on_main: bool,
) -> tuple[subprocess.CompletedProcess[str], Path, Path, Path, Path, dict[str, str]]:
    main_repo = tmp_path / "main-repo"
    wave_repo = tmp_path / "wave-repo"
    lease = tmp_path / "lease"
    main_repo.mkdir()
    lease.mkdir()
    tools = main_repo / "tools"
    tools.mkdir()
    shutil.copy2(_TOOL, tools / "dev_wave_wait.py")
    shutil.copy2(_LEASE_HELPER, tools / "wave_land_window.py")
    shutil.copy2(_LAUNCHER, tools / "acceptance_launcher.py")
    _write_test_provenance_checker(main_repo)
    counter = tmp_path / "command-runs.txt"
    _write_exact_runner(
        main_repo,
        "from pathlib import Path\n"
        f"with Path({str(counter)!r}).open('a', encoding='ascii') as stream:\n"
        "    stream.write('run\\n')\n"
        "print('IZANAGI_EFFECTIVE_SCHEDULER_V1 "
        "{\"effective_scheduler\":\"serial\"}')\n",
    )
    env = {
        **{
            key: value
            for key, value in os.environ.items()
            if key not in DW._GIT_ENV_KEYS
            and key not in {
                "PYTEST_ADDOPTS",
                "PYTEST_PLUGINS",
                "IZANAGI_TASK_RUN_ID",
                "IZANAGI_TASK_RUNS_ROOT",
            }
        },
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }

    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["IZANAGI_ACCEPTANCE_SHARDS"] = "1"

    def git(repo: Path, *args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            env=env,
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()

    git(main_repo, "init", "-b", "main")
    git(main_repo, "add", "tools")
    git(main_repo, "commit", "-m", "version A")
    branch = f"worktree-{wave}"
    git(main_repo, "branch", branch)
    git(main_repo, "worktree", "add", str(wave_repo), branch)
    if change_waiter_on_main:
        with (tools / "dev_wave_wait.py").open("a", encoding="utf-8") as stream:
            stream.write("\n# version B\n")
        git(main_repo, "add", "tools/dev_wave_wait.py")
    else:
        (main_repo / "main-advance.txt").write_text("advanced\n", encoding="utf-8")
        git(main_repo, "add", "main-advance.txt")
    git(main_repo, "commit", "-m", "advance main")

    message = tmp_path / "merge-message.txt"
    message.write_text(
        "merge main\n\nAI-Agent: product=codex; model=gpt-5; "
        "reasoning=high; role=author\n",
        encoding="utf-8",
    )
    receipt = tmp_path / "acceptance-receipt.json"
    log = tmp_path / "acceptance.log"
    result = subprocess.run(
        [
            sys.executable,
            str(wave_repo / "tools" / "dev_wave_wait.py"),
            "acceptance",
            "--wave",
            wave,
            "--lease-dir",
            str(lease),
            "--merge-message-file",
            str(message),
            "--receipt-file",
            str(receipt),
            "--log-file",
            str(log),
            "--",
            sys.executable,
            str(wave_repo / "tools" / "run_tests.py"),
            str(counter),
        ],
        cwd=wave_repo,
        env=env,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result, wave_repo, lease, receipt, counter, env


def test_real_waiter_process_rejects_merged_tip_with_different_waiter_bytes(
    tmp_path: Path,
) -> None:
    wave = "runtime-bytes-negative"
    result, _repo, lease, receipt, counter, _env = _run_runtime_waiter_bytes_case(
        tmp_path,
        wave=wave,
        change_waiter_on_main=True,
    )

    assert result.returncode == 70, result.stderr
    assert "error: stage=restart-required rc=70 detail=" in result.stderr
    assert '"reason":"receipt-waiter-sha256-mismatch"' in result.stderr
    assert "diagnostic: stage=restart-required rc=70 detail=" in result.stdout
    assert '"reason":"receipt-waiter-sha256-mismatch"' in result.stdout
    assert "acceptance-command argv=" not in result.stderr
    assert not counter.exists()
    assert not receipt.exists()
    assert not (lease / "acceptance.lease").exists()


def test_real_waiter_process_accepts_merged_tip_with_same_waiter_bytes(
    tmp_path: Path,
) -> None:
    wave = "runtime-bytes-positive"
    result, repo, lease, receipt, counter, env = _run_runtime_waiter_bytes_case(
        tmp_path,
        wave=wave,
        change_waiter_on_main=False,
    )

    assert result.returncode == 0, result.stderr
    assert counter.read_text(encoding="ascii").splitlines() == ["run"]
    payload = json.loads(receipt.read_text(encoding="ascii"))
    assert payload["schema_version"] == "dev-wave-acceptance-receipt/v5"
    assert payload["flake_nodeids"] == []
    waiter_blob_sha = subprocess.run(
        ["git", "rev-parse", "HEAD:tools/dev_wave_wait.py"],
        cwd=repo,
        env=env,
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    assert payload["waiter_blob_sha"] == waiter_blob_sha
    assert (lease / "acceptance.lease").is_file()


def test_default_wiring_second_acceptance_reuses_self_held_lease(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    lease_dir = tmp_path / "lease"
    repo.mkdir()
    lease_dir.mkdir()
    (repo / "tools").mkdir()
    helper = repo / "tools" / "wave_land_window.py"
    shutil.copy2(_LEASE_HELPER, helper)
    shutil.copy2(_TOOL, repo / "tools" / "dev_wave_wait.py")
    shutil.copy2(_LAUNCHER, repo / "tools" / "acceptance_launcher.py")
    _write_test_provenance_checker(repo)
    _write_exact_runner(
        repo,
        "print('SECOND-ACCEPTANCE-SENTINEL')\n"
        "print('IZANAGI_EFFECTIVE_SCHEDULER_V1 "
        "{\"effective_scheduler\":\"serial\"}')\n",
    )
    git_env = {
        **{key: value for key, value in os.environ.items() if key not in DW._GIT_ENV_KEYS},
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
        "IZANAGI_ACCEPTANCE_SHARDS": "1",
    }

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
            env=git_env,
        ).stdout.strip()

    git("init", "-b", "main")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(
        "add",
        "tracked.txt",
        "tools/wave_land_window.py",
        "tools/dev_wave_wait.py",
        "tools/acceptance_launcher.py",
        "tools/run_tests.py",
        "tools/check_ai_provenance.py",
    )
    git("commit", "-m", "base")
    git("checkout", "-b", "worktree-deadlock")
    main_sha = git("rev-parse", "main")
    git_env["PYTHONDONTWRITEBYTECODE"] = "1"
    claim = subprocess.run(
        [
            sys.executable,
            str(helper),
            "claim",
            "--lease-dir",
            str(lease_dir),
            "--wave",
            "deadlock",
            "--main-sha",
            main_sha,
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=git_env,
    )
    assert claim.returncode == 0, claim.stderr
    assert json.loads(claim.stdout)["state"] == "acquired"
    lease_path = lease_dir / "acceptance.lease"
    before_payload = lease_path.read_bytes()
    before_mtime = lease_path.stat().st_mtime_ns - 10_000_000_000
    os.utime(lease_path, ns=(before_mtime, before_mtime))

    result = subprocess.run(
        [
            sys.executable,
            str(_TOOL),
            "acceptance",
            "--wave",
            "deadlock",
            "--lease-dir",
            str(lease_dir),
            "--max-wait-seconds",
            "1",
            "--receipt-file",
            str(tmp_path / "second-receipt.json"),
            "--log-file",
            str(tmp_path / "second.log"),
            "--",
            sys.executable,
            "-c",
            "print('SECOND-ACCEPTANCE-SENTINEL'); "
            "print('IZANAGI_EFFECTIVE_SCHEDULER_V1 "
            "{\"effective_scheduler\":\"serial\"}')",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=git_env,
    )

    assert result.returncode == 0, result.stderr
    assert "SECOND-ACCEPTANCE-SENTINEL" in (
        tmp_path / "second.log"
    ).read_text(encoding="utf-8")
    assert "SECOND-ACCEPTANCE-SENTINEL" not in result.stdout
    assert "claim-timeout" not in result.stderr
    assert lease_path.read_bytes() == before_payload
    assert lease_path.stat().st_mtime_ns > before_mtime


def test_public_main_real_signal_releases_lease(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    lease = tmp_path / "lease"
    repo.mkdir()
    lease.mkdir()
    (repo / "tools").mkdir()
    shutil.copy2(_LEASE_HELPER, repo / "tools" / "wave_land_window.py")
    shutil.copy2(_TOOL, repo / "tools" / "dev_wave_wait.py")
    shutil.copy2(_LAUNCHER, repo / "tools" / "acceptance_launcher.py")
    _write_test_provenance_checker(repo)
    _write_exact_runner(
        repo,
        "import os, signal\n"
        "os.kill(os.getppid(), signal.SIGTERM)\n",
    )
    git_env = {
        **{key: value for key, value in os.environ.items() if key not in DW._GIT_ENV_KEYS},
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
        "IZANAGI_ACCEPTANCE_SHARDS": "1",
    }

    def git(*args: str) -> None:
        subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True,
            env=git_env,
        )

    git("init", "-b", "main")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(
        "add",
        "tracked.txt",
        "tools/wave_land_window.py",
        "tools/dev_wave_wait.py",
        "tools/acceptance_launcher.py",
        "tools/run_tests.py",
        "tools/check_ai_provenance.py",
    )
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
            "--receipt-file",
            str(tmp_path / "signal-receipt.json"),
            "--log-file",
            str(tmp_path / "signal.log"),
            "--",
            sys.executable,
            "-c",
            signal_child,
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env={
            **git_env,
            "IZANAGI_WAVE_LEASE_DIR": str(lease),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
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
    shutil.copy2(_TOOL, repo / "tools" / "dev_wave_wait.py")
    shutil.copy2(_LAUNCHER, repo / "tools" / "acceptance_launcher.py")
    _write_test_provenance_checker(repo)
    _write_exact_runner(
        repo,
        "print('IZANAGI_EFFECTIVE_SCHEDULER_V1 "
        "{\"effective_scheduler\":\"serial\"}')\n",
    )
    git_env = {
        **{key: value for key, value in os.environ.items() if key not in DW._GIT_ENV_KEYS},
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
        "IZANAGI_ACCEPTANCE_SHARDS": "1",
    }

    def git(*args: str) -> None:
        subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True,
            env=git_env,
        )

    git("init", "-b", "main")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(
        "add",
        "tracked.txt",
        "tools/wave_land_window.py",
        "tools/dev_wave_wait.py",
        "tools/acceptance_launcher.py",
        "tools/run_tests.py",
        "tools/check_ai_provenance.py",
    )
    git("commit", "-m", "base")
    git("checkout", "-b", "worktree-signal-success")
    runner = tmp_path / "success-boundary.py"
    runner.write_text(
        "import importlib.util, os, select, signal, sys, threading\n"
        "from pathlib import Path\n"
        "spec=importlib.util.spec_from_file_location('waiter', sys.argv[1])\n"
        "module=importlib.util.module_from_spec(spec)\n"
        "sys.modules[spec.name]=module\n"
        "spec.loader.exec_module(module)\n"
        "received=[]\n"
        "handled=threading.Event()\n"
        "def restored(n, f):\n"
        "    received.append(n)\n"
        "    handled.set()\n"
        "read_fd,write_fd=os.pipe()\n"
        "os.set_blocking(read_fd, False)\n"
        "os.set_blocking(write_fd, False)\n"
        "old_wakeup=signal.set_wakeup_fd(write_fd)\n"
        "signal.signal(signal.SIGTERM, restored)\n"
        "try:\n"
        "    rc=module.main(['acceptance','--wave','signal-success',"
        "'--receipt-file',sys.argv[3],'--log-file',sys.argv[4],'--',"
        "sys.executable,'-c',\"print('IZANAGI_EFFECTIVE_SCHEDULER_V1 "
        "{\\\"effective_scheduler\\\":\\\"serial\\\"}')\"], repo=Path(sys.argv[2]))\n"
        "    os.kill(os.getpid(), signal.SIGTERM)\n"
        "    if not handled.wait(5.0):\n"
        "        raise RuntimeError('Python signal handler did not run')\n"
        "    readable,_,_=select.select([read_fd], [], [], 5.0)\n"
        "    if readable != [read_fd]:\n"
        "        raise RuntimeError('C signal handler did not publish a token')\n"
        "    token=os.read(read_fd, 1)\n"
        "    if token != bytes((signal.SIGTERM & 0xff,)):\n"
        "        raise RuntimeError(f'unexpected wakeup token: {token!r}')\n"
        "    print(f'RESTORED={received} RC={rc} TOKEN={list(token)}')\n"
        "finally:\n"
        "    signal.set_wakeup_fd(old_wakeup)\n"
        "    os.close(read_fd)\n"
        "    os.close(write_fd)\n"
        "raise SystemExit(rc)\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(runner),
            str(_TOOL),
            str(repo),
            str(tmp_path / "signal-success-receipt.json"),
            str(tmp_path / "signal-success.log"),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env={
            **git_env,
            "IZANAGI_WAVE_LEASE_DIR": str(lease),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )

    assert result.returncode == 0, result.stderr
    assert f"RESTORED=[{signal.SIGTERM}] RC=0" in result.stdout
    assert f"TOKEN=[{signal.SIGTERM & 0xFF}]" in result.stdout
    assert (lease / "acceptance.lease").is_file()


def _attempt_journals(stderr: str) -> list[dict[str, object]]:
    return [
        json.loads(line[len(DW._ATTEMPT_JOURNAL_PREFIX):])
        for line in stderr.splitlines()
        if line.startswith(DW._ATTEMPT_JOURNAL_PREFIX)
    ]


def test_no_verdict_attempt_retries_in_same_process_and_keeps_owned_lease(
    capsys: pytest.CaptureFixture[str],
) -> None:
    first_log = _dispatch_outcome_marker()
    second_log = _scheduler_marker()
    lifecycle = DW._AcceptanceLifecycle()
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[first_log, second_log],
    )
    fake.lifecycle_to_observe = lifecycle

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    archive = _LOG.with_name(_LOG.name + ".attempt-01.no-verdict")
    assert outcome == DW._Outcome(0)
    assert fake.submissions == 2
    assert fake.claims == 4
    assert fake.releases == 0
    assert fake.submission_ownerships == [
        DW._LeaseOwnership.ACQUIRED,
        DW._LeaseOwnership.ACQUIRED,
    ]
    assert lifecycle.ownership is DW._LeaseOwnership.RETAINED
    assert fake.byte_files[archive] == first_log
    assert fake.byte_files[_LOG] == second_log
    journals = _attempt_journals(capsys.readouterr().err)
    assert [item["attempt"] for item in journals] == [1, 2]
    assert set(journals[0]) == {
        "attempt", "classification", "raw_child_rc", "normalized_child_rc",
        "archived_log_path", "log_sha256", "claimed_main", "retry", "reason",
    }
    assert journals[0]["classification"] == "no-verdict-infra"
    assert journals[0]["raw_child_rc"] == 16
    assert journals[0]["normalized_child_rc"] == 16
    assert journals[0]["claimed_main"] == _SHA_A
    assert journals[0]["retry"] is True
    assert journals[0]["reason"] == "retryable-no-verdict-infra"
    assert journals[0]["archived_log_path"] == str(archive)
    assert journals[0]["log_sha256"] == hashlib.sha256(first_log).hexdigest()
    assert journals[1]["classification"] == "child-green"
    assert journals[1]["raw_child_rc"] == 0
    assert journals[1]["normalized_child_rc"] == 0
    assert journals[1]["retry"] is False
    assert journals[1]["reason"] == "child-verdict"


def test_retry_keeps_priority_with_real_lease_and_competing_ticket(
    tmp_path: Path,
) -> None:
    lease_dir = tmp_path / "lease"
    lease_dir.mkdir()
    competitor_wave = "later-competing-wave"
    fake = _RealLeaseRetryEffects(
        lease_dir=lease_dir,
        command_results=[16, 0],
        logs=[_dispatch_outcome_marker(), _scheduler_marker()],
        competitor_wave=competitor_wave,
    )

    outcome = _run_acceptance(fake, lease_dir=lease_dir)

    competitor_holder = hashlib.sha256(
        competitor_wave.encode("utf-8")
    ).hexdigest()[:12]
    assert outcome == DW._Outcome(0)
    assert fake.submissions == 2
    assert fake.competitor_claim is not None
    assert fake.competitor_claim["state"] == "held"
    assert not (lease_dir / f"ticket.{competitor_holder}").is_file()
    assert (lease_dir / "acceptance.lease").is_file()


def test_retry_renew_restores_real_lease_ttl_without_replacing_inode(
    tmp_path: Path,
) -> None:
    lease_dir = tmp_path / "lease"
    lease_dir.mkdir()
    fake = _RealLeaseRetryEffects(
        lease_dir=lease_dir,
        command_results=[16, 0],
        logs=[_dispatch_outcome_marker(), _scheduler_marker()],
        age_before_retry_seconds=120,
    )

    outcome = _run_acceptance(fake, lease_dir=lease_dir)

    assert outcome == DW._Outcome(0)
    assert fake.aged_lease_stat is not None
    assert fake.archive_lease_stat is not None
    assert fake.archive_lease_stat.st_ino == fake.aged_lease_stat.st_ino
    assert fake.archive_lease_stat.st_mtime_ns > fake.aged_lease_stat.st_mtime_ns
    assert fake.renew_stats[0][2]["state"] == "held-self"
    assert fake.renew_stats[0][2]["age_seconds"] == 0


def test_attempt_two_terminal_releases_real_owned_lease(tmp_path: Path) -> None:
    lease_dir = tmp_path / "lease"
    lease_dir.mkdir()
    lifecycle = DW._AcceptanceLifecycle()
    marker = _dispatch_outcome_marker()
    fake = _RealLeaseRetryEffects(
        lease_dir=lease_dir,
        command_results=[16, 16],
        logs=[marker, marker],
    )

    outcome = _run_acceptance(
        fake,
        lease_dir=lease_dir,
        lifecycle=lifecycle,
    )

    assert outcome == DW._Outcome(70, "acceptance-command", 16)
    assert fake.submissions == 2
    assert len(fake.release_results) == 1
    assert fake.release_results[0]["state"] == "released"
    assert fake.release_results[0]["holder"] == _HOLDER
    assert not (lease_dir / "acceptance.lease").exists()
    assert lifecycle.ownership is DW._LeaseOwnership.NONE


@pytest.mark.parametrize(
    ("child_rc", "expected_rc", "expected_claims"),
    [(0, 0, 2), (1, 70, 1)],
    ids=("green", "red"),
)
def test_child_verdict_attempt_is_never_retried(
    child_rc: int,
    expected_rc: int,
    expected_claims: int,
) -> None:
    fake = _RetryAcceptanceEffects(
        command_results=[child_rc, 0],
        logs=[_scheduler_marker(), _scheduler_marker()],
    )

    outcome = _run_acceptance(fake)

    assert outcome.rc == expected_rc
    assert fake.submissions == 1
    assert fake.claims == expected_claims
    assert not any(event[0] == "run_with_input" for event in fake.events)


@pytest.mark.parametrize(
    "log_bytes",
    [
        b"dispatch failed without attestation\n",
        _dispatch_outcome_marker() + _dispatch_outcome_marker(),
        _dispatch_outcome_marker(child_started=True, child_rc=1),
        _dispatch_outcome_marker(relay=True),
        DW._DISPATCH_OUTCOME_PREFIX + b"not-json\n",
        DW._DISPATCH_OUTCOME_PREFIX
        + b'{"child_rc":null,"child_started":true,"child_started":false,'
        + b'"kind":"infra","reason":"queue-wait-timeout"}\n',
        _dispatch_outcome_marker()[:-1],
        _dispatch_outcome_marker(child_rc=1),
        _dispatch_outcome_marker(reason="overall-timeout"),
        _dispatch_outcome_marker(
            child_started=True,
            reason="receipt-persist-failed",
        ),
        _dispatch_outcome_marker() + b"\xff\n",
        _dispatch_outcome_marker()
        + b"x" * (DW._PYTEST_TRACE_LINE_MAX_BYTES + 1)
        + b"\n",
    ],
    ids=(
        "missing", "duplicate", "child-started", "relay", "malformed",
        "duplicate-key", "unterminated-eof", "false-with-child-rc",
        "false-with-nonqueue-reason", "persist-without-child-rc",
        "invalid-utf8", "oversized-line",
    ),
)
def test_dispatch_attestation_ambiguity_never_retries(log_bytes: bytes) -> None:
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[log_bytes, _scheduler_marker()],
    )

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, "acceptance-command", 16)
    assert fake.submissions == 1
    assert fake.claims == 1
    assert fake.releases == 1


@pytest.mark.parametrize(
    "framing",
    [
        (
            (
                "| [先頭 4096 bytes を省略。末尾 65536 bytes を収集]"
                "\\nretained tail\n"
            ).encode("utf-8")
        ),
        (
            b"[Pegasus dispatch] request 424242.nqsv child stdout begin "
            b"(size=70000 bytes, omitted_bytes=4464)\n"
        ),
        (
            b"[Pegasus dispatch] request 424242.nqsv child log relay "
            b"aborted after broken pipe on stderr\n"
        ),
    ],
    ids=("upstream-omission", "relay-truncation", "relay-abort"),
)
def test_dispatch_truncation_framing_makes_pytest_absence_indeterminate(
    framing: bytes,
) -> None:
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[_dispatch_outcome_marker() + framing, _scheduler_marker()],
    )

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, "acceptance-command", 16)
    assert fake.submissions == 1
    assert fake.claims == 1
    assert fake.releases == 1


@pytest.mark.parametrize(
    "trace",
    [
        b"FAILED orchestrator/tests/test_known.py::test_known\n",
        b"================ 1 failed in 0.12s ================\n",
    ],
    ids=("red-nodeid", "session-summary"),
)
def test_pytest_verdict_trace_blocks_retry_even_with_prechild_attestation(
    trace: bytes,
) -> None:
    log_bytes = _dispatch_outcome_marker() + trace
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[log_bytes, _scheduler_marker()],
    )

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, "acceptance-command", 16)
    assert fake.submissions == 1
    assert fake.releases == 1


def test_no_verdict_retry_stops_at_attempt_limit() -> None:
    marker = _dispatch_outcome_marker()
    fake = _RetryAcceptanceEffects(
        command_results=[16, 16, 0],
        logs=[marker, marker, _scheduler_marker()],
    )

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, "acceptance-command", 16)
    assert fake.submissions == DW._MAX_ACCEPTANCE_ATTEMPTS
    assert fake.command_results == [0]
    assert fake.releases == 1


def test_no_verdict_retry_stops_at_shared_deadline() -> None:
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[_dispatch_outcome_marker(), _scheduler_marker()],
        advance_after_first=31.0,
    )

    outcome = _run_acceptance(fake, max_wait=30)

    assert outcome == DW._Outcome(70, "acceptance-command", 16)
    assert fake.submissions == 1
    assert fake.releases == 1


def test_acceptance_shared_deadline_is_fixed_at_invocation_entry() -> None:
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[_dispatch_outcome_marker(), _scheduler_marker()],
        advance_before_first_claim=31.0,
    )

    outcome = _run_acceptance(fake, max_wait=30)

    assert outcome == DW._Outcome(70, "claim-timeout")
    assert fake.claims == 0
    assert fake.submissions == 0
    assert fake.releases == 0


def test_attempt_two_deadline_is_rechecked_immediately_before_command() -> None:
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[_dispatch_outcome_marker(), _scheduler_marker()],
        advance_on_claim={3: 31.0},
    )

    outcome = _run_acceptance(fake, max_wait=30)

    assert outcome == DW._Outcome(70, "acceptance-command-deadline")
    assert fake.claims == 3
    assert fake.submissions == 1
    assert fake.releases == 1


def test_retry_success_uses_only_success_attempt_values_and_v5_schema() -> None:
    first_log = _dispatch_outcome_marker()
    second_log = b"second attempt\n" + _scheduler_marker("loadgroup", relay=True)
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[first_log, second_log],
        head_shas=[_SHA_A, _SHA_A, _SHA_B, _SHA_B],
    )
    fake.env_after_archive = {
        "IZANAGI_TASK_RUN_ID": "attempt-two",
        "IZANAGI_TASK_RUNS_ROOT": "/task-runs",
    }

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(0)
    receipt = json.loads(fake.receipt_content)
    assert receipt["tested_main"] == _SHA_A
    assert receipt["tested_tip"] == _SHA_B
    assert receipt["log_sha256"] == hashlib.sha256(second_log).hexdigest()
    assert receipt["effective_scheduler"] == "loadgroup"
    assert receipt["env_projection"]["IZANAGI_TASK_RUN_ID"] == "attempt-two"
    assert receipt["env_projection"]["IZANAGI_TASK_RUNS_ROOT"] == "/task-runs"
    assert receipt["log_sha256"] != hashlib.sha256(first_log).hexdigest()
    assert receipt["schema_version"] == "dev-wave-acceptance-receipt/v5"
    assert receipt["flake_nodeids"] == []
    assert set(receipt) == {
        "schema_version", "authority_kind", "acceptance_wave", "lease_holder",
        "tested_main", "tested_tip", "argv", "resolved_runner_path", "child_rc",
        "pre_fingerprint", "post_fingerprint", "waiter_blob_sha",
        "env_projection", "verdict", "log_sha256", "checker_rc",
        "checker_status", "checker_blob_sha", "checker_receipt_sha256",
        "red_nodeids", "flake_nodeids", "effective_scheduler",
        "launcher_source_revision", "launcher_blob_sha",
        "launcher_executed_sha256", "waiter_executed_sha256",
        "runner_executed_sha256",
    }


def test_retry_main_advance_is_terminal_before_second_command() -> None:
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[_dispatch_outcome_marker(), _scheduler_marker()],
        main_after_first=_SHA_B,
    )

    outcome = _run_acceptance(fake)

    assert outcome.rc == 70
    assert outcome.stage == "claim-self-unverified"
    assert fake.submissions == 1
    assert fake.claims == 3
    assert fake.releases == 1


def test_retry_archive_collision_stops_without_overwrite() -> None:
    archive = _LOG.with_name(_LOG.name + ".attempt-01.no-verdict")
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[_dispatch_outcome_marker(), _scheduler_marker()],
    )
    fake.existing_paths.add(archive)
    fake.byte_files[archive] = b"existing archive\n"

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, "acceptance-retry-log-archive")
    assert fake.submissions == 1
    assert fake.byte_files[archive] == b"existing archive\n"
    assert fake.byte_files[_LOG] == _dispatch_outcome_marker()
    assert fake.releases == 1


def test_default_retry_archive_never_overwrites_existing_sibling(
    tmp_path: Path,
) -> None:
    source = tmp_path / "acceptance.log"
    destination = tmp_path / "acceptance.log.attempt-01.no-verdict"
    source.write_bytes(b"new evidence\n")
    destination.write_bytes(b"existing evidence\n")

    with pytest.raises(FileExistsError):
        DW._default_archive_log(source, destination)

    assert source.read_bytes() == b"new evidence\n"
    assert destination.read_bytes() == b"existing evidence\n"


@pytest.mark.parametrize(
    "renew_payload",
    [
        _acquired_payload(),
        _held_self_payload(holder="0" * 12),
        _held_self_payload(main_sha=_SHA_B),
    ],
    ids=("not-held-self", "holder-mismatch", "main-mismatch"),
)
def test_retry_renew_requires_same_held_self_lease(renew_payload: str) -> None:
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[_dispatch_outcome_marker(), _scheduler_marker()],
    )
    fake.claim_payload_overrides[2] = renew_payload

    outcome = _run_acceptance(fake)

    assert outcome.stage == "acceptance-retry-renew"
    assert fake.submissions == 1
    assert fake.releases == 1


def test_retry_does_not_remove_receipt_that_appears_between_attempts() -> None:
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[_dispatch_outcome_marker(), _scheduler_marker()],
    )
    fake.inject_artifact_after_archive = _RECEIPT

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(2, "acceptance-receipt-preflight")
    assert fake.submissions == 1
    assert _RECEIPT in fake.existing_paths
    assert not any(
        event[0] == "unlink" and event[1] == _RECEIPT
        for event in fake.events
    )
    assert fake.releases == 1


def test_existing_cleanup_failure_blocks_retry() -> None:
    lifecycle = DW._AcceptanceLifecycle(
        cleanup_failure=DW._Outcome(74, "release"),
    )
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[_dispatch_outcome_marker(), _scheduler_marker()],
    )

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    assert outcome == DW._Outcome(70, "acceptance-command", 16)
    assert fake.submissions == 1
    assert fake.releases == 1


def test_held_self_ownership_never_retries_no_verdict_attempt() -> None:
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[_dispatch_outcome_marker(), _scheduler_marker()],
    )
    fake.claim_payload_overrides[1] = _held_self_payload()

    outcome = _run_acceptance(fake)

    assert outcome == DW._Outcome(70, "acceptance-command", 16)
    assert fake.submissions == 1
    assert fake.releases == 0


def test_signal_during_retry_renew_releases_once_and_stops() -> None:
    lifecycle = DW._AcceptanceLifecycle()
    fake = _RetryAcceptanceEffects(
        command_results=[16, 0],
        logs=[_dispatch_outcome_marker(), _scheduler_marker()],
        signal_on_claim=2,
    )

    outcome = _run_acceptance(fake, lifecycle=lifecycle)

    assert outcome == DW._Outcome(143, "signal-15")
    assert fake.submissions == 1
    assert fake.releases == 1
    assert lifecycle.ownership is DW._LeaseOwnership.NONE
    assert sum(
        event[0] == "run" and event[1] == _helper("release")
        for event in fake.events
    ) == 1
