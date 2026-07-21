# -*- coding: utf-8 -*-
"""dev-waves Unix framing/socket tests with a pytest-independent runner."""
from __future__ import annotations

import importlib
import os
import socket
import stat
import struct
import sys
import tempfile
import threading
import time
import traceback
import types
import unittest
from unittest import mock
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
_PKG = "_izanagi_unit_a_dev_waves"
if _PKG not in sys.modules:
    package = types.ModuleType(_PKG)
    package.__path__ = [str(_ROOT / "tools" / "dev_waves")]
    package.__package__ = _PKG
    sys.modules[_PKG] = package
schema = importlib.import_module(f"{_PKG}.schema")
protocol = importlib.import_module(f"{_PKG}.protocol")


def _expect_error(fn):
    try:
        fn()
    except schema.DevWavesError:
        return
    raise AssertionError("不正 protocol input が拒否されなかった")


def _pair():
    left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    left.settimeout(0.2)
    right.settimeout(0.2)
    return left, right


class _MemorySocket:
    """Short-read/short-write capable socket double for framing, not AF_UNIX."""

    def __init__(self, incoming=b"", *, keep_open=False, chunk=3):
        self.incoming = bytearray(incoming)
        self.outgoing = bytearray()
        self.keep_open = keep_open
        self.chunk = chunk

    def send(self, data):
        count = min(len(data), self.chunk)
        self.outgoing.extend(bytes(data[:count]))
        return count

    def recv(self, size):
        if self.incoming:
            count = min(size, self.chunk, len(self.incoming))
            result = bytes(self.incoming[:count])
            del self.incoming[:count]
            return result
        if self.keep_open:
            raise socket.timeout()
        return b""


class _ExchangeSocket(_MemorySocket):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def settimeout(self, _value):
        return None

    def shutdown(self, _how):
        return None

    def send(self, data):
        self.outgoing.extend(bytes(data))
        return len(data)


def _framed(raw):
    sender = _MemorySocket(chunk=2)
    protocol.send_frame(sender, raw)
    return bytes(sender.outgoing)


def _require_unix_socket_io():
    """Skip only when the execution sandbox forbids AF_UNIX data operations."""
    left, right = _pair()
    try:
        try:
            left.send(b"x")
            if right.recv(1) != b"x":
                raise AssertionError("AF_UNIX capability probe lost a byte")
        except PermissionError as exc:
            raise unittest.SkipTest(
                f"sandbox forbids AF_UNIX I/O: errno={exc.errno}"
            ) from None
    finally:
        left.close()
        right.close()


def test_frame_round_trip_requires_client_half_close():
    raw = b'{"action":"status"}'
    receiver = _MemorySocket(_framed(raw), chunk=2)
    assert protocol.recv_frame(receiver, max_bytes=100) == raw


def test_frame_rejects_truncated_header_body_oversize_and_trailing_frame():
    payloads = (
        b"\x00\x00",
        struct.pack(">I", 5) + b"abc",
        struct.pack(">I", 101),
        struct.pack(">I", 2) + b"{}" + b"x",
    )
    for payload in payloads:
        receiver = _MemorySocket(payload, chunk=2)
        _expect_error(lambda receiver=receiver: protocol.recv_frame(receiver, max_bytes=100))


def test_frame_rejects_missing_half_close_at_read_deadline():
    receiver = _MemorySocket(_framed(b"{}"), keep_open=True)
    _expect_error(lambda: protocol.recv_frame(receiver, max_bytes=10))


def test_one_connection_rejects_a_second_request_frame():
    receiver = _MemorySocket(_framed(b"{}") + _framed(b"[]"))
    _expect_error(lambda: protocol.recv_frame(receiver, max_bytes=100))


def _runtime_dir(parent, name="runtime"):
    path = Path(parent) / name
    path.mkdir()
    path.chmod(0o700)
    return path


def test_bind_connect_peercred_mode_and_one_request_response():
    _require_unix_socket_io()
    with tempfile.TemporaryDirectory(prefix="izanagi_devwaves_socket_") as temp:
        runtime = _runtime_dir(temp)
        with protocol.bind_repo_socket(runtime, os.getuid()) as bound:
            visible = runtime / ".s"
            info = visible.stat()
            assert stat.S_ISSOCK(info.st_mode)
            assert stat.S_IMODE(info.st_mode) == 0o600

            result = []
            errors = []

            def server():
                try:
                    protocol.serve_one(
                        bound, lambda raw: b'{"ok":true,"echo":' + raw + b"}",
                        read_deadline_s=1.0, expected_uid=os.getuid(), max_bytes=1024,
                    )
                except Exception as exc:  # surfaced in main thread
                    errors.append(exc)

            thread = threading.Thread(target=server)
            thread.start()
            result.append(protocol.exchange(runtime, b'"hello"', timeout_s=1.0))
            thread.join(2)
            assert not thread.is_alive()
            assert not errors, errors
            assert result == [b'{"ok":true,"echo":"hello"}']
        assert not (runtime / ".s").exists()


def test_peer_credentials_report_same_uid_on_real_unix_pair():
    _require_unix_socket_io()
    left, right = _pair()
    try:
        credentials = protocol.peer_credentials(right)
        assert credentials.pid == os.getpid()
        assert credentials.uid == os.getuid()
        assert credentials.gid == os.getgid()
    finally:
        left.close()
        right.close()


