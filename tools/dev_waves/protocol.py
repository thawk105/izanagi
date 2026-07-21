"""Length-framed one-request Unix-socket transport for dev-waves."""
from __future__ import annotations

import os
import socket
import stat
import struct
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from .schema import (
    DEFAULT_MAX_JSON_BYTES, DevWavesError, ReasonCode, canonical_bytes,
)


FRAME_HEADER_BYTES = 4
SOCKET_BASENAME = ".s"
RUNTIME_DIR_MODE = 0o700
SOCKET_MODE = 0o600


@dataclass(frozen=True)
class PeerCredentials:
    pid: int
    uid: int
    gid: int


@dataclass
class SocketPathAlias:
    directory_fd: int
    path: str

    def close(self) -> None:
        if self.directory_fd >= 0:
            os.close(self.directory_fd)
            self.directory_fd = -1

    def __enter__(self) -> "SocketPathAlias":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self.close()


@dataclass
class BoundRepoSocket:
    sock: socket.socket
    alias: SocketPathAlias
    socket_device: int
    socket_inode: int
    closed: bool = False

    @property
    def path(self) -> str:
        return self.alias.path

    @property
    def directory_fd(self) -> int:
        return self.alias.directory_fd

    def accept(self) -> tuple[socket.socket, object]:
        return self.sock.accept()

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        try:
            self.sock.close()
        finally:
            try:
                info = os.stat(
                    SOCKET_BASENAME, dir_fd=self.alias.directory_fd,
                    follow_symlinks=False,
                )
                if (info.st_dev, info.st_ino) == (self.socket_device, self.socket_inode):
                    os.unlink(SOCKET_BASENAME, dir_fd=self.alias.directory_fd)
            except FileNotFoundError:
                pass
            finally:
                self.alias.close()

    def __enter__(self) -> "BoundRepoSocket":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self.close()


def _runtime_error(kind: str) -> DevWavesError:
    return DevWavesError(ReasonCode.RUNTIME_IO_FAILURE, {
        "label": "repo-socket", "kind": kind,
    })


def _open_runtime_dir(runtime_dir: os.PathLike[str] | str, expected_uid: int) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(os.fspath(runtime_dir), flags)
        info = os.fstat(fd)
        if info.st_uid != expected_uid or stat.S_IMODE(info.st_mode) != RUNTIME_DIR_MODE:
            os.close(fd)
            raise _runtime_error("runtime-dir-owner-mode")
        return fd
    except DevWavesError:
        raise
    except OSError:
        raise _runtime_error("runtime-dir-open") from None


def socket_path_alias(
    runtime_dir: os.PathLike[str] | str,
    *,
    expected_uid: Optional[int] = None,
) -> SocketPathAlias:
    """Open runtime_dir and return its short /proc/self/fd alias.

    The directory fd must remain open for as long as the alias is used.  This
    avoids AF_UNIX sun_path limits without silently moving the socket.
    """
    uid = os.getuid() if expected_uid is None else expected_uid
    fd = _open_runtime_dir(runtime_dir, uid)
    alias = f"/proc/self/fd/{fd}/{SOCKET_BASENAME}"
    if not os.path.isdir(f"/proc/self/fd/{fd}"):
        os.close(fd)
        raise _runtime_error("proc-fd-unavailable")
    # Linux sockaddr_un.sun_path is 108 bytes including its terminating NUL.
    if len(os.fsencode(alias)) >= 108:
        os.close(fd)
        raise _runtime_error("socket-alias-too-long")
    return SocketPathAlias(fd, alias)


def peer_credentials(sock: socket.socket) -> PeerCredentials:
    if not hasattr(socket, "SO_PEERCRED"):
        raise _runtime_error("peer-credentials-unavailable")
    try:
        raw = sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
        pid, uid, gid = struct.unpack("3i", raw)
    except (OSError, struct.error):
        raise _runtime_error("peer-credentials-read") from None
    if pid <= 0 or uid < 0 or gid < 0:
        raise _runtime_error("peer-credentials-invalid")
    return PeerCredentials(pid, uid, gid)


