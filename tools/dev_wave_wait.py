#!/usr/bin/env python3
"""dev-wave の producer と acceptance lease を安全に待つ。"""
from __future__ import annotations

import argparse
import errno
import json
import math
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Sequence


RC_OK = 0
RC_USAGE = 2
RC_FAIL_CLOSED = 70
RC_CLEANUP_FAILED = 74
RC_INTERRUPTED = 130

_PROGRAM = "dev-wave-wait"
_LEASE_ENV = "IZANAGI_WAVE_LEASE_DIR"
_PRODUCER_POLL_SECONDS = 5
_PRODUCER_GRACE_SECONDS = 30
_DEFAULT_ACCEPTANCE_POLL_SECONDS = 30
_MIN_ACCEPTANCE_POLL_SECONDS = 30
_MAX_ACCEPTANCE_POLL_SECONDS = 120
_DEFAULT_ACCEPTANCE_MAX_WAIT_SECONDS = 7200
_STAGE_TIMEOUT_SECONDS = 300
_STAGE_TERMINATION_SECONDS = 5
_LEASE_TTL_SECONDS = 2400
_GIT_ENV_KEYS = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
    }
)
_HANDLED_SIGNALS = (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)
_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
_HOLDER_RE = re.compile(r"[0-9a-f]{12}\Z")
_CLAIM_STATES = frozenset(
    {"acquired", "held-self", "held", "queued", "stale-held", "unavailable"}
)
_ACCEPTED_CLAIM_STATES = frozenset({"acquired", "held-self"})
_POLLING_CLAIM_STATES = frozenset({"held", "queued"})
_RELEASED_STATES = frozenset({"released", "free", "not-owner"})


@dataclass(frozen=True)
class _CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class _Outcome:
    rc: int
    stage: str | None = None
    source_rc: int | None = None


class _PidState(Enum):
    ALIVE = "alive"
    DEAD = "dead"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class _Effects:
    run: Callable[[Sequence[str], Path, bool], _CommandResult]
    run_unbounded: Callable[[Sequence[str], Path, bool], _CommandResult]
    sleep: Callable[[float], None]
    kill: Callable[[int, int], None]
    is_file: Callable[[Path], bool]
    read_text: Callable[[Path], str]
    getenv: Callable[[str], str | None]
    monotonic: Callable[[], float]
    write_temp: Callable[[bytes], Path]
    unlink: Callable[[Path], None]


class _LeaseOwnership(Enum):
    # HELD_SELF は merge abort 権限だけを持ち、lease release 権限は持たない。
    NONE = "none"
    UNKNOWN = "unknown"
    ACQUIRED = "acquired"
    HELD_SELF = "held-self"
    RETAINED = "retained"


@dataclass
class _AcceptanceLifecycle:
    ownership: _LeaseOwnership = _LeaseOwnership.NONE
    acquired_at: float | None = None
    merge_pending: bool = False
    cleanup_failure: _Outcome | None = None


class _StageFailure(Exception):
    def __init__(self, stage: str, rc: int = RC_FAIL_CLOSED, source_rc: int | None = None):
        super().__init__(stage)
        self.outcome = _Outcome(rc, stage, source_rc)


class _SignalReceived(BaseException):
    def __init__(self, signum: int):
        super().__init__(signum)
        self.signum = signum


