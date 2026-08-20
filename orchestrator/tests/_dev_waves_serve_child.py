"""Dedicated subprocess entrypoint for the long-path serve integration test."""
from __future__ import annotations

import contextlib
import errno
import json
import math
import numbers
import os
import socket
import sys
import threading
import time
import traceback
import uuid
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from pathlib import Path

from tools.dev_waves.checker import CheckSpec
from tools.dev_waves.daemon import (
    Supervisor,
    SupervisorConfig,
    SupervisorDependencies,
    SupervisorProfile,
)
from tools.dev_waves.git_state import resolve_repo_identity
from tools.dev_waves.protocol import exchange
from tools.dev_waves.schema import (
    PROTOCOL_VERSION,
    ResourceLimits,
    RunState,
    SubmitRequest,
    parse_response,
)
import tools.dev_waves.daemon as daemon_mod


_TERMINAL = {
    RunState.COMPLETED,
    RunState.BLOCKED,
    RunState.FAILED,
    RunState.INTERRUPTED,
}
_GENEROUS_PER_WAVE = 60
_PROFILE_MAX_PER_WAVE = 60
_PROFILE_MAX_TOTAL = 240
_SERVE_CHILD_RESULT_PREFIX = "T145_SERVE_RESULT="


@dataclass(frozen=True)
class _ServeRepo:
    main: Path
    fake: Path
    fake_digest: str
    runtime: Path


def _profile(check_timeout: int = 60) -> SupervisorProfile:
    checks = (
        CheckSpec("docs", (sys.executable, "tools/check_docs.py"), check_timeout),
        CheckSpec("fixed", (sys.executable, "tools/check_ok.py"), check_timeout),
    )
    return SupervisorProfile(
        "default", "fake-model", "low", checks,
        max_waves=4, max_per_wave_timeout_s=_PROFILE_MAX_PER_WAVE,
        max_total_timeout_s=_PROFILE_MAX_TOTAL,
        max_per_wave_budget_usd=Decimal("1"), max_total_budget_usd=Decimal("3"),
        max_wave_output_bytes=512 * 1024, max_run_bytes=8 * 1024 * 1024,
        allowed_models=("fake-model",),
    )


def _supervisor(
    repo: _ServeRepo,
    *, dependencies: SupervisorDependencies | None = None,
) -> Supervisor:
    return Supervisor(SupervisorConfig(
        str(repo.main), str(repo.fake), repo.fake_digest, _profile(), 15, 0.1,
        runtime_dir=str(repo.runtime), audit_max_bytes=64 * 1024,
    ), dependencies)


def _request(
    repo: _ServeRepo,
    *, waves: int = 1, request_id: str | None = None,
    per_wave_timeout: int = _GENEROUS_PER_WAVE,
    total_timeout: int | None = None,
    per_wave_budget: str = "1", total_budget: str | None = None,
    output_bytes: int = 256 * 1024,
    run_bytes: int = 8 * 1024 * 1024,
) -> SubmitRequest:
    identity = resolve_repo_identity(repo.main)
    return SubmitRequest(
        PROTOCOL_VERSION, "submit", identity.digest, waves, "default",
        request_id or str(uuid.uuid4()),
        ResourceLimits(
            per_wave_timeout, total_timeout or waves * per_wave_timeout,
            Decimal(per_wave_budget), Decimal(total_budget or str(waves)),
            output_bytes, run_bytes,
        ),
    )


def _best_effort_wait_cleanup(supervisor: Supervisor, run_id: str) -> str:
    diagnostics = []
    target_thread = None
    try:
        with supervisor._lock:
            active = supervisor._active
            if active is not None and active.run_id == run_id:
                target_thread = active.thread
    except BaseException as exc:
        diagnostics.append(f"active={type(exc).__name__}: {exc}")
    if target_thread is not None:
        try:
            supervisor.cancel(run_id)
        except BaseException as exc:
            diagnostics.append(f"cancel={type(exc).__name__}: {exc}")
        try:
            target_thread.join(120)
            if target_thread.is_alive():
                diagnostics.append("thread_alive=true")
        except BaseException as exc:
            diagnostics.append(f"join={type(exc).__name__}: {exc}")
    return "; ".join(diagnostics)


