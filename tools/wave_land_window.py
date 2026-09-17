#!/usr/bin/env python3
"""dev-wave の受入 claim に使う advisory な sidecar lease。"""
from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import json
import os
import re
import stat
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


RC_OK = 0
RC_REJECTED = 2
RC_MESSAGE_REJECTED = 3

_PROGRAM = "wave-land-window"
_LEASE_NAME = "acceptance.lease"
_TICKET_PREFIX = "ticket."
_LEASE_ENV = "IZANAGI_WAVE_LEASE_DIR"
_POLICY_TTL_SECONDS = 2400
_MAX_LEASE_BYTES = 4096
_MAX_LAND_JSON_BYTES = 64 * 1024
_MAX_RACE_RETRIES = 8
_MAX_LOCK_RETRIES = 8
_LOCK_RETRY_DELAY_SECONDS = 0.01
_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
_HOLDER_RE = re.compile(r"[0-9a-f]{12}\Z")
_SUCCESS_STATUSES = frozenset({"landed", "already-landed"})
_ADVISORY = (
    "advisory です。指示ではありません。local main を読み直す契機にだけ使い、"
    "待機・取り込み・検査省略の根拠にしないでください。"
    "受入を開始済みなら中断せず完走してください。"
)
_ROLLED_BACK_ADVISORY = (
    "advisory です。指示ではありません。local main を読み直す契機にだけ使い、"
    "待機・取り込み・検査省略の根拠にしないでください。"
    "受入を開始済みなら中断せず完走してください。"
    "この land 結果では main は記載の SHA にあり、wave tip とは異なります。"
    "取り込んだ main の SHA について git merge-base --is-ancestor <SHA> refs/heads/main が rc=1 なら、"
    "受入完走後に受入 tip へ reset して取り込み直してください。"
)


class _Rejected(Exception):
    def __init__(self, rc: int, reason: str):
        super().__init__(reason)
        self.rc = rc
        self.reason = reason


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise _Rejected(RC_REJECTED, "cli-usage")


@dataclass(frozen=True)
class _Lease:
    fd: int
    metadata: os.stat_result
    holder: str | None
    main_sha: str | None
    age_seconds: int
    stale: bool

    @property
    def payload_valid(self) -> bool:
        return self.holder is not None and self.main_sha is not None


def _is_sha(value: object) -> bool:
    return isinstance(value, str) and _SHA_RE.fullmatch(value) is not None


def _holder_for(wave: str) -> str:
    try:
        return hashlib.sha256(wave.encode("utf-8")).hexdigest()[:12]
    except UnicodeError:
        raise _Rejected(RC_REJECTED, "wave-invalid") from None


def _read_fd(fd: int, limit: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        request = min(64 * 1024, limit + 1 - total)
        if request <= 0:
            raise ValueError("byte limit exceeded")
        chunk = os.read(fd, request)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)
        total += len(chunk)
        if total > limit:
            raise ValueError("byte limit exceeded")


def _write_all(fd: int, content: bytes) -> None:
    view = memoryview(content)
    offset = 0
    while offset < len(view):
        written = os.write(fd, view[offset:])
        if written <= 0:
            raise OSError("short write")
        offset += written


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _load_json(content: bytes) -> object:
    return json.loads(content.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)


def _lease_payload(holder: str, main_sha: str, ttl: int) -> bytes:
    value = {"holder": holder, "main_sha": main_sha, "ttl": ttl}
    return (json.dumps(value, ensure_ascii=True) + "\n").encode("ascii")


# 旧版が残した ticket を release 時に掃除するためだけに残す。
def _ticket_name(holder: str) -> str:
    if _HOLDER_RE.fullmatch(holder) is None:
        raise ValueError("invalid ticket holder")
    return f"{_TICKET_PREFIX}{holder}"