def _run_subprocess(
    argv: Sequence[str], cwd: Path, capture: bool, *, stage_policy: bool
) -> _CommandResult:
    values = list(argv)
    kwargs: dict[str, object] = {
        "cwd": cwd,
        "text": True,
        "shell": False,
    }
    bounded_stage = False
    if values and values[0] == "git":
        kwargs["env"] = {
            key: value for key, value in os.environ.items() if key not in _GIT_ENV_KEYS
        }
        bounded_stage = stage_policy
    elif (
        stage_policy
        and len(values) >= 2
        and Path(values[1]).name == "wave_land_window.py"
    ):
        bounded_stage = True
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    if not bounded_stage:
        result = subprocess.run(values, check=False, **kwargs)
        return _CommandResult(
            result.returncode,
            result.stdout if capture else "",
            result.stderr if capture else "",
        )

    # Stage subprocess だけを専用 group に閉じる。受入 command は無制限のまま。
    process = subprocess.Popen(values, start_new_session=True, **kwargs)
    try:
        stdout, stderr = process.communicate(timeout=_STAGE_TIMEOUT_SECONDS)
    except BaseException:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.communicate(timeout=_STAGE_TERMINATION_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.wait(timeout=_STAGE_TERMINATION_SECONDS)
            except subprocess.TimeoutExpired:
                pass
        raise
    return _CommandResult(
        process.returncode,
        stdout if capture else "",
        stderr if capture else "",
    )


def _default_run(argv: Sequence[str], cwd: Path, capture: bool) -> _CommandResult:
    return _run_subprocess(argv, cwd, capture, stage_policy=True)


def _default_run_unbounded(
    argv: Sequence[str], cwd: Path, capture: bool
) -> _CommandResult:
    return _run_subprocess(argv, cwd, capture, stage_policy=False)


def _default_read_text(path: Path) -> str:
    # newline translation を無効にし、検査した UTF-8 bytes を一時 file へ再現する。
    with path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()


def _default_write_temp(content: bytes) -> Path:
    fd, raw_path = tempfile.mkstemp(prefix="dev-wave-wait-message-", suffix=".txt")
    path = Path(raw_path)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def _default_effects() -> _Effects:
    return _Effects(
        run=_default_run,
        run_unbounded=_default_run_unbounded,
        sleep=time.sleep,
        kill=os.kill,
        is_file=Path.is_file,
        read_text=_default_read_text,
        getenv=os.environ.get,
        monotonic=time.monotonic,
        write_temp=_default_write_temp,
        unlink=lambda path: path.unlink(missing_ok=True),
    )


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise _StageFailure("cli-usage", RC_USAGE)


def _positive_int(value: str) -> int:
    try:
        parsed = int(value, 10)
    except ValueError:
        raise argparse.ArgumentTypeError("positive integer required") from None
    if parsed <= 0:
        raise argparse.ArgumentTypeError("positive integer required")
    return parsed


def _poll_seconds(value: str) -> int:
    parsed = _positive_int(value)
    if not _MIN_ACCEPTANCE_POLL_SECONDS <= parsed <= _MAX_ACCEPTANCE_POLL_SECONDS:
        raise argparse.ArgumentTypeError("poll outside policy range")
    return parsed


def _producer_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog=f"{_PROGRAM} producer", add_help=True)
    parser.add_argument("--done-file", type=Path, required=True)
    parser.add_argument("--artifact-file", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pid")
    source.add_argument("--pid-file", type=Path)
    parser.add_argument("--max-wait-seconds", type=_positive_int)
    return parser


def _acceptance_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog=f"{_PROGRAM} acceptance", add_help=True)
    parser.add_argument("--wave", required=True)
    parser.add_argument("--lease-dir", type=Path)
    parser.add_argument("--merge-message-file", type=Path)
    parser.add_argument("--owned-path", type=Path, action="append", default=[])
    parser.add_argument(
        "--poll-seconds",
        type=_poll_seconds,
        default=_DEFAULT_ACCEPTANCE_POLL_SECONDS,
    )
    parser.add_argument(
        "--max-wait-seconds",
        type=_positive_int,
        default=_DEFAULT_ACCEPTANCE_MAX_WAIT_SECONDS,
    )
    return parser


def _parse_cli(argv: Sequence[str]) -> tuple[str, argparse.Namespace, list[str]]:
    values = list(argv)
    if not values:
        raise _StageFailure("cli-usage", RC_USAGE)
    command = values[0]
    if command == "producer":
        args = _producer_parser().parse_args(values[1:])
        return command, args, []
    if command != "acceptance":
        raise _StageFailure("cli-usage", RC_USAGE)
    try:
        delimiter = values.index("--", 1)
    except ValueError:
        raise _StageFailure("cli-usage", RC_USAGE) from None
    command_argv = values[delimiter + 1 :]
    if not command_argv:
        raise _StageFailure("cli-usage", RC_USAGE)
    args = _acceptance_parser().parse_args(values[1:delimiter])
    return command, args, command_argv


def _parse_pid(value: str) -> int:
    if not value.isascii() or not value.isdecimal():
        raise _StageFailure("pid-input", RC_USAGE)
    pid = int(value, 10)
    if pid <= 0:
        raise _StageFailure("pid-input", RC_USAGE)
    return pid