def _boottime() -> float:
    return time.clock_gettime(time.CLOCK_BOOTTIME)


def _deadline_left(deadline: float) -> float:
    left = deadline - _boottime()
    if left <= 0:
        raise _runtime_error("read-deadline")
    return left


def _recv_exact(
    sock: socket.socket, size: int, kind: str, *, deadline: Optional[float] = None,
) -> bytes:
    chunks = []
    remaining = size
    while remaining:
        if deadline is not None:
            left = deadline - _boottime()
            if left <= 0:
                raise _runtime_error("read-deadline")
            sock.settimeout(left)
        try:
            chunk = sock.recv(remaining)
        except (socket.timeout, TimeoutError):
            raise _runtime_error("read-deadline") from None
        except OSError:
            raise _runtime_error(kind) from None
        if not chunk:
            raise _runtime_error(kind)
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def recv_frame(
    sock: socket.socket,
    *,
    max_bytes: int,
    require_eof: bool = True,
    deadline: Optional[float] = None,
) -> bytes:
    """Read one frame and, by default, require the peer's write half-close."""
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1:
        raise ValueError("max_bytes must be a positive integer")
    header = _recv_exact(
        sock, FRAME_HEADER_BYTES, "truncated-frame-header", deadline=deadline,
    )
    length = struct.unpack(">I", header)[0]
    if length < 1:
        raise _runtime_error("empty-frame")
    if length > max_bytes:
        raise _runtime_error("oversize-frame")
    payload = _recv_exact(sock, length, "truncated-frame-body", deadline=deadline)
    if require_eof:
        if deadline is not None:
            left = deadline - _boottime()
            if left <= 0:
                raise _runtime_error("read-deadline")
            sock.settimeout(left)
        try:
            trailing = sock.recv(1)
        except (socket.timeout, TimeoutError):
            raise _runtime_error("half-close-required") from None
        except OSError:
            raise _runtime_error("trailing-frame-check") from None
        if trailing:
            raise _runtime_error("trailing-frame")
    return payload


def send_frame(
    sock: socket.socket, raw: bytes, *, deadline: Optional[float] = None,
) -> None:
    if not isinstance(raw, bytes):
        raise TypeError("raw must be bytes")
    if not raw or len(raw) > 0xFFFFFFFF:
        raise ValueError("frame payload length out of range")
    data = struct.pack(">I", len(raw)) + raw
    view = memoryview(data)
    while view:
        if deadline is not None:
            sock.settimeout(_deadline_left(deadline))
        try:
            sent = sock.send(view)
        except (socket.timeout, TimeoutError):
            raise _runtime_error("write-deadline") from None
        except OSError:
            raise _runtime_error("frame-write") from None
        if sent <= 0:
            raise _runtime_error("short-frame-write")
        view = view[sent:]