def _parse_lease(content: bytes) -> tuple[str, str]:
    value = _load_json(content)
    if not isinstance(value, dict) or set(value) != {"holder", "main_sha", "ttl"}:
        raise ValueError("invalid lease")
    holder, main_sha, ttl = value["holder"], value["main_sha"], value["ttl"]
    if not isinstance(holder, str) or _HOLDER_RE.fullmatch(holder) is None:
        raise ValueError("invalid holder")
    if not _is_sha(main_sha):
        raise ValueError("invalid main sha")
    if (
        isinstance(ttl, bool)
        or not isinstance(ttl, int)
        or ttl <= 0
        or ttl > _POLICY_TTL_SECONDS
    ):
        raise ValueError("invalid ttl")
    return holder, main_sha


def _mtime_state(metadata: os.stat_result) -> tuple[int, bool]:
    delta = time.time() - metadata.st_mtime
    age_seconds = max(0, int(delta))
    future_seconds = max(0, int(-delta))
    stale = (
        age_seconds > _POLICY_TTL_SECONDS
        or future_seconds > _POLICY_TTL_SECONDS
    )
    return age_seconds, stale


def _result(
    state: str,
    holder: str | None = None,
    self_holder: str | None = None,
    main_sha: str | None = None,
    age_seconds: int = 0,
    unavailable_reason: str | None = None,
) -> dict[str, object]:
    source_status = "unavailable" if unavailable_reason else "ok"
    return {
        "state": state,
        "holder": holder,
        "holder_self": holder is not None and holder == self_holder,
        "main_sha": main_sha,
        "age_seconds": age_seconds,
        "source": {"status": source_status, "reason": unavailable_reason},
    }


def _unavailable(reason: str, self_holder: str | None) -> dict[str, object]:
    return _result("unavailable", self_holder=self_holder, unavailable_reason=reason)


def _open_directory(lease_dir: Path) -> int:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        raise OSError(errno.ENOTSUP, "required open flags unavailable")
    flags = os.O_RDONLY | directory | nofollow | getattr(os, "O_CLOEXEC", 0)
    return os.open(lease_dir, flags)


def _same_entry(directory_fd: int, name: str, metadata: os.stat_result) -> bool:
    try:
        current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except OSError:
        return False
    return (
        stat.S_ISREG(current.st_mode)
        and (current.st_dev, current.st_ino) == (metadata.st_dev, metadata.st_ino)
    )


def _validate_owned_regular(metadata: os.stat_result) -> None:
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("entry is not regular")
    if metadata.st_uid != os.geteuid():
        raise ValueError("entry owner differs")


def _flock_bounded(fd: int, operation: int) -> None:
    retryable = {errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK}
    for attempt in range(_MAX_LOCK_RETRIES):
        try:
            fcntl.flock(fd, operation | fcntl.LOCK_NB)
            return
        except OSError as exc:
            if exc.errno not in retryable:
                raise
            if attempt + 1 < _MAX_LOCK_RETRIES:
                time.sleep(_LOCK_RETRY_DELAY_SECONDS)
    raise BlockingIOError(errno.EWOULDBLOCK, "lease lock busy")