def _resolve_pid(
    direct: str | None,
    pid_file: Path | None,
    effects: _Effects,
) -> int:
    if (direct is None) == (pid_file is None):
        raise _StageFailure("pid-input", RC_USAGE)
    if direct is not None:
        return _parse_pid(direct)
    assert pid_file is not None
    try:
        raw = effects.read_text(pid_file)
    except (OSError, UnicodeError):
        raise _StageFailure("pid-file", RC_USAGE) from None
    return _parse_pid(raw.strip())


def _parse_process_identity(value: str, pid: int) -> tuple[str, int]:
    prefix = f"{pid} ("
    if not value.startswith(prefix):
        raise ValueError("pid mismatch")
    close = value.rfind(")")
    if close < len(prefix):
        raise ValueError("malformed stat")
    remaining = value[close + 1 :].split()
    if (
        len(remaining) <= 19
        or len(remaining[0]) != 1
        or not remaining[19].isascii()
        or not remaining[19].isdecimal()
    ):
        raise ValueError("missing starttime")
    return remaining[0], int(remaining[19], 10)


def _parse_start_time(value: str, pid: int) -> int:
    return _parse_process_identity(value, pid)[1]


def _read_start_time(pid: int, effects: _Effects) -> int:
    return _parse_start_time(effects.read_text(Path(f"/proc/{pid}/stat")), pid)


def _read_process_identity(pid: int, effects: _Effects) -> tuple[str, int]:
    return _parse_process_identity(
        effects.read_text(Path(f"/proc/{pid}/stat")), pid
    )


def _initial_start_time(pid: int, effects: _Effects) -> int | None:
    try:
        return _read_start_time(pid, effects)
    except (OSError, UnicodeError, ValueError):
        print(
            f"producer: /proc/{pid}/stat を読めないため pid-only へ縮退します",
            file=sys.stderr,
        )
        return None


def _pid_state(pid: int, start_time: int | None, effects: _Effects) -> _PidState:
    try:
        effects.kill(pid, 0)
    except ProcessLookupError:
        return _PidState.DEAD
    except PermissionError:
        return _PidState.UNKNOWN
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return _PidState.DEAD
        return _PidState.UNKNOWN
    if start_time is None:
        return _PidState.ALIVE
    try:
        process_state, current = _read_process_identity(pid, effects)
    except (OSError, UnicodeError, ValueError):
        return _PidState.UNKNOWN
    if process_state == "Z":
        return _PidState.DEAD
    return _PidState.ALIVE if current == start_time else _PidState.DEAD


def wait_for_producer(
    *,
    done_file: Path,
    artifact_file: Path,
    pid: int,
    max_wait_seconds: int | None,
    effects: _Effects,
) -> _Outcome:
    started = effects.monotonic()
    start_time = _initial_start_time(pid, effects)
    while True:
        state = _pid_state(pid, start_time, effects)
        if state is _PidState.UNKNOWN:
            return _Outcome(RC_FAIL_CLOSED, "producer-liveness")
        if state is _PidState.DEAD:
            break
        if max_wait_seconds is not None:
            try:
                elapsed = effects.monotonic() - started
            except Exception:
                return _Outcome(RC_FAIL_CLOSED, "producer-clock")
            if elapsed + _PRODUCER_POLL_SECONDS > max_wait_seconds:
                return _Outcome(RC_FAIL_CLOSED, "producer-timeout")
        effects.sleep(_PRODUCER_POLL_SECONDS)

    grace_elapsed = 0
    while True:
        if effects.is_file(done_file) and effects.is_file(artifact_file):
            return _Outcome(RC_OK)
        if grace_elapsed >= _PRODUCER_GRACE_SECONDS:
            return _Outcome(RC_FAIL_CLOSED, "producer-files")
        effects.sleep(_PRODUCER_POLL_SECONDS)
        grace_elapsed += _PRODUCER_POLL_SECONDS


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _parse_json_object(value: str, *, stage: str) -> dict[str, object]:
    try:
        parsed = json.loads(value, object_pairs_hook=_no_duplicate_keys)
    except (json.JSONDecodeError, UnicodeError, ValueError, RecursionError):
        raise _StageFailure(stage) from None
    if not isinstance(parsed, dict):
        raise _StageFailure(stage)
    return parsed


def _run_capture(
    effects: _Effects,
    argv: Sequence[str],
    repo: Path,
    stage: str,
) -> _CommandResult:
    try:
        result = effects.run(tuple(argv), repo, True)
    except (OSError, UnicodeError, subprocess.SubprocessError):
        raise _StageFailure(stage) from None
    if result.returncode != 0:
        raise _StageFailure(stage, source_rc=result.returncode)
    return result