def test_socket_alias_handles_visible_path_longer_than_sun_path():
    with tempfile.TemporaryDirectory(prefix="izanagi_devwaves_long_") as temp:
        path = Path(temp)
        for index in range(3):
            path /= (str(index) + "x" * 70)
            path.mkdir()
        runtime = _runtime_dir(path)
        assert len(os.fsencode(str(runtime / ".s"))) >= 108
        with protocol.socket_path_alias(runtime) as alias:
            assert alias.path.startswith("/proc/self/fd/")
            assert len(os.fsencode(alias.path)) < 108


def test_socket_alias_covers_visible_107_and_108_byte_boundaries():
    with tempfile.TemporaryDirectory(prefix="izanagi_devwaves_boundary_") as temp:
        base = Path(temp)
        for target in (107, 108):
            component_length = target - len(os.fsencode(str(base))) - 4
            assert 1 <= component_length <= 255
            runtime = _runtime_dir(base, f"r{target}_" + "x" * (component_length - 5))
            assert len(os.fsencode(str(runtime / ".s"))) == target
            with protocol.socket_path_alias(runtime) as alias:
                assert len(os.fsencode(alias.path)) < 108


def test_long_visible_socket_path_can_bind_through_alias():
    _require_unix_socket_io()
    with tempfile.TemporaryDirectory(prefix="izanagi_devwaves_long_bind_") as temp:
        path = Path(temp)
        for index in range(3):
            path /= (str(index) + "x" * 70)
            path.mkdir()
        runtime = _runtime_dir(path)
        with protocol.bind_repo_socket(runtime, os.getuid()):
            assert (runtime / ".s").exists()


def test_runtime_and_socket_modes_are_fail_closed():
    _require_unix_socket_io()
    with tempfile.TemporaryDirectory(prefix="izanagi_devwaves_mode_") as temp:
        runtime = _runtime_dir(temp)
        runtime.chmod(0o755)
        _expect_error(lambda: protocol.bind_repo_socket(runtime, os.getuid()))
        runtime.chmod(0o700)
        with protocol.bind_repo_socket(runtime, os.getuid()):
            (runtime / ".s").chmod(0o666)
            _expect_error(lambda: protocol.connect_repo_socket(runtime, 0.1))


def test_server_read_deadline_rejects_delayed_partial_frame():
    _require_unix_socket_io()
    left, right = _pair()
    try:
        left.sendall(struct.pack(">I", 10) + b"abc")
        _expect_error(lambda: protocol.receive_request(
            right, max_bytes=100, deadline_s=0.02, expected_uid=os.getuid(),
        ))
    finally:
        left.close()
        right.close()


def test_server_read_deadline_is_absolute_under_slow_byte_drip() -> None:
    _require_unix_socket_io()
    left, right = _pair()
    payload = _framed(b'{"action":"status"}')

    def drip() -> None:
        for byte in payload:
            try:
                left.send(bytes((byte,)))
            except OSError:
                return
            time.sleep(0.01)

    thread = threading.Thread(target=drip)
    thread.start()
    started = time.monotonic()
    try:
        _expect_error(lambda: protocol.receive_request(
            right, max_bytes=100, deadline_s=0.04, expected_uid=os.getuid(),
        ))
        assert time.monotonic() - started < 0.15
    finally:
        left.close(); right.close(); thread.join(1)


def test_client_exchange_response_deadline_is_absolute_under_slow_byte_drip() -> None:
    _require_unix_socket_io()
    with tempfile.TemporaryDirectory(prefix="izanagi_devwaves_client_deadline_") as temp:
        runtime = _runtime_dir(temp)
        with protocol.bind_repo_socket(runtime, os.getuid()) as bound:
            errors = []

            def server() -> None:
                try:
                    conn, _ = bound.accept()
                    with conn:
                        protocol.receive_request(
                            conn, max_bytes=100, deadline_s=1,
                            expected_uid=os.getuid(),
                        )
                        response = _framed(b'{"ok":true}')
                        for byte in response:
                            try:
                                conn.send(bytes((byte,)))
                            except OSError:
                                return
                            time.sleep(0.01)
                except Exception as exc:
                    errors.append(exc)

            thread = threading.Thread(target=server)
            thread.start()
            started = time.monotonic()
            _expect_error(lambda: protocol.exchange(runtime, b"{}", timeout_s=0.04))
            elapsed = time.monotonic() - started
            thread.join(1)
            assert elapsed < 0.15
            assert not errors, errors


def test_client_exchange_deadline_cannot_be_refreshed_by_response_bytes() -> None:
    receiver = _ExchangeSocket(_framed(b'{"ok":true}'), chunk=1)
    now = 0.0

    def advancing_boottime() -> float:
        nonlocal now
        now += 0.01
        return now

    with mock.patch.object(protocol, "connect_repo_socket", return_value=receiver), \
            mock.patch.object(protocol, "_boottime", side_effect=advancing_boottime):
        _expect_error(lambda: protocol.exchange("/unused", b"{}", timeout_s=0.04))
    assert receiver.outgoing == _framed(b"{}")


def _run():
    fns = [value for name, value in sorted(globals().items())
           if name.startswith("test_") and callable(value)]
    passed = failed = errors = skipped = 0
    for fn in fns:
        try:
            fn()
            passed += 1
        except unittest.SkipTest as exc:
            skipped += 1
            print(f"SKIP {fn.__name__}: {exc}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
        except Exception:
            errors += 1
            print(f"ERROR {fn.__name__}:")
            traceback.print_exc()
    print(
        f"\n{passed} passed, {skipped} skipped, {failed} failed, "
        f"{errors} errors (of {len(fns)})"
    )
    return 0 if failed == 0 and errors == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