def _open_lease(directory_fd: int, *, exclusive: bool) -> _Lease:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise OSError(errno.ENOTSUP, "required open flag unavailable")
    flags = (
        os.O_RDONLY
        | os.O_NONBLOCK
        | nofollow
        | getattr(os, "O_CLOEXEC", 0)
    )
    fd = os.open(_LEASE_NAME, flags, dir_fd=directory_fd)
    try:
        initial_metadata = os.fstat(fd)
        _validate_owned_regular(initial_metadata)
        _flock_bounded(fd, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        metadata = os.fstat(fd)
        _validate_owned_regular(metadata)
        try:
            holder, main_sha = _parse_lease(_read_fd(fd, _MAX_LEASE_BYTES))
        except (UnicodeError, ValueError, RecursionError):
            holder, main_sha = None, None
        if not _same_entry(directory_fd, _LEASE_NAME, metadata):
            raise FileNotFoundError(errno.ENOENT, "lease changed")
        age_seconds, stale = _mtime_state(metadata)
        return _Lease(fd, metadata, holder, main_sha, age_seconds, stale)
    except BaseException:
        os.close(fd)
        raise


def _lease_result(
    state: str,
    lease: _Lease,
    self_holder: str | None,
    *,
    age_seconds: int | None = None,
    unavailable_reason: str | None = None,
) -> dict[str, object]:
    return _result(
        state,
        lease.holder,
        self_holder,
        lease.main_sha,
        age_seconds=lease.age_seconds if age_seconds is None else age_seconds,
        unavailable_reason=unavailable_reason,
    )


def _create_lease(
    directory_fd: int, holder: str, main_sha: str
) -> dict[str, object] | None:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise OSError(errno.ENOTSUP, "required open flag unavailable")
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | nofollow
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        fd = os.open(_LEASE_NAME, flags, 0o600, dir_fd=directory_fd)
    except FileExistsError:
        return None
    metadata: os.stat_result | None = None
    try:
        metadata = os.fstat(fd)
        _validate_owned_regular(metadata)
        _flock_bounded(fd, fcntl.LOCK_EX)
        _write_all(fd, _lease_payload(holder, main_sha, _POLICY_TTL_SECONDS))
        os.fsync(fd)
    except BaseException:
        if metadata is not None and _same_entry(directory_fd, _LEASE_NAME, metadata):
            try:
                os.unlink(_LEASE_NAME, dir_fd=directory_fd)
            except OSError:
                pass
        raise
    finally:
        os.close(fd)
    return _result("acquired", holder, holder, main_sha)


def _drop_ticket_best_effort(directory_fd: int, holder: str) -> bool:
    try:
        name = _ticket_name(holder)
    except (ValueError, UnicodeError, RecursionError):
        return False
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        return False
    flags = (
        os.O_RDONLY
        | os.O_NONBLOCK
        | nofollow
        | getattr(os, "O_CLOEXEC", 0)
    )
    for _ in range(_MAX_RACE_RETRIES):
        try:
            fd = os.open(name, flags, dir_fd=directory_fd)
        except FileNotFoundError:
            return True
        except OSError:
            continue
        try:
            metadata = os.fstat(fd)
            _validate_owned_regular(metadata)
            if not _same_entry(directory_fd, name, metadata):
                return False
            os.unlink(name, dir_fd=directory_fd)
            return True
        except FileNotFoundError:
            continue
        except (OSError, ValueError, UnicodeError, RecursionError):
            continue
        finally:
            try:
                os.close(fd)
            except OSError:
                pass
    return False


def claim(lease_dir: Path, wave: str, main_sha: str, ttl: int) -> dict[str, object]:
    self_holder = _holder_for(wave)
    if (
        not _is_sha(main_sha)
        or isinstance(ttl, bool)
        or not isinstance(ttl, int)
        or ttl <= 0
        or ttl > _POLICY_TTL_SECONDS
    ):
        raise _Rejected(RC_REJECTED, "claim-input-invalid")
    try:
        directory_fd = _open_directory(lease_dir)
    except OSError:
        return _unavailable("directory-unavailable", self_holder)
    last_stale: _Lease | None = None
    try:
        for _ in range(_MAX_RACE_RETRIES):
            try:
                lease = _open_lease(directory_fd, exclusive=True)
            except FileNotFoundError:
                lease = None
            except (OSError, UnicodeError, ValueError, RecursionError):
                return _unavailable("lease-unavailable", self_holder)
            if lease is None:
                try:
                    acquired = _create_lease(directory_fd, self_holder, main_sha)
                except (OSError, UnicodeError, ValueError, RecursionError):
                    return _unavailable("lease-unavailable", self_holder)
                if acquired is not None:
                    return acquired
                continue
            try:
                if not lease.stale and not lease.payload_valid:
                    return _unavailable("lease-unavailable", self_holder)
                if not lease.stale:
                    if lease.holder == self_holder:
                        try:
                            renewed_ns = time.time_ns()
                            os.utime(lease.fd, ns=(renewed_ns, renewed_ns))
                            refreshed_metadata = os.fstat(lease.fd)
                            _validate_owned_regular(refreshed_metadata)
                            if not _same_entry(
                                directory_fd, _LEASE_NAME, refreshed_metadata
                            ):
                                raise FileNotFoundError(
                                    errno.ENOENT, "renewed lease changed"
                                )
                            age_seconds, stale = _mtime_state(refreshed_metadata)
                            if stale:
                                raise ValueError("renewed lease is stale")
                        except Exception:
                            return _lease_result(
                                "unavailable",
                                lease,
                                self_holder,
                                unavailable_reason="self-renew-failed",
                            )
                        return _lease_result(
                            "held-self",
                            lease,
                            self_holder,
                            age_seconds=age_seconds,
                        )
                    return _lease_result("held", lease, self_holder)
                last_stale = lease
                if not _same_entry(directory_fd, _LEASE_NAME, lease.metadata):
                    continue
                try:
                    os.unlink(_LEASE_NAME, dir_fd=directory_fd)
                except FileNotFoundError:
                    continue
                except OSError:
                    return _unavailable("stale-release-failed", self_holder)
            finally:
                os.close(lease.fd)
        if last_stale is not None:
            return _lease_result("stale-held", last_stale, self_holder)
        return _unavailable("lease-race", self_holder)
    finally:
        os.close(directory_fd)


def renew(lease_dir: Path, wave: str) -> dict[str, object]:
    self_holder = _holder_for(wave)
    try:
        directory_fd = _open_directory(lease_dir)
    except OSError:
        return _unavailable("directory-unavailable", self_holder)
    try:
        for _ in range(_MAX_RACE_RETRIES):
            try:
                names = os.listdir(directory_fd)
            except OSError:
                return _unavailable("directory-unavailable", self_holder)
            if _LEASE_NAME not in names:
                return _result("free", self_holder=self_holder)
            try:
                lease = _open_lease(directory_fd, exclusive=True)
            except FileNotFoundError:
                continue
            except (OSError, UnicodeError, ValueError, RecursionError):
                return _unavailable("lease-unavailable", self_holder)
            try:
                if not lease.stale and not lease.payload_valid:
                    return _lease_result(
                        "unavailable",
                        lease,
                        self_holder,
                        unavailable_reason="lease-unavailable",
                    )
                if lease.stale:
                    return _lease_result("stale", lease, self_holder)
                if lease.holder != self_holder:
                    return _lease_result("not-owner", lease, self_holder)
                try:
                    renewed_ns = time.time_ns()
                    os.utime(lease.fd, ns=(renewed_ns, renewed_ns))
                    refreshed_metadata = os.fstat(lease.fd)
                    _validate_owned_regular(refreshed_metadata)
                    if not _same_entry(
                        directory_fd, _LEASE_NAME, refreshed_metadata
                    ):
                        raise FileNotFoundError(
                            errno.ENOENT, "renewed lease changed"
                        )
                    age_seconds, stale = _mtime_state(refreshed_metadata)
                    if stale:
                        raise ValueError("renewed lease is stale")
                except Exception:
                    return _lease_result(
                        "unavailable",
                        lease,
                        self_holder,
                        unavailable_reason="self-renew-failed",
                    )
                return _lease_result(
                    "held-self",
                    lease,
                    self_holder,
                    age_seconds=age_seconds,
                )
            finally:
                os.close(lease.fd)
        return _unavailable("lease-race", self_holder)
    finally:
        os.close(directory_fd)


def release(
    lease_dir: Path,
    wave: str,
    expected_main_sha: str | None = None,
) -> dict[str, object]:
    self_holder = _holder_for(wave)
    try:
        directory_fd = _open_directory(lease_dir)
    except OSError:
        return _unavailable("directory-unavailable", self_holder)
    cleanup_in_finally = True
    try:
        for _ in range(_MAX_RACE_RETRIES):
            try:
                lease = _open_lease(directory_fd, exclusive=True)
            except FileNotFoundError:
                _drop_ticket_best_effort(directory_fd, self_holder)
                cleanup_in_finally = False
                return _result("free", self_holder=self_holder)
            except (OSError, UnicodeError, ValueError, RecursionError):
                return _unavailable("lease-unavailable", self_holder)
            try:
                if not lease.payload_valid:
                    return _unavailable("lease-unavailable", self_holder)
                if lease.holder != self_holder:
                    return _lease_result("not-owner", lease, self_holder)
                if (
                    expected_main_sha is not None
                    and lease.main_sha != expected_main_sha
                ):
                    return _result(
                        "not-owner",
                        lease.holder,
                        self_holder,
                        lease.main_sha,
                        lease.age_seconds,
                        "main-sha-mismatch",
                    )
                if not _same_entry(directory_fd, _LEASE_NAME, lease.metadata):
                    continue
                try:
                    os.unlink(_LEASE_NAME, dir_fd=directory_fd)
                except FileNotFoundError:
                    continue
                except OSError:
                    return _unavailable("lease-release-failed", self_holder)
                return _result("released", lease.holder, self_holder)
            finally:
                os.close(lease.fd)
        return _unavailable("lease-race", self_holder)
    finally:
        if cleanup_in_finally:
            _drop_ticket_best_effort(directory_fd, self_holder)
        os.close(directory_fd)


def status(lease_dir: Path, wave: str | None) -> dict[str, object]:
    self_holder = _holder_for(wave) if wave is not None else None
    try:
        directory_fd = _open_directory(lease_dir)
    except OSError:
        return _unavailable("directory-unavailable", self_holder)
    try:
        for _ in range(_MAX_RACE_RETRIES):
            try:
                names = os.listdir(directory_fd)
            except OSError:
                return _unavailable("directory-unavailable", self_holder)
            if _LEASE_NAME not in names:
                return _result("free", self_holder=self_holder)
            try:
                lease = _open_lease(directory_fd, exclusive=False)
            except FileNotFoundError:
                continue
            except (OSError, UnicodeError, ValueError, RecursionError):
                return _unavailable("lease-unavailable", self_holder)
            try:
                if not lease.stale and not lease.payload_valid:
                    return _unavailable("lease-unavailable", self_holder)
                state_value = "stale" if lease.stale else "held"
                return _lease_result(state_value, lease, self_holder)
            finally:
                os.close(lease.fd)
        return _unavailable("lease-race", self_holder)
    finally:
        os.close(directory_fd)


def _load_land_result(path: Path) -> dict[str, object]:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise _Rejected(RC_MESSAGE_REJECTED, "land-json-rejected")
    try:
        fd = os.open(path, os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0))
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError("not regular")
            value = _load_json(_read_fd(fd, _MAX_LAND_JSON_BYTES))
        finally:
            os.close(fd)
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError):
        raise _Rejected(RC_MESSAGE_REJECTED, "land-json-rejected") from None
    if not isinstance(value, dict):
        raise _Rejected(RC_MESSAGE_REJECTED, "land-json-rejected")
    return value