def _main_sha(effects: _Effects, repo: Path, stage: str) -> str:
    result = _run_capture(effects, ("git", "rev-parse", "main"), repo, stage)
    value = result.stdout.strip()
    if _SHA_RE.fullmatch(value) is None:
        raise _StageFailure(stage)
    return value


def _head_sha(effects: _Effects, repo: Path, stage: str) -> str:
    result = _run_capture(effects, ("git", "rev-parse", "HEAD"), repo, stage)
    value = result.stdout.strip()
    if _SHA_RE.fullmatch(value) is None:
        raise _StageFailure(stage)
    return value


def _behind_count(effects: _Effects, repo: Path, stage: str) -> int:
    result = _run_capture(
        effects,
        ("git", "rev-list", "--count", "HEAD..main"),
        repo,
        stage,
    )
    value = result.stdout.strip()
    if not value.isascii() or not value.isdecimal():
        raise _StageFailure(stage)
    return int(value, 10)


def _normalized_repo_path_parts(value: str | Path, repo: Path) -> tuple[str, ...]:
    path = Path(os.path.normpath(os.fspath(value)))
    if path.is_absolute():
        normalized_repo = Path(os.path.normpath(os.fspath(repo)))
        try:
            path = path.relative_to(normalized_repo)
        except ValueError:
            pass
    return path.parts


def _owned_path_overlap(
    effects: _Effects,
    repo: Path,
    owned_paths: Sequence[Path],
) -> bool:
    result = _run_capture(
        effects,
        ("git", "diff", "--name-only", "HEAD...main"),
        repo,
        "owned-path-diff",
    )
    owned_parts = [
        _normalized_repo_path_parts(path, repo) for path in owned_paths
    ]
    for changed_path in result.stdout.splitlines():
        if not changed_path:
            continue
        changed_parts = _normalized_repo_path_parts(changed_path, repo)
        if any(
            changed_parts == owned
            or changed_parts[: len(owned)] == owned
            for owned in owned_parts
        ):
            return True
    return False


def _identity_preflight(effects: _Effects, repo: Path, wave: str) -> None:
    def preflight_run(argv: Sequence[str], stage: str) -> _CommandResult:
        try:
            return _run_capture(effects, argv, repo, stage)
        except _StageFailure as exc:
            raise _StageFailure(stage, RC_USAGE, exc.outcome.source_rc) from None

    inside = preflight_run(
        ("git", "rev-parse", "--is-inside-work-tree"), "preflight-worktree"
    )
    if inside.stdout.strip() != "true":
        raise _StageFailure("preflight-worktree", RC_USAGE)
    top_level = preflight_run(
        ("git", "rev-parse", "--show-toplevel"), "preflight-toplevel"
    ).stdout.strip()
    try:
        if not top_level or Path(top_level).resolve() != repo.resolve():
            raise _StageFailure("preflight-toplevel", RC_USAGE)
    except OSError:
        raise _StageFailure("preflight-toplevel", RC_USAGE) from None
    branch = preflight_run(
        ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
        "preflight-branch",
    ).stdout.strip()
    if not wave or not branch or not branch.endswith(wave):
        raise _StageFailure("preflight-branch", RC_USAGE)
    status = preflight_run(
        ("git", "status", "--porcelain", "--untracked-files=no"),
        "preflight-clean",
    )
    if status.stdout:
        raise _StageFailure("preflight-clean", RC_USAGE)


def _lease_command(
    repo: Path,
    action: str,
    lease_dir: Path,
    wave: str,
    main_sha: str | None = None,
) -> tuple[str, ...]:
    argv = [
        sys.executable,
        str(repo / "tools" / "wave_land_window.py"),
        action,
        "--lease-dir",
        str(lease_dir),
        "--wave",
        wave,
    ]
    if main_sha is not None:
        argv.extend(("--main-sha", main_sha))
    return tuple(argv)


