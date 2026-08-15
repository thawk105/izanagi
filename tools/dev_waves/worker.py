"""Bounded, fake-only child process worker for the dev-wave supervisor."""
from __future__ import annotations

import errno
import ctypes
import hashlib
import math
import os
import re
import resource
import selectors
import signal
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

from .schema import (
    CHILD_ARGV_FORBIDDEN_TOKENS,
    DevWavesError,
    ReasonCode,
    WorkerSpec,
    canonical_bytes,
    canonical_decimal,
    parse_worker_spec,
    validate_child_argv,
)


_HANDSHAKE_PREFIX = "dev-waves-fake/v1 "
_REAL_VERSION_RE = re.compile(r"^(?:Claude Code\s+)?\d+\.\d+(?:\.\d+)?(?:\s|$)", re.I)
_COPY_CHUNK = 64 * 1024
# Group-stop is the only stop ``_preexec`` can produce; ptrace-stop ("t") is not
# ours, so waiting past it into the bounded failure is the safe direction.
_CHILD_STOPPED_STATE = "T"
_CHILD_EXITED_STATES = frozenset({"Z", "X", "x"})
_STOP_HANDSHAKE_TIMEOUT_S = 5.0
_STOP_HANDSHAKE_POLL_S = 0.0002


@dataclass(frozen=True)
class PidIdentity:
    pid: int
    boot_id: str
    start_ticks: int


@dataclass(frozen=True)
class WorkerHandle:
    process: subprocess.Popen[bytes]
    identity: PidIdentity
    pgid: int


@dataclass(frozen=True)
class WorkerExit:
    child: Optional[PidIdentity]
    return_code: Optional[int]
    reason: Optional[ReasonCode]
    timed_out: bool
    log_limit_exceeded: bool
    process_group_residual: bool
    stdout_bytes: int
    stderr_bytes: int
    started_boottime_ns: int
    finished_boottime_ns: int


CrashHook = Callable[[str], None]


def pid_identity_record(identity: PidIdentity) -> dict[str, object]:
    """Return the closed typed identity record used by WAL observations."""
    if not isinstance(identity, PidIdentity):
        raise TypeError("identity must be PidIdentity")
    if identity.pid < 1 or identity.start_ticks < 1 or not identity.boot_id:
        raise ValueError("invalid process identity")
    return {
        "pid": identity.pid,
        "boot_id": identity.boot_id,
        "start_ticks": identity.start_ticks,
    }


def pid_identity_digest(identity: PidIdentity) -> str:
    return hashlib.sha256(canonical_bytes(pid_identity_record(identity))).hexdigest()


def _boottime_ns() -> int:
    return time.clock_gettime_ns(time.CLOCK_BOOTTIME)


def _read_boot_id() -> str:
    value = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    if not value or "\x00" in value:
        raise OSError("invalid boot identity")
    return value


def _proc_stat(pid: int) -> tuple[str, int, int]:
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    end = raw.rfind(")")
    if end < 1:
        raise OSError("invalid proc stat")
    fields = raw[end + 2:].split()
    # fields[0] is field 3 (state), fields[2] field 5 (pgrp), fields[19] field 22.
    if len(fields) <= 19:
        raise OSError("short proc stat")
    return fields[0], int(fields[2]), int(fields[19])