def _wait_terminal(supervisor: Supervisor, run_id: str, timeout_s: float = 300.0):
    """Wait for a terminal state and for the run thread to release the run.

    Terminal state precedes quiescence: the run thread still joins its WAL
    writer, rewrites the status file and drops the run's descriptors after
    ``status`` first reports a terminal state.  Tests tear the temporary tree
    down as soon as this helper returns, so returning on the state alone races
    that tail — observed as ``OSError: Directory not empty`` in whichever node
    lost the race (5/48 in the standalone probe, 0/48 once joined).
    """
    try:
        deadline = time.monotonic() + timeout_s
        seen = []
        while time.monotonic() < deadline:
            status = supervisor.status(run_id)
            seen.append(status.state)
            if status.state in _TERMINAL:
                assert supervisor.wait_idle(120), (
                    f"run thread still running after terminal state; states={seen[-10:]}"
                )
                return status, seen
            time.sleep(0.02)
        raise AssertionError(f"run did not terminate; states={seen[-10:]}")
    except BaseException as exc:
        cleanup = _best_effort_wait_cleanup(supervisor, run_id)
        if cleanup:
            exc.args = (*exc.args, f"best-effort cleanup: {cleanup}")
        raise


def _sandbox_permits_short_alias_bind(directory: Path) -> bool:
    """この sandbox が本番と同じ手順の AF_UNIX bind を許すかだけを独立に確かめる。

    capability probe が検査対象の `bind_repo_socket()` 自身を呼ぶと、108 byte 回避
    (`protocol.socket_path_alias`) の退行を「sandbox が許さない」と区別できず、
    SKIPPED + rc=0 の恒真ゲートになる ([T-138])。ここは本番実装を通さず、本番と
    同じ basename と同じ syscall 列 (socket → bind → chmod → stat → listen) を生の
    socket で踏む。名前も syscall も減らさないのは、pathname policy や listen 禁止の
    ような capability 差を本番の退行と誤認しないため — 短縮すると probe が通って
    本番だけ落ちる断面が残る。socket そのものを作れない sandbox も capability 不足で
    あって退行ではないので、例外を漏らさず False にする。

    本番 bind の前に呼ぶ前提で、作った socket file は必ず消す。消せなければ本番が
    `socket-path-exists` で偽赤になるため、その失敗は隠さず送出する。
    """
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        try:
            os.stat(".s", dir_fd=fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise FileExistsError(
                errno.EEXIST, "short alias probe pathname already exists", ".s",
            )
        alias = f"/proc/self/fd/{fd}/.s"
        if not os.path.isdir(f"/proc/self/fd/{fd}") or len(os.fsencode(alias)) >= 108:
            return False
        probe = None
        owned = False
        try:
            try:
                probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            except OSError:
                return False
            try:
                probe.bind(alias)
            except OSError:
                try:
                    os.stat(".s", dir_fd=fd, follow_symlinks=False)
                except FileNotFoundError:
                    return False
                owned = probe.getsockname() == alias
                return False
            owned = True
            try:
                os.chmod(".s", 0o600, dir_fd=fd, follow_symlinks=False)
                os.stat(".s", dir_fd=fd, follow_symlinks=False)
                probe.listen(1)
            except OSError:
                return False
            return True
        finally:
            if probe is not None:
                with contextlib.suppress(OSError):
                    probe.close()
            if owned:
                try:
                    os.unlink(".s", dir_fd=fd)
                except FileNotFoundError:
                    try:
                        os.stat(".s", dir_fd=fd, follow_symlinks=False)
                    except FileNotFoundError:
                        pass
                    else:
                        raise
                else:
                    try:
                        os.stat(".s", dir_fd=fd, follow_symlinks=False)
                    except FileNotFoundError:
                        pass
                    else:
                        raise FileExistsError(
                            errno.EEXIST,
                            "short alias probe cleanup left the pathname present",
                            ".s",
                        )
    finally:
        os.close(fd)


class _ServeObservation(Enum):
    LISTENER_BOUND = "listener-bound"
    REQUEST_READY = "request-ready"
    EXCHANGE_COMPLETED = "exchange-completed"
    PARKED = "parked"
    SHUTDOWN_SET = "shutdown-set"
    RELEASED = "released"
    SERVE_RETURNED = "serve-returned"
    SERVE_RAISED = "serve-raised"


class _ServeHarnessFailure(AssertionError):
    """Deterministic failure raised by the long-path serve harness."""


class _ServePollShapeChanged(_ServeHarnessFailure):
    pass


class _ServePollTimeoutChanged(_ServeHarnessFailure):
    pass


class _ServeLoopIgnoredShutdown(_ServeHarnessFailure):
    pass


class _ServeSelectProxy:
    """Observe only the target serve loop without patching stdlib ``select``."""

    def __init__(self, real_module: object, shutdown: threading.Event) -> None:
        self._real_module = real_module
        self._real_select = real_module.select
        self._shutdown = shutdown
        self._target_thread: threading.Thread | None = None
        self._listener: object | None = None
        self._relay_reader: object | None = None
        self._relay: object | None = None
        self._condition = threading.Condition()
        self._trace: list[_ServeObservation] = []
        self._foreign_calls = 0
        self.exchange_completed = threading.Event()
        self.parked = threading.Event()
        self.released = threading.Event()

    def __getattr__(self, name: str) -> object:
        return getattr(self._real_module, name)

    def bind_target_thread(self, thread: threading.Thread) -> None:
        assert self._target_thread is None
        self._target_thread = thread

    def bind_relay(self, relay: object) -> None:
        if self._relay is not None:
            raise _ServePollShapeChanged(
                "serve created more than one SignalRelay instance",
            )
        fileno = getattr(relay, "fileno", None)
        if not callable(fileno) or type(fileno()) is not int:
            raise _ServePollShapeChanged(
                "serve SignalRelay did not expose one integer fd",
            )
        self._relay = relay

    @property
    def listener(self) -> object | None:
        return self._listener

    @property
    def foreign_calls(self) -> int:
        with self._condition:
            return self._foreign_calls

    @property
    def trace(self) -> list[_ServeObservation]:
        with self._condition:
            return list(self._trace)

    def _observe(self, observation: _ServeObservation) -> None:
        with self._condition:
            if observation not in self._trace:
                self._trace.append(observation)
            self._condition.notify_all()

    def wait_for(
        self, *observations: _ServeObservation,
    ) -> _ServeObservation:
        with self._condition:
            self._condition.wait_for(
                lambda: any(item in self._trace for item in observations),
            )
            return next(item for item in self._trace if item in observations)

    def note_exchange_completed(self) -> None:
        self.exchange_completed.set()
        self._observe(_ServeObservation.EXCHANGE_COMPLETED)

    def note_shutdown_set(self) -> None:
        if not self._shutdown.is_set():
            raise _ServeHarnessFailure("shutdown Event was not set")
        self._observe(_ServeObservation.SHUTDOWN_SET)

    def release(self) -> None:
        self.released.set()
        self._observe(_ServeObservation.RELEASED)

    def note_serve_returned(self) -> None:
        self._observe(_ServeObservation.SERVE_RETURNED)

    def note_serve_raised(self) -> None:
        self._observe(_ServeObservation.SERVE_RAISED)

    def _bind_or_validate_target_shape(
        self, readers: object, writers: object, errors: object,
    ) -> bool:
        if (not isinstance(readers, (list, tuple)) or len(readers) != 2 or
                not isinstance(writers, (list, tuple)) or writers or
                not isinstance(errors, (list, tuple)) or errors):
            raise _ServePollShapeChanged(
                "serve poll readers/writers/errors shape changed",
            )
        listeners = [item for item in readers if isinstance(item, socket.socket)]
        relay_readers = [item for item in readers if type(item) is int]
        if len(listeners) != 1 or len(relay_readers) != 1:
            raise _ServePollShapeChanged(
                "serve poll requires one socket listener and one integer relay fd",
            )
        listener = listeners[0]
        relay_reader = relay_readers[0]
        if self._relay is None:
            raise _ServePollShapeChanged(
                "serve polled before creating its SignalRelay",
            )
        actual_relay_reader = self._relay.fileno()
        if relay_reader != actual_relay_reader:
            raise _ServePollShapeChanged(
                "serve poll relay reader is not the generated SignalRelay fd",
            )
        if self._listener is None:
            self._listener = listener
            self._relay_reader = relay_reader
            return True
        if listener is not self._listener or relay_reader != self._relay_reader:
            raise _ServePollShapeChanged(
                "serve poll listener or relay reader identity changed",
            )
        return False

    @staticmethod
    def _validate_timeout(timeout: object) -> float:
        if isinstance(timeout, bool) or not isinstance(timeout, numbers.Real):
            raise _ServePollTimeoutChanged(
                f"serve poll timeout must be finite and positive: {timeout!r}",
            )
        try:
            numeric = float(timeout)
        except (OverflowError, ValueError):
            raise _ServePollTimeoutChanged(
                f"serve poll timeout must be finite and positive: {timeout!r}",
            ) from None
        if not math.isfinite(numeric) or not 0 < numeric <= 0.25:
            raise _ServePollTimeoutChanged(
                f"serve poll timeout must satisfy 0 < timeout <= 0.25: {timeout!r}",
            )
        return numeric

    def select(
        self, *args: object, **kwargs: object,
    ) -> tuple[list[object], list[object], list[object]]:
        if threading.current_thread() is not self._target_thread:
            with self._condition:
                self._foreign_calls += 1
            return self._real_select(*args, **kwargs)

        if kwargs or len(args) not in (3, 4):
            raise _ServePollShapeChanged(
                "serve poll must use three collections and one positional timeout",
            )
        readers, writers, errors = args[:3]
        listener_was_bound = self._bind_or_validate_target_shape(
            readers, writers, errors,
        )
        timeout = args[3] if len(args) == 4 else None
        timeout = self._validate_timeout(timeout)
        if listener_was_bound:
            self._observe(_ServeObservation.LISTENER_BOUND)
        if self.exchange_completed.is_set():
            if self.parked.is_set():
                raise _ServeLoopIgnoredShutdown(
                    "serve loop selected again after shutdown release",
                )
            self.parked.set()
            self._observe(_ServeObservation.PARKED)
            self.released.wait()
            if not self._shutdown.is_set():
                raise _ServeHarnessFailure(
                    "parked serve poll was released before shutdown Event set",
                )
            return [], [], []

        result = self._real_select(readers, writers, errors, timeout)
        if any(item is self._listener for item in result[0]):
            self._observe(_ServeObservation.REQUEST_READY)
        return result


def _run_long_path_serve_harness(repo: _ServeRepo) -> None:
    supervisor = _supervisor(repo)
    serve_failures: list[BaseException] = []
    real_select_module = daemon_mod.select
    real_select = real_select_module.select
    real_signal_relay = daemon_mod.SignalRelay
    select_proxy = _ServeSelectProxy(
        real_select_module, supervisor._shutdown,
    )

    def _observed_signal_relay(*args: object, **kwargs: object) -> object:
        relay = real_signal_relay(*args, **kwargs)
        select_proxy.bind_relay(relay)
        return relay

    def _serve() -> None:
        # serve_forever の例外を主スレッドへ回収する。thread 内で死なせると
        # テストランナーは warning しか出さず、bind の退行が緑で通る ([T-137])。
        try:
            supervisor.serve_forever()
        except BaseException as exc:
            serve_failures.append(exc)
            select_proxy.note_serve_raised()
        else:
            select_proxy.note_serve_returned()

    thread = threading.Thread(target=_serve, daemon=True)
    select_proxy.bind_target_thread(thread)
    try:
        daemon_mod.select = select_proxy
        daemon_mod.SignalRelay = _observed_signal_relay
        # module binding だけが proxy で、標準 module の属性は不変。
        assert real_select_module.select is real_select
        assert daemon_mod.select is select_proxy
        assert daemon_mod.select.select([], [], [], 0) == ([], [], [])
        assert select_proxy.foreign_calls == 1

        assert thread.daemon is True
        thread.start()
        ready = select_proxy.wait_for(
            _ServeObservation.LISTENER_BOUND,
            _ServeObservation.SERVE_RETURNED,
            _ServeObservation.SERVE_RAISED,
        )
        if ready is not _ServeObservation.LISTENER_BOUND:
            if serve_failures:
                raise serve_failures[0]
            raise _ServeHarnessFailure(
                "serve_forever returned before binding its listener",
            )
        assert select_proxy.listener is not None
        assert (repo.runtime / ".s").exists()

        raw = exchange(repo.runtime, _request(repo), timeout_s=60)
        response = parse_response(raw)
        select_proxy.note_exchange_completed()
        assert response.ok and response.run_id is not None
        status, _seen = _wait_terminal(supervisor, response.run_id)
        assert status.state is RunState.COMPLETED

        parked = select_proxy.wait_for(
            _ServeObservation.PARKED,
            _ServeObservation.SERVE_RETURNED,
            _ServeObservation.SERVE_RAISED,
        )
        if parked is not _ServeObservation.PARKED:
            if serve_failures:
                raise serve_failures[0]
            raise _ServeHarnessFailure(
                "serve_forever returned before the post-exchange park",
            )
        supervisor.shutdown()
        select_proxy.note_shutdown_set()
        select_proxy.release()
        outcome = select_proxy.wait_for(
            _ServeObservation.SERVE_RETURNED,
            _ServeObservation.SERVE_RAISED,
        )
        if outcome is _ServeObservation.SERVE_RAISED:
            raise serve_failures[0]
        assert not serve_failures
        assert select_proxy.trace == [
            _ServeObservation.LISTENER_BOUND,
            _ServeObservation.REQUEST_READY,
            _ServeObservation.EXCHANGE_COMPLETED,
            _ServeObservation.PARKED,
            _ServeObservation.SHUTDOWN_SET,
            _ServeObservation.RELEASED,
            _ServeObservation.SERVE_RETURNED,
        ]
    finally:
        primary_error = sys.exc_info()[1]
        cleanup_error: BaseException | None = None
        if thread.ident is not None:
            try:
                supervisor.shutdown()
                select_proxy.note_shutdown_set()
            except BaseException as exc:
                if cleanup_error is None:
                    cleanup_error = exc
            try:
                select_proxy.release()
            except BaseException as exc:
                if cleanup_error is None:
                    cleanup_error = exc
            try:
                outcome = select_proxy.wait_for(
                    _ServeObservation.SERVE_RETURNED,
                    _ServeObservation.SERVE_RAISED,
                )
                if (outcome is _ServeObservation.SERVE_RAISED and
                        serve_failures and cleanup_error is None):
                    cleanup_error = serve_failures[0]
                thread.join()
            except BaseException as exc:
                if cleanup_error is None:
                    cleanup_error = exc
        daemon_mod.SignalRelay = real_signal_relay
        daemon_mod.select = real_select_module
        if primary_error is None and cleanup_error is not None:
            raise cleanup_error


def _serve_child_payload(
    outcome: str, exc: BaseException | None = None,
) -> dict[str, object]:
    return {
        "outcome": outcome,
        "exception_type": None if exc is None else type(exc).__qualname__,
        "exception_args": [] if exc is None else [repr(item) for item in exc.args],
        "traceback": "" if exc is None else traceback.format_exc(),
    }


def _serve_repo_from_argv() -> _ServeRepo:
    arguments = sys.argv[1:]
    if len(arguments) != 4:
        raise ValueError(
            "serve child requires main, fake, fake digest, and runtime arguments",
        )
    main, fake, fake_digest, runtime = arguments
    if not fake_digest:
        raise ValueError("serve child fake digest must be non-empty")
    return _ServeRepo(Path(main), Path(fake), fake_digest, Path(runtime))


def _serve_child_main() -> int:
    try:
        _run_long_path_serve_harness(_serve_repo_from_argv())
    except BaseException as exc:
        payload = _serve_child_payload("FAIL", exc)
        returncode = 1
    else:
        payload = _serve_child_payload("PASS")
        returncode = 0
    print(
        _SERVE_CHILD_RESULT_PREFIX + json.dumps(payload, sort_keys=True),
        flush=True,
    )
    return returncode