def _claim_once(
    effects: _Effects,
    repo: Path,
    lease_dir: Path,
    wave: str,
    main_sha: str,
    lifecycle: _AcceptanceLifecycle | None = None,
) -> str:
    if lifecycle is not None:
        lifecycle.ownership = _LeaseOwnership.UNKNOWN
    result = _run_capture(
        effects,
        _lease_command(repo, "claim", lease_dir, wave, main_sha),
        repo,
        "claim",
    )
    parsed = _parse_json_object(result.stdout, stage="claim-json")
    state = parsed.get("state")
    if not isinstance(state, str) or state not in _CLAIM_STATES:
        raise _StageFailure("claim-state")
    holder_self = parsed.get("holder_self") is True
    source = parsed.get("source")
    self_renew_failed = (
        state == "unavailable"
        and holder_self
        and isinstance(source, dict)
        and source.get("reason") == "self-renew-failed"
    )
    if lifecycle is not None:
        if state == "acquired":
            lifecycle.ownership = _LeaseOwnership.ACQUIRED
        elif state == "held-self" or self_renew_failed or holder_self:
            lifecycle.ownership = _LeaseOwnership.HELD_SELF
        else:
            lifecycle.ownership = _LeaseOwnership.NONE
            # held/queued の待ち札は 300 秒で失効するため、他 holder を release しない。
    if self_renew_failed:
        raise _StageFailure("claim-self-renew-failed")
    if state == "held-self":
        holder = parsed.get("holder")
        age_seconds = parsed.get("age_seconds")
        if not (
            holder_self
            and isinstance(holder, str)
            and _HOLDER_RE.fullmatch(holder) is not None
            and type(age_seconds) is int
            and source == {"status": "ok", "reason": None}
        ):
            raise _StageFailure("claim-self-unverified")
    elif state != "acquired" and holder_self:
        raise _StageFailure("claim-self-unverified")
    return state


def _wait_until_acquired(
    effects: _Effects,
    repo: Path,
    lease_dir: Path,
    wave: str,
    poll_seconds: int,
    max_wait_seconds: int,
    lifecycle: _AcceptanceLifecycle,
) -> float:
    started = effects.monotonic()
    while True:
        sha = _main_sha(effects, repo, "preclaim-rev-parse")
        claim_started_at = effects.monotonic()
        state = _claim_once(effects, repo, lease_dir, wave, sha, lifecycle)
        if state in _ACCEPTED_CLAIM_STATES:
            lifecycle.acquired_at = claim_started_at
            return claim_started_at
        if state not in _POLLING_CLAIM_STATES:
            raise _StageFailure("claim-state")
        if effects.monotonic() - started + poll_seconds > max_wait_seconds:
            raise _StageFailure("claim-timeout")
        effects.sleep(poll_seconds)


def _message_has_ai_agent(content: str) -> bool:
    return bool(content.strip()) and any(
        line.startswith("AI-Agent:") for line in content.splitlines()
    )


def _validated_message_copy(path: Path, effects: _Effects) -> Path | None:
    if not effects.is_file(path):
        return None
    try:
        content = effects.read_text(path)
    except (OSError, UnicodeError):
        return None
    if not _message_has_ai_agent(content):
        return None
    try:
        return effects.write_temp(content.encode("utf-8"))
    except (OSError, UnicodeError):
        return None


def _release_once(
    effects: _Effects,
    repo: Path,
    lease_dir: Path,
    wave: str,
) -> _Outcome:
    try:
        result = effects.run(
            _lease_command(repo, "release", lease_dir, wave), repo, True
        )
    except BaseException:
        return _Outcome(RC_CLEANUP_FAILED, "release")
    if result.returncode != 0:
        return _Outcome(RC_CLEANUP_FAILED, "release", result.returncode)
    try:
        parsed = _parse_json_object(result.stdout, stage="release-json")
    except _StageFailure:
        return _Outcome(RC_CLEANUP_FAILED, "release-json", result.returncode)
    state = parsed.get("state")
    if not isinstance(state, str) or state not in _RELEASED_STATES:
        return _Outcome(RC_CLEANUP_FAILED, "release-state", result.returncode)
    return _Outcome(RC_OK)