def message(wave: str, land_json: Path, *, kind: str = "landed") -> str:
    holder = _holder_for(wave)
    result = _load_land_result(land_json)
    status_value = result.get("status")
    if kind == "rolled-back":
        if not isinstance(status_value, str) or status_value != "fold-failed":
            raise _Rejected(RC_MESSAGE_REJECTED, "land-status-rejected")
        main_after = result.get("main_after")
        if not _is_sha(main_after):
            raise _Rejected(RC_MESSAGE_REJECTED, "land-main-rejected")
        wave_tip = result.get("wave_tip")
        if not _is_sha(wave_tip):
            raise _Rejected(RC_MESSAGE_REJECTED, "land-tip-rejected")
        if main_after == wave_tip:
            raise _Rejected(RC_MESSAGE_REJECTED, "land-tip-rejected")
        return (
            f"[dev-wave] rolled-back main={main_after} wave-tip={wave_tip} wave={holder}\n"
            f"{_ROLLED_BACK_ADVISORY}"
        )
    if not isinstance(status_value, str) or status_value not in _SUCCESS_STATUSES:
        raise _Rejected(RC_MESSAGE_REJECTED, "land-status-rejected")
    main_after = result.get("main_after")
    if not _is_sha(main_after):
        raise _Rejected(RC_MESSAGE_REJECTED, "land-main-rejected")
    return f"[dev-wave] landed main={main_after} wave={holder}\n{_ADVISORY}"