def read_pid_identity(pid: int) -> PidIdentity:
    """Read the Linux boot/start tuple used before every signal operation."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        raise ValueError("pid must be a positive integer")
    _state, _pgid, start_ticks = _proc_stat(pid)
    return PidIdentity(pid=pid, boot_id=_read_boot_id(), start_ticks=start_ticks)


def _verified_state(identity: PidIdentity) -> Optional[str]:
    """Return the process state, but only while the recorded identity verifies.

    State and identity come from one ``/proc/<pid>/stat`` read so a PID reused
    between the two can never present another process's state as our child's.
    """
    try:
        state, pgid, start_ticks = _proc_stat(identity.pid)
        boot_id = _read_boot_id()
    except (OSError, ValueError):
        return None
    if start_ticks != identity.start_ticks or boot_id != identity.boot_id:
        return None
    if pgid != identity.pid:
        return None
    return state


def _identity_matches(identity: PidIdentity) -> bool:
    return _verified_state(identity) is not None


def _group_members(pgid: int) -> tuple[tuple[int, int], ...]:
    members = []
    try:
        entries = os.scandir("/proc")
    except OSError:
        return ()
    with entries:
        for entry in entries:
            if not entry.name.isdigit():
                continue
            pid = int(entry.name)
            try:
                _state, process_group, start_ticks = _proc_stat(pid)
            except (OSError, ValueError):
                continue
            if process_group == pgid:
                members.append((pid, start_ticks))
    return tuple(sorted(members))


def _verified_group_exists(identity: PidIdentity) -> bool:
    try:
        current_boot = _read_boot_id()
    except OSError:
        return False
    if current_boot != identity.boot_id:
        return False
    if _identity_matches(identity):
        return True
    members = _group_members(identity.pid)
    # After leader exit, only signal a still-live group whose members cannot
    # predate the recorded leader. This avoids signalling a reused PGID.
    return bool(members) and all(start >= identity.start_ticks for _pid, start in members)


def terminate_verified_group(identity: PidIdentity, grace_s: float) -> bool:
    """TERM then KILL a process group only while its recorded identity verifies."""
    if not isinstance(identity, PidIdentity):
        raise TypeError("identity must be PidIdentity")
    if grace_s < 0:
        raise ValueError("grace_s must be non-negative")
    if not _verified_group_exists(identity):
        return False
    try:
        os.killpg(identity.pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    deadline = _boottime_ns() + int(grace_s * 1_000_000_000)
    while _boottime_ns() < deadline:
        if not _group_members(identity.pid):
            return True
        time.sleep(min(0.01, grace_s or 0.001))
    if not _verified_group_exists(identity):
        return False
    try:
        os.killpg(identity.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    return True


def kill_spawned_process(process: subprocess.Popen[bytes]) -> None:
    """Kill and reap the exact process returned by our successful ``Popen``.

    This is the ownership fallback used before a durable PID identity exists;
    it deliberately targets only the handle's exact PID, never an unverified
    process group.
    """
    if not isinstance(process, subprocess.Popen):
        raise TypeError("process must be Popen")
    if process.poll() is None:
        try:
            process.kill()
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.kill(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def build_child_argv(spec: WorkerSpec) -> tuple[str, ...]:
    """Build the sole accepted fake-child grammar from schema-owned constants."""
    if not isinstance(spec, WorkerSpec):
        raise TypeError("spec must be WorkerSpec")
    argv = (
        "-p",
        f"--model={spec.model}",
        f"--effort={spec.effort}",
        "--permission-mode=auto",
        "--output-format=json",
        f"--json-schema={spec.receipt_schema_json}",
        f"--max-budget-usd={canonical_decimal(spec.per_wave_budget_usd)}",
        f"--add-dir={spec.main_worktree}",
        f"/dev-wave --supervised-manifest {spec.wave_manifest_path}",
    )
    validate_child_argv(argv)
    if any(token in CHILD_ARGV_FORBIDDEN_TOKENS for token in argv):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {
            "label": "child-argv", "kind": "forbidden",
        })
    return argv


def _safe_environment(spec: WorkerSpec) -> dict[str, str]:
    environment = dict(spec.environment)
    if "CLAUDECODE" in environment or any(key.startswith("GIT_") and key not in {
        "GIT_CONFIG_GLOBAL", "GIT_TERMINAL_PROMPT", "GIT_TRACE2_EVENT",
    } for key in environment):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {
            "label": "environment", "kind": "forbidden",
        })
    return environment


def _open_verified_executable(spec: WorkerSpec) -> int:
    flags = getattr(os, "O_PATH", os.O_RDONLY)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(spec.executable_path, flags)
    except OSError:
        raise DevWavesError(ReasonCode.CLAUDE_UNAVAILABLE, {
            "label": "executable", "kind": "open-failed",
        }) from None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o111:
            raise OSError("not executable regular file")
        digest_fd = os.open(f"/proc/self/fd/{fd}", os.O_RDONLY)
        try:
            hasher = hashlib.sha256()
            while True:
                chunk = os.read(digest_fd, _COPY_CHUNK)
                if not chunk:
                    break
                hasher.update(chunk)
            digest = hasher.hexdigest()
        finally:
            os.close(digest_fd)
        if digest != spec.executable_sha256:
            raise DevWavesError(ReasonCode.CLAUDE_UNAVAILABLE, {
                "label": "executable", "kind": "digest-mismatch",
            })
        return fd
    except Exception:
        os.close(fd)
        raise


def _handshake(spec: WorkerSpec, executable_fd: int) -> None:
    nonce = os.urandom(24).hex()
    command = [f"/proc/self/fd/{executable_fd}", "--dev-waves-fake-handshake", nonce]
    def handshake_limit() -> None:
        resource.setrlimit(resource.RLIMIT_FSIZE, (4096, 4096))
    try:
        with tempfile.TemporaryFile() as output:
            result = subprocess.run(
                command, shell=False, stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.DEVNULL, cwd=spec.cwd,
                env=_safe_environment(spec), pass_fds=(executable_fd,),
                preexec_fn=handshake_limit,
                timeout=min(5, spec.per_wave_timeout_s), check=False,
            )
            output.seek(0)
            raw = output.read(4097)
    except (OSError, subprocess.TimeoutExpired):
        raise DevWavesError(ReasonCode.FAKE_HANDSHAKE_FAILED, {
            "label": "fake-handshake", "kind": "execution",
        }) from None
    if len(raw) > 4096:
        raise DevWavesError(ReasonCode.FAKE_HANDSHAKE_FAILED, {
            "label": "fake-handshake", "kind": "oversize",
        })
    stdout = raw.decode("utf-8", errors="replace").strip()
    expected = _HANDSHAKE_PREFIX + nonce
    if (result.returncode != 0 or stdout != expected or
            _REAL_VERSION_RE.match(stdout) is not None):
        raise DevWavesError(ReasonCode.FAKE_HANDSHAKE_FAILED, {
            "label": "fake-handshake", "kind": "response",
        })


def _create_private(path: str) -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return os.open(path, flags, 0o600)


def _write_all(fd: int, raw: bytes) -> None:
    view = memoryview(raw)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("short write")
        view = view[written:]


def _fsync_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _persist_create_only(path: str, value: object) -> None:
    fd = _create_private(path)
    try:
        _write_all(fd, canonical_bytes(value) + b"\n")
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_parent(path)


def _preexec(executable_fd: int, file_limit: int, parent_pid: int) -> Callable[[], None]:
    def prepare() -> None:
        signal.signal(signal.SIGHUP, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0:  # PR_SET_PDEATHSIG
            error = ctypes.get_errno()
            raise OSError(error, "PR_SET_PDEATHSIG failed")
        if os.getppid() != parent_pid:
            os._exit(127)
        os.setpgid(0, 0)
        resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))
        # Popen normally waits for its exec-error pipe. Closing every descriptor
        # except the verified executable makes Popen return while this process is
        # stopped before exec. stdout/stderr have already been dup2'd to 1/2.
        if executable_fd > 3:
            os.closerange(3, executable_fd)
        upper = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        if upper == resource.RLIM_INFINITY:
            upper = 1 << 20
        os.closerange(executable_fd + 1, min(int(upper), 1 << 20))
        os.kill(os.getpid(), signal.SIGSTOP)
    return prepare


def _spawn_stopped(spec: WorkerSpec, executable_fd: int) -> subprocess.Popen[bytes]:
    argv = build_child_argv(spec)
    parent_pid = os.getpid()
    return subprocess.Popen(
        [f"/proc/self/fd/{executable_fd}", *argv],
        shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, cwd=spec.cwd, env=_safe_environment(spec),
        close_fds=True, pass_fds=(executable_fd,), start_new_session=False,
        preexec_fn=_preexec(executable_fd, spec.max_run_bytes, parent_pid),
    )


def _await_stopped_child(
    identity: PidIdentity, timeout_s: float = _STOP_HANDSHAKE_TIMEOUT_S,
) -> str:
    """Return the child's state once it is observed stopped, or fail closed.

    ``Popen`` returns as soon as the child closes the exec-error pipe, which
    ``_preexec`` does *before* stopping itself, so the parent can reach this
    point while the child is still running towards its own ``SIGSTOP``.  A
    ``SIGCONT`` delivered inside that window is discarded -- the kernel has no
    stop to undo -- and the child then stays stopped until the wave deadline
    kills it with no output at all.  Every resume therefore waits for an
    observed stop first.
    """
    deadline = _boottime_ns() + int(timeout_s * 1_000_000_000)
    while True:
        state = _verified_state(identity)
        if state is None:
            raise DevWavesError(ReasonCode.AMBIGUOUS_RECOVERY, {
                "label": "child", "kind": "identity-mismatch-before-cont",
            })
        if state == _CHILD_STOPPED_STATE or state in _CHILD_EXITED_STATES:
            return state
        if _boottime_ns() >= deadline:
            raise DevWavesError(ReasonCode.AMBIGUOUS_RECOVERY, {
                "label": "child", "kind": "stop-handshake-timeout",
            })
        time.sleep(_STOP_HANDSHAKE_POLL_S)


def _signal_cont_verified(identity: PidIdentity) -> None:
    if _await_stopped_child(identity) in _CHILD_EXITED_STATES:
        # Died before the handshake; the exit path below reports it verbatim.
        return
    os.kill(identity.pid, signal.SIGCONT)


def _copy_capped(
    process: subprocess.Popen[bytes], stdout_fd: int, stderr_fd: int,
    *, cap: int, deadline_ns: int, identity: PidIdentity, grace_s: float,
) -> tuple[int, int, bool, bool]:
    selector = selectors.DefaultSelector()
    counts = {"stdout": 0, "stderr": 0}
    streams = (("stdout", process.stdout, stdout_fd), ("stderr", process.stderr, stderr_fd))
    for name, stream, target in streams:
        assert stream is not None
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ, (name, target))
    total = 0
    timed_out = False
    limited = False
    signalled = False
    while selector.get_map() or process.poll() is None:
        now = _boottime_ns()
        if not signalled and now >= deadline_ns:
            timed_out = True
            if not terminate_verified_group(identity, grace_s):
                raise DevWavesError(ReasonCode.AMBIGUOUS_RECOVERY, {
                    "label": "child", "kind": "timeout-identity-mismatch",
                })
            signalled = True
        wait_s = 0.05 if signalled else max(0.0, min(0.05, (deadline_ns - now) / 1e9))
        events = selector.select(wait_s) if selector.get_map() else ()
        if not selector.get_map() and process.poll() is None:
            time.sleep(wait_s)
        for key, _mask in events:
            name, target = key.data
            try:
                chunk = os.read(key.fileobj.fileno(), _COPY_CHUNK)
            except BlockingIOError:
                continue
            if not chunk:
                selector.unregister(key.fileobj)
                key.fileobj.close()
                continue
            room = max(0, cap - total)
            if len(chunk) > room:
                limited = True
                chunk = chunk[:room]
            if chunk:
                _write_all(target, chunk)
                counts[name] += len(chunk)
                total += len(chunk)
            if limited and not signalled:
                if not terminate_verified_group(identity, grace_s):
                    raise DevWavesError(ReasonCode.AMBIGUOUS_RECOVERY, {
                        "label": "child", "kind": "log-limit-identity-mismatch",
                    })
                signalled = True
        if process.poll() is not None and not selector.get_map():
            break
    return counts["stdout"], counts["stderr"], timed_out, limited


def _worker_exit_wire(exit_record: WorkerExit) -> dict[str, object]:
    value = asdict(exit_record)
    value["reason"] = exit_record.reason.value if exit_record.reason else None
    return value


def run_worker(
    spec: WorkerSpec,
    *,
    termination_grace_s: float = 1.0,
    crash_hook: Optional[CrashHook] = None,
) -> WorkerExit:
    """Run one fake child and durably record its identity and bounded exit."""
    if not isinstance(spec, WorkerSpec):
        raise TypeError("spec must be WorkerSpec")
    if crash_hook:
        crash_hook("before-spawn")
    started = _boottime_ns()
    executable_fd = _open_verified_executable(spec)
    stdout_fd = stderr_fd = -1
    process: Optional[subprocess.Popen[bytes]] = None
    identity: Optional[PidIdentity] = None
    try:
        try:
            _handshake(spec, executable_fd)
        except DevWavesError as exc:
            if exc.code is ReasonCode.FAKE_HANDSHAKE_FAILED:
                failure = WorkerExit(
                    None, None, exc.code, False, False, False, 0, 0,
                    started, _boottime_ns(),
                )
                _persist_create_only(spec.worker_exit_path, _worker_exit_wire(failure))
            raise
        stdout_fd = _create_private(spec.stdout_path)
        stderr_fd = _create_private(spec.stderr_path)
        process = _spawn_stopped(spec, executable_fd)
        if crash_hook:
            crash_hook("after-spawn")
        identity = read_pid_identity(process.pid)
        if crash_hook:
            crash_hook("before-identity-fsync")
        _persist_create_only(spec.child_start_path, {
            "pid": identity.pid, "boot_id": identity.boot_id,
            "start_ticks": identity.start_ticks, "pgid": identity.pid,
        })
        if crash_hook:
            crash_hook("after-identity-fsync")
        _signal_cont_verified(identity)
        deadline = started + spec.per_wave_timeout_s * 1_000_000_000
        out_count, err_count, timed_out, limited = _copy_capped(
            process, stdout_fd, stderr_fd, cap=spec.max_wave_output_bytes,
            deadline_ns=deadline, identity=identity, grace_s=termination_grace_s,
        )
        return_code = process.wait()
        residual = bool(_group_members(identity.pid))
        if residual:
            terminate_verified_group(identity, termination_grace_s)
        if timed_out:
            reason = ReasonCode.TIMEOUT
        elif limited:
            reason = ReasonCode.LOG_LIMIT
        elif residual:
            reason = ReasonCode.NONZERO_EXIT
        elif return_code != 0:
            reason = ReasonCode.NONZERO_EXIT
        else:
            reason = None
        exit_record = WorkerExit(
            identity, return_code, reason, timed_out, limited, residual,
            out_count, err_count, started, _boottime_ns(),
        )
        for fd in (stdout_fd, stderr_fd):
            os.fsync(fd)
        _fsync_parent(spec.stdout_path)
        _persist_create_only(spec.worker_exit_path, _worker_exit_wire(exit_record))
        return exit_record
    except BaseException:
        if identity is not None:
            terminate_verified_group(identity, termination_grace_s)
        elif process is not None:
            kill_spawned_process(process)
        raise
    finally:
        for fd in (stdout_fd, stderr_fd, executable_fd):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError as exc:
                    if exc.errno != errno.EBADF:
                        raise


def load_worker_spec(path: os.PathLike[str] | str) -> WorkerSpec:
    raw = Path(path).read_bytes()
    return parse_worker_spec(raw)


def spawn_worker(
    spec_path: os.PathLike[str] | str,
    *,
    termination_grace_s: float,
) -> subprocess.Popen[bytes]:
    """Spawn the worker process itself with the required noninteractive flags."""
    path = os.path.abspath(os.fspath(spec_path))
    spec = load_worker_spec(path)
    if (isinstance(termination_grace_s, bool) or
            not isinstance(termination_grace_s, (int, float)) or
            not math.isfinite(termination_grace_s) or termination_grace_s < 0):
        raise ValueError("termination_grace_s must be finite and non-negative")
    repo_root = str(Path(__file__).resolve().parents[2])
    environment = {
        key: os.environ[key] for key in ("LANG", "LC_ALL", "PATH", "TZ") if key in os.environ
    }
    environment["PYTHONPATH"] = repo_root
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    parent_pid = os.getpid()

    def prepare_wrapper() -> None:
        signal.signal(signal.SIGHUP, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "worker PR_SET_PDEATHSIG failed")
        if os.getppid() != parent_pid:
            os._exit(127)

    return subprocess.Popen(
        [
            sys.executable, "-m", "tools.dev_waves.worker", path,
            format(float(termination_grace_s), ".17g"),
        ],
        shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, cwd=spec.cwd, env=environment,
        start_new_session=True, close_fds=True,
        preexec_fn=prepare_wrapper,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        return 2
    try:
        grace = float(args[1])
        if not math.isfinite(grace) or grace < 0:
            return 2
        result = run_worker(load_worker_spec(args[0]), termination_grace_s=grace)
    except DevWavesError:
        return 2
    except (OSError, ValueError):
        return 2
    return 0 if result.reason is None else 1


if __name__ == "__main__":
    sys.exit(main())


__all__ = [
    "PidIdentity", "WorkerExit", "WorkerHandle", "WorkerSpec", "build_child_argv",
    "kill_spawned_process", "load_worker_spec", "main", "pid_identity_digest", "pid_identity_record",
    "read_pid_identity", "run_worker",
    "spawn_worker", "terminate_verified_group",
]