def _abort_pending_merge(effects: _Effects, repo: Path) -> _Outcome:
    failure: _Outcome | None = None
    try:
        result = effects.run(("git", "merge", "--abort"), repo, True)
    except BaseException:
        failure = _Outcome(RC_CLEANUP_FAILED, "merge-abort")
    else:
        if result.returncode != 0:
            failure = _Outcome(
                RC_CLEANUP_FAILED, "merge-abort", result.returncode
            )

    try:
        merge_head = effects.run(
            ("git", "rev-parse", "-q", "--verify", "MERGE_HEAD"),
            repo,
            True,
        )
    except BaseException:
        merge_head = None
    if (merge_head is None or merge_head.returncode != 1) and failure is None:
        failure = _Outcome(RC_CLEANUP_FAILED, "merge-abort-state")

    try:
        status = effects.run(
            ("git", "status", "--porcelain", "--untracked-files=no"),
            repo,
            True,
        )
    except BaseException:
        status = None
    if (
        (status is None or status.returncode != 0 or status.stdout)
        and failure is None
    ):
        failure = _Outcome(RC_CLEANUP_FAILED, "merge-abort-clean")
    return _Outcome(RC_OK) if failure is None else failure


def _normalize_child_rc(returncode: int) -> int:
    if returncode >= 0:
        return returncode
    return 128 + (-returncode)


def _cleanup_after_claim(
    effects: _Effects,
    repo: Path,
    lease_dir: Path,
    wave: str,
    *,
    merge_pending: bool,
    release_lease: bool,
) -> _Outcome | None:
    cleanup_failure: _Outcome | None = None
    previous_mask: set[signal.Signals] | None = None
    pthread_sigmask = getattr(signal, "pthread_sigmask", None)
    if pthread_sigmask is not None:
        try:
            previous_mask = pthread_sigmask(signal.SIG_BLOCK, _HANDLED_SIGNALS)
        except (OSError, ValueError):
            previous_mask = None
    try:
        if merge_pending:
            abort_outcome = _abort_pending_merge(effects, repo)
            if abort_outcome.rc != RC_OK:
                cleanup_failure = abort_outcome
        if release_lease:
            release_outcome = _release_once(effects, repo, lease_dir, wave)
            if release_outcome.rc != RC_OK:
                if cleanup_failure is not None:
                    _print_outcome(release_outcome)
                else:
                    cleanup_failure = release_outcome
    finally:
        if previous_mask is not None:
            try:
                pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            except _SignalReceived:
                # cleanup 中に届いた再 signal は cleanup 完了後まで遅延できた。
                pass
    return cleanup_failure


def _cleanup_lifecycle(
    lifecycle: _AcceptanceLifecycle,
    effects: _Effects,
    repo: Path,
    lease_dir: Path,
    wave: str,
) -> _Outcome | None:
    if lifecycle.ownership not in {
        _LeaseOwnership.UNKNOWN,
        _LeaseOwnership.ACQUIRED,
        _LeaseOwnership.HELD_SELF,
    }:
        return lifecycle.cleanup_failure
    ownership = lifecycle.ownership
    merge_pending = lifecycle.merge_pending
    # cleanup 権限を実処理より先に消費し、signal/finally の再入を no-op にする。
    lifecycle.ownership = _LeaseOwnership.NONE
    lifecycle.merge_pending = False
    lifecycle.cleanup_failure = _cleanup_after_claim(
        effects,
        repo,
        lease_dir,
        wave,
        merge_pending=merge_pending,
        release_lease=ownership in {
            _LeaseOwnership.UNKNOWN,
            _LeaseOwnership.ACQUIRED,
        },
    )
    if ownership is _LeaseOwnership.HELD_SELF:
        print(
            "acceptance: held-self lease retained; "
            "this invocation has no release authority",
            file=sys.stderr,
        )
    return lifecycle.cleanup_failure