def _lease_dir(argument: Path | None) -> Path:
    if argument is not None:
        return argument
    value = os.environ.get(_LEASE_ENV)
    if not value:
        raise _Rejected(RC_REJECTED, "lease-dir-required")
    return Path(value)


def _ttl_seconds(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("invalid integer") from None
    if parsed <= 0 or parsed > _POLICY_TTL_SECONDS:
        raise argparse.ArgumentTypeError("invalid integer")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog=_PROGRAM, description="dev-wave acceptance lease helper")
    commands = parser.add_subparsers(dest="command", required=True)
    claim_parser = commands.add_parser("claim")
    claim_parser.add_argument("--lease-dir", type=Path)
    claim_parser.add_argument("--wave", required=True, metavar="WAVE")
    claim_parser.add_argument("--main-sha", required=True, metavar="SHA")
    claim_parser.add_argument(
        "--ttl", type=_ttl_seconds, default=_POLICY_TTL_SECONDS, metavar="SECONDS"
    )
    release_parser = commands.add_parser("release")
    release_parser.add_argument("--lease-dir", type=Path)
    release_parser.add_argument("--wave", required=True, metavar="WAVE")
    status_parser = commands.add_parser("status")
    status_parser.add_argument("--lease-dir", type=Path)
    status_parser.add_argument("--wave", metavar="WAVE")
    status_parser.add_argument("--json", action="store_true")
    message_parser = commands.add_parser("message")
    message_parser.add_argument("--kind", choices=("landed", "rolled-back"), required=True)
    message_parser.add_argument("--land-json", type=Path, required=True)
    message_parser.add_argument("--wave", required=True, metavar="WAVE")
    return parser


def _print_status(result: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return
    holder = result["holder"] if result["holder"] is not None else "none"
    main_sha = result["main_sha"] if result["main_sha"] is not None else "none"
    source = result["source"]
    assert isinstance(source, dict)
    reason = source["reason"] if source["reason"] is not None else "none"
    print(
        f"state={result['state']} holder={holder} "
        f"holder_self={str(result['holder_self']).lower()} main_sha={main_sha} "
        f"age_seconds={result['age_seconds']} source={source['status']} reason={reason}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if args.command == "claim":
            result = claim(_lease_dir(args.lease_dir), args.wave, args.main_sha, args.ttl)
            print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        elif args.command == "release":
            result = release(_lease_dir(args.lease_dir), args.wave)
            print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        elif args.command == "status":
            _print_status(status(_lease_dir(args.lease_dir), args.wave), args.json)
        else:
            print(message(args.wave, args.land_json, kind=args.kind))
        return RC_OK
    except _Rejected as exc:
        print(f"error: {exc.reason}", file=sys.stderr)
        return exc.rc
    except (Exception, KeyboardInterrupt):
        print("error: internal-error", file=sys.stderr)
        return RC_REJECTED


if __name__ == "__main__":
    sys.exit(main())