def bind_repo_socket(
    runtime_dir: os.PathLike[str] | str,
    expected_uid: int,
) -> BoundRepoSocket:
    alias = socket_path_alias(runtime_dir, expected_uid=expected_uid)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    created = False
    try:
        try:
            os.stat(SOCKET_BASENAME, dir_fd=alias.directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise _runtime_error("socket-path-exists")
        sock.bind(alias.path)
        created = True
        os.chmod(
            SOCKET_BASENAME, SOCKET_MODE, dir_fd=alias.directory_fd,
            follow_symlinks=False,
        )
        info = os.stat(SOCKET_BASENAME, dir_fd=alias.directory_fd, follow_symlinks=False)
        if (info.st_uid != expected_uid or stat.S_IMODE(info.st_mode) != SOCKET_MODE or
                not stat.S_ISSOCK(info.st_mode)):
            raise _runtime_error("socket-owner-mode")
        sock.listen(1)
        return BoundRepoSocket(sock, alias, info.st_dev, info.st_ino)
    except Exception:
        sock.close()
        if created:
            try:
                os.unlink(SOCKET_BASENAME, dir_fd=alias.directory_fd)
            except FileNotFoundError:
                pass
        alias.close()
        raise


def connect_repo_socket(
    runtime_dir: os.PathLike[str] | str,
    timeout_s: float,
) -> socket.socket:
    if not isinstance(timeout_s, (int, float)) or isinstance(timeout_s, bool) or timeout_s <= 0:
        raise ValueError("timeout_s must be positive")
    alias = socket_path_alias(runtime_dir, expected_uid=os.getuid())
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(float(timeout_s))
    try:
        info = os.stat(SOCKET_BASENAME, dir_fd=alias.directory_fd, follow_symlinks=False)
        if (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != SOCKET_MODE or
                not stat.S_ISSOCK(info.st_mode)):
            raise _runtime_error("socket-owner-mode")
        sock.connect(alias.path)
        after = os.stat(SOCKET_BASENAME, dir_fd=alias.directory_fd, follow_symlinks=False)
        if (after.st_dev, after.st_ino) != (info.st_dev, info.st_ino):
            raise _runtime_error("socket-inode-changed")
        return sock
    except Exception:
        sock.close()
        raise
    finally:
        alias.close()


def receive_request(
    conn: socket.socket,
    *,
    max_bytes: int,
    deadline_s: float,
    expected_uid: int,
) -> bytes:
    """Server-side bounded read with peer UID and half-close enforcement."""
    if (not isinstance(deadline_s, (int, float)) or isinstance(deadline_s, bool) or
            deadline_s <= 0):
        raise ValueError("deadline_s must be positive")
    credentials = peer_credentials(conn)
    if credentials.uid != expected_uid:
        raise _runtime_error("peer-uid-mismatch")
    previous_timeout = conn.gettimeout()
    deadline = _boottime() + float(deadline_s)
    conn.settimeout(float(deadline_s))
    try:
        return recv_frame(
            conn, max_bytes=max_bytes, require_eof=True, deadline=deadline,
        )
    finally:
        conn.settimeout(previous_timeout)


def serve_one(
    bound: BoundRepoSocket,
    handler: Callable[[bytes], bytes],
    *,
    max_bytes: int = DEFAULT_MAX_JSON_BYTES,
    read_deadline_s: float,
    expected_uid: int,
) -> None:
    """Accept exactly one request on one connection, send one response, close."""
    conn, _address = bound.accept()
    with conn:
        request = receive_request(
            conn, max_bytes=max_bytes, deadline_s=read_deadline_s,
            expected_uid=expected_uid,
        )
        response = handler(request)
        if not isinstance(response, bytes):
            raise TypeError("handler response must be bytes")
        send_frame(conn, response)
        conn.shutdown(socket.SHUT_WR)


def exchange(
    runtime_dir: os.PathLike[str] | str,
    request: object,
    *,
    timeout_s: float,
    max_bytes: int = DEFAULT_MAX_JSON_BYTES,
) -> bytes:
    """Client exchange bounded by one absolute boottime deadline."""
    raw = request if isinstance(request, bytes) else canonical_bytes(request)
    if len(raw) > max_bytes:
        raise _runtime_error("oversize-frame")
    if not isinstance(timeout_s, (int, float)) or isinstance(timeout_s, bool) or timeout_s <= 0:
        raise ValueError("timeout_s must be positive")
    deadline = _boottime() + float(timeout_s)
    sock = connect_repo_socket(runtime_dir, _deadline_left(deadline))
    with sock:
        send_frame(sock, raw, deadline=deadline)
        sock.shutdown(socket.SHUT_WR)
        return recv_frame(
            sock, max_bytes=max_bytes, require_eof=True, deadline=deadline,
        )


__all__ = [
    "BoundRepoSocket", "FRAME_HEADER_BYTES", "PeerCredentials", "RUNTIME_DIR_MODE",
    "SOCKET_BASENAME", "SOCKET_MODE", "SocketPathAlias", "bind_repo_socket",
    "connect_repo_socket", "exchange", "peer_credentials", "receive_request",
    "recv_frame", "send_frame", "serve_one", "socket_path_alias",
]