def run_acceptance(
    *,
    wave: str,
    lease_dir: Path,
    merge_message_file: Path | None,
    poll_seconds: int,
    max_wait_seconds: int,
    command: Sequence[str],
    repo: Path,
    effects: _Effects,
    lifecycle: _AcceptanceLifecycle | None = None,
    owned_paths: Sequence[Path] = (),
) -> _Outcome:
    active_lifecycle = lifecycle or _AcceptanceLifecycle()
    primary = _Outcome(RC_FAIL_CLOSED, "internal")
    cleanup_failure: _Outcome | None = None
    validated_message: Path | None = None
    committed_sha: str | None = None
    try:
        _identity_preflight(effects, repo, wave)
        if merge_message_file is not None and not effects.is_file(merge_message_file):
            raise _StageFailure("merge-message-preflight", RC_USAGE)
        if not owned_paths:
            print(
                "acceptance: --owned-path 未指定のため所有実装面 overlap 判定を省略します",
                file=sys.stderr,
            )
        acquired_at = _wait_until_acquired(
            effects,
            repo,
            lease_dir,
            wave,
            poll_seconds,
            max_wait_seconds,
            active_lifecycle,
        )
        _main_sha(effects, repo, "postclaim-rev-parse")
        behind = _behind_count(effects, repo, "behind-count")
        if behind > 0:
            if owned_paths and _owned_path_overlap(effects, repo, owned_paths):
                raise _StageFailure("owned-path-overlap")
            if merge_message_file is None:
                raise _StageFailure("merge-message")
            validated_message = _validated_message_copy(merge_message_file, effects)
            if validated_message is None:
                raise _StageFailure("merge-message")
            active_lifecycle.merge_pending = True
            _run_capture(
                effects,
                ("git", "merge", "--no-ff", "--no-commit", "main"),
                repo,
                "merge",
            )
            _run_capture(
                effects,
                ("git", "commit", "--dry-run", "-F", str(validated_message)),
                repo,
                "commit-dry-run",
            )
            _run_capture(
                effects,
                ("git", "commit", "-F", str(validated_message)),
                repo,
                "commit",
            )
            active_lifecycle.merge_pending = False
            committed_sha = _head_sha(effects, repo, "commit-rev-parse")
            committed_message = _run_capture(
                effects,
                ("git", "log", "-1", "--format=%B", committed_sha),
                repo,
                "commit-message-postcheck",
            ).stdout
            if not _message_has_ai_agent(committed_message):
                raise _StageFailure("commit-message-postcheck")
        if _behind_count(effects, repo, "postcheck") != 0:
            raise _StageFailure("postcheck")
        if (
            committed_sha is not None
            and _head_sha(effects, repo, "commit-head-postcheck") != committed_sha
        ):
            raise _StageFailure("commit-head-postcheck")
        print(
            "acceptance-command argv=" + json.dumps(list(command), ensure_ascii=True),
            file=sys.stderr,
        )
        print(
            "acceptance-command timeout=none (long-running acceptance is intentional)",
            file=sys.stderr,
        )
        try:
            # 受入 command 自身は正当に長時間走るため、stage timeout を適用しない。
            child = effects.run_unbounded(tuple(command), repo, False)
        except (OSError, UnicodeError, subprocess.SubprocessError):
            raise _StageFailure("acceptance-command") from None
        child_rc = _normalize_child_rc(child.returncode)
        if child_rc == 0:
            try:
                elapsed = effects.monotonic() - acquired_at
            except Exception:
                raise _StageFailure("acceptance-clock") from None
            if not math.isfinite(elapsed) or elapsed < 0:
                raise _StageFailure("acceptance-clock")
            ttl_remaining = max(0, _LEASE_TTL_SECONDS - math.ceil(elapsed))
            print(
                "acceptance succeeded; lease is held; "
                f"TTL remaining at most {ttl_remaining} seconds; "
                "exclusivity is lost after expiry"
            )
            print("known limitation: no fencing token is provided")
            active_lifecycle.ownership = _LeaseOwnership.RETAINED
            primary = _Outcome(RC_OK)
        else:
            primary = _Outcome(child_rc, "acceptance-command", child.returncode)
    except _StageFailure as exc:
        primary = exc.outcome
    except KeyboardInterrupt:
        primary = _Outcome(RC_INTERRUPTED, "keyboard-interrupt")
    except _SignalReceived as exc:
        primary = _Outcome(128 + exc.signum, f"signal-{exc.signum}")
    except BaseException:
        primary = _Outcome(RC_FAIL_CLOSED, "unexpected-error")
    finally:
        if validated_message is not None:
            try:
                effects.unlink(validated_message)
            except OSError:
                pass
        cleanup_failure = _cleanup_lifecycle(
            active_lifecycle,
            effects,
            repo,
            lease_dir,
            wave,
        )
    return cleanup_failure if cleanup_failure is not None else primary


def _lease_dir(argument: Path | None, effects: _Effects) -> Path:
    if argument is not None:
        return argument
    value = effects.getenv(_LEASE_ENV)
    if not value:
        raise _StageFailure("lease-dir", RC_USAGE)
    return Path(value)


def _install_signal_handlers() -> dict[int, object]:
    # SIGKILL と host 停止は unwind 不能なので既存 lease TTL に委ねる。
    previous: dict[int, object] = {}

    def handler(signum: int, frame: object) -> None:
        del frame
        raise _SignalReceived(signum)

    try:
        for signum in _HANDLED_SIGNALS:
            previous[signum] = signal.getsignal(signum)
            signal.signal(signum, handler)
    except BaseException:
        _restore_signal_handlers(previous)
        raise
    return previous


def _restore_signal_handlers(previous: dict[int, object]) -> None:
    previous_mask: set[signal.Signals] | None = None
    pthread_sigmask = getattr(signal, "pthread_sigmask", None)
    if pthread_sigmask is not None:
        previous_mask = pthread_sigmask(signal.SIG_BLOCK, _HANDLED_SIGNALS)
    failure: BaseException | None = None
    try:
        for signum, handler in previous.items():
            try:
                signal.signal(signum, handler)
            except BaseException as exc:
                if failure is None:
                    failure = exc
    finally:
        if previous_mask is not None:
            pthread_sigmask(signal.SIG_SETMASK, previous_mask)
    if failure is not None:
        raise failure


def _print_outcome(outcome: _Outcome) -> None:
    if outcome.rc == 0:
        return
    suffix = f" source_rc={outcome.source_rc}" if outcome.source_rc is not None else ""
    print(f"error: stage={outcome.stage or 'unknown'} rc={outcome.rc}{suffix}", file=sys.stderr)


def main(
    argv: Sequence[str] | None = None,
    *,
    effects: _Effects | None = None,
    repo: Path | None = None,
) -> int:
    active_effects = _default_effects() if effects is None else effects
    try:
        command, args, child_argv = _parse_cli(
            list(sys.argv[1:] if argv is None else argv)
        )
        if command == "producer":
            pid = _resolve_pid(args.pid, args.pid_file, active_effects)
            outcome = wait_for_producer(
                done_file=args.done_file,
                artifact_file=args.artifact_file,
                pid=pid,
                max_wait_seconds=args.max_wait_seconds,
                effects=active_effects,
            )
        else:
            active_repo = Path.cwd() if repo is None else repo
            lease_dir = _lease_dir(args.lease_dir, active_effects)
            lifecycle = _AcceptanceLifecycle()
            previous = _install_signal_handlers()
            try:
                outcome = run_acceptance(
                    wave=args.wave,
                    lease_dir=lease_dir,
                    merge_message_file=args.merge_message_file,
                    poll_seconds=args.poll_seconds,
                    max_wait_seconds=args.max_wait_seconds,
                    command=child_argv,
                    repo=active_repo,
                    effects=active_effects,
                    lifecycle=lifecycle,
                    owned_paths=args.owned_path,
                )
            except BaseException as exc:
                if isinstance(exc, _SignalReceived):
                    outcome = _Outcome(128 + exc.signum, f"signal-{exc.signum}")
                elif isinstance(exc, KeyboardInterrupt):
                    outcome = _Outcome(RC_INTERRUPTED, "keyboard-interrupt")
                else:
                    outcome = _Outcome(RC_FAIL_CLOSED, "internal")
                cleanup = _cleanup_lifecycle(
                    lifecycle,
                    active_effects,
                    active_repo,
                    lease_dir,
                    args.wave,
                )
                if cleanup is not None:
                    outcome = cleanup
            finally:
                restored = False
                while not restored:
                    try:
                        _restore_signal_handlers(previous)
                        restored = True
                    except BaseException as exc:
                        if isinstance(exc, _SignalReceived):
                            outcome = _Outcome(
                                128 + exc.signum, f"signal-{exc.signum}"
                            )
                        elif isinstance(exc, KeyboardInterrupt):
                            outcome = _Outcome(
                                RC_INTERRUPTED, "keyboard-interrupt"
                            )
                        else:
                            outcome = _Outcome(
                                RC_FAIL_CLOSED, "signal-restore"
                            )
                            restored = True
                        cleanup = _cleanup_lifecycle(
                            lifecycle,
                            active_effects,
                            active_repo,
                            lease_dir,
                            args.wave,
                        )
                        if cleanup is not None:
                            outcome = cleanup
    except _StageFailure as exc:
        outcome = exc.outcome
    except (Exception, KeyboardInterrupt):
        outcome = _Outcome(RC_FAIL_CLOSED, "internal")
    _print_outcome(outcome)
    return outcome.rc


if __name__ == "__main__":
    sys.exit(main())
